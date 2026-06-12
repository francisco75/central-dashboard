# conteo-stock/scrape_stock.py
"""
Scrape "Productos → Ver stock" en Datalive.
Devuelve {nombre_normalizado: stock_int}.
Reutiliza el patrón de login de scrape_datalive.py del proyecto.
"""
import os
import re
import asyncio
import unicodedata
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()  # busca .env subiendo el árbol de directorios automáticamente

BASE_URL = "https://vm4.zona.dlsrvz.com/central/sistema/prd/index.php"
DL_USER  = os.environ["DATALIVE_USER"]
DL_PASS  = os.environ["DATALIVE_PASS"]


def normalize(s: str) -> str:
    """Minúsculas, sin tildes, sin puntuación extra. Igual que en scrape_datalive.py."""
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


async def _login(page) -> None:
    login_url = BASE_URL.replace("index.php", "login_new.php")
    await page.goto(login_url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_selector("#usu", state="visible", timeout=15000)
    await page.fill("#usu", DL_USER)
    await page.fill('input[type="password"]', DL_PASS)
    for sel in [".btnLoginModal", 'button[type="submit"]', 'input[type="submit"]']:
        btn = await page.query_selector(sel)
        if btn and await btn.is_visible():
            await btn.click()
            break
    else:
        await page.press('input[type="password"]', "Enter")
    await page.wait_for_url(lambda u: "login_new.php" not in u, timeout=20000)
    print("✅ Login OK")


async def _fetch_stock(page) -> dict[str, int]:
    """
    Navega a Productos → Ver stock y extrae {nombre_normalizado: stock}.
    Intenta URLs directas primero; si fallan, navega por el menú.
    """
    candidates = [
        BASE_URL + "?action=5&subaction=ver_stock",
        BASE_URL + "?action=5&subaction=stock",
        BASE_URL + "?action=productos&subaction=ver_stock",
    ]
    for url in candidates:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        content = await page.content()
        if "<table" in content.lower() and len(content) > 3000:
            print(f"  ↳ Stock encontrado en: {url}")
            return _parse_stock_table(content)

    # Fallback: navegar por el menú
    await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=20000)
    for text in ["Productos", "Stock"]:
        link = await page.query_selector(f'a:has-text("{text}")')
        if link:
            await link.click()
            await page.wait_for_load_state("domcontentloaded")
            break
    for text in ["Ver stock", "Stock actual", "ver stock"]:
        link = await page.query_selector(f'a:has-text("{text}")')
        if link:
            await link.click()
            await page.wait_for_load_state("domcontentloaded")
            break
    return _parse_stock_table(await page.content())


def _parse_stock_table(html: str) -> dict[str, int]:
    """
    Parsea la tabla de stock.
    Primera columna = nombre producto, busca columna con 'stock'/'cantidad'/'existencia' en header.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        print("  ⚠️  No se encontró tabla de stock")
        return {}

    rows = table.find_all("tr")
    if len(rows) < 2:
        return {}

    headers = [c.get_text(strip=True).lower() for c in rows[0].find_all(["th", "td"])]
    stock_col = next(
        (i for i, h in enumerate(headers) if any(kw in h for kw in ["stock", "cantidad", "existencia", "actual"])),
        1  # fallback: segunda columna
    )
    print(f"  ↳ Headers: {headers[:6]} | columna stock: idx={stock_col}")

    result = {}
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if len(cells) <= stock_col:
            continue
        name_raw = cells[0].get_text(strip=True)
        if not name_raw:
            continue
        val_raw = cells[stock_col].get_text(strip=True).replace(".", "").replace(",", "").strip()
        try:
            stock = int(float(val_raw)) if val_raw and val_raw not in ("-", "") else 0
        except ValueError:
            stock = 0
        result[normalize(name_raw)] = stock

    print(f"  ↳ {len(result)} productos parseados")
    return result


async def get_stock() -> dict[str, int]:
    """Entry point público. Devuelve {nombre_normalizado: stock_int}."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await (await browser.new_context()).new_page()
        try:
            print("🔐 Login Datalive...")
            await _login(page)
            print("📦 Obteniendo stock...")
            stock = await _fetch_stock(page)
        finally:
            await browser.close()
    return stock


if __name__ == "__main__":
    stock = asyncio.run(get_stock())
    for name, qty in list(stock.items())[:10]:
        print(f"  {name}: {qty}")
    print(f"  ... ({len(stock)} productos total)")
