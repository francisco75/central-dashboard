#!/usr/bin/env python3
"""
scrape_datalive.py — Actualización diaria del dashboard Central Recoleta 4
Ejecutado por GitHub Actions cada noche (Lun–Sáb) a las 23:00 ART.

Actualiza en el HTML:
  • EMP_DIARIAS, MED_DIARIAS, PIZZA_DIARIAS_G, PIZZA_DIARIAS_M (totales diarios)
  • Columna del mes actual en EMPANADAS[] y PIZZAS[] (totales mensuales por producto)
"""

import os
import re
import asyncio
import unicodedata
from datetime import date
from collections import defaultdict
from playwright.async_api import async_playwright

# ── Config ────────────────────────────────────────────────────────
BASE_URL   = "https://vm4.zona.dlsrvz.com/central/sistema/prd/index.php"
DASHBOARD  = "dashboard_central_recoleta4.html"
DL_USER    = os.environ["DATALIVE_USER"]
DL_PASS    = os.environ["DATALIVE_PASS"]

# Índice 0 = Sep 2025
MONTH_ZERO = date(2025, 9, 1)

def month_idx(d: date) -> int:
    return (d.year - MONTH_ZERO.year) * 12 + (d.month - MONTH_ZERO.month)

# ── Normalización de nombres ───────────────────────────────────────
def normalize(s: str) -> str:
    """Minúsculas, sin tildes, sin puntuación extra."""
    s = s.lower().strip()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

# ── Mapeo nombres Datalive → nombres del dashboard ────────────────
EMPANADA_MAP = {
    'jamon y queso':            'Jamón y Queso',
    'carne c cuchillo':         'Carne Cuchillo',
    'carne cuchillo':           'Carne Cuchillo',
    'carne al cuchillo':        'Carne Cuchillo',
    'carne suave':              'Carne Suave',
    'cheeseburger':             'Cheeseburger',
    'pollo':                    'Pollo',
    'bondiola':                 'Bondiola',
    'carne picante':            'Carne Picante',
    'capresse':                 'Capresse',
    'caprese':                  'Capresse',
    'roquefort c jamon':        'Roquefort con Jamón',
    'roquefort con jamon':      'Roquefort con Jamón',
    'roquefort y jamon':        'Roquefort con Jamón',
    'cebolla y queso':          'Cebolla y Queso',
    'verdura':                  'Verdura',
    'humita':                   'Humita',
    'puerro y hongos':          'Puerro y Hongos',
    'puerro hongos':            'Puerro y Hongos',
    'choclo y calabaza':        'Choclo y Calabaza',
    'choclo calabaza':          'Choclo y Calabaza',
    'pollo al curry vegana':    'Pollo al Curry Vegana',
    'pollo curry vegana':       'Pollo al Curry Vegana',
    'veg pollo al curry':       'Pollo al Curry Vegana',
    'carne a la criolla veg':   'Carne a la Criolla Veg.',
    'carne criolla vegana':     'Carne a la Criolla Veg.',
    'veg carne criolla':        'Carne a la Criolla Veg.',
}

PIZZA_MAP = {
    'muzzarella':                    'Muzzarella',
    'mega muzzarella':               'Mega Muzzarella',
    'muzzarella c jamon':            'Muzzarella c/ Jamón',
    'muzzarella con jamon':          'Muzzarella c/ Jamón',
    'napolitana':                    'Napolitana',
    'napolitana c jamon':            'Napolitana c/ Jamón',
    'napolitana con jamon':          'Napolitana c/ Jamón',
    'especial':                      'Especial',
    'mega muzz c jamon':             'Mega Muzz. c/ Jamón',
    'mega muzzarella c jamon':       'Mega Muzz. c/ Jamón',
    'cuatro quesos':                 'Cuatro Quesos',
    '4 quesos':                      'Cuatro Quesos',
    'calabresa':                     'Calabresa',
    'mega calabresa':                'Mega Calabresa',
    'mega napolitana':               'Mega Napolitana',
    'muzzarella c morrones':         'Muzzarella c/ Morrones',
    'muzzarella con morrones':       'Muzzarella c/ Morrones',
    'fugazza c jamon y muzz':        'Fugazza c/ Jamón y Muzz.',
    'fugazza c muzzarella':          'Fugazza c/ Muzzarella',
    'mega especial':                 'Mega Especial',
    'roquefort':                     'Roquefort',
    'provolone':                     'Provolone',
    'fugazza mega c muzz':           'Fugazza Mega c/ Muzz.',
}

MEDIALUNA_KEYWORDS = ['medialuna']

# ── Precios de carta (sincronizado con PRODUCTOS en el HTML) ──────────
PRECIO_DASHBOARD = {
    'Medialunas':               400,
    'Jamón y Queso':           1000,
    'Carne Cuchillo':          1000,
    'Carne Suave':             1000,
    'Cheeseburger':            1000,
    'Pollo':                   1000,
    'Bondiola':                1000,
    'Carne Picante':           1000,
    'Capresse':                1000,
    'Roquefort con Jamón':     1000,
    'Cebolla y Queso':         1000,
    'Verdura':                 1000,
    'Humita':                  1000,
    'Puerro y Hongos':         1000,
    'Choclo y Calabaza':       1000,
    'Pollo al Curry Vegana':   1000,
    'Carne a la Criolla Veg.': 1000,
    'Coca Cola 500/600ml':     2300,
    'Pizza Muzzarella':        8200,
    'Pizza Mega Muzzarella':  11500,
}

BEBIDA_MAP = {
    'coca cola':      'Coca Cola 500/600ml',
    'coca cola 500':  'Coca Cola 500/600ml',
    'coca cola 600':  'Coca Cola 500/600ml',
    'coca 500':       'Coca Cola 500/600ml',
    'coca 600':       'Coca Cola 500/600ml',
}

DOW_ES = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}

MONTH_NAMES_ES = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
    5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
    9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE',
}

def dl_to_dashboard(dl_name: str, mapping: dict) -> str | None:
    """Intenta mapear nombre Datalive al nombre del dashboard."""
    key = normalize(dl_name)
    if key in mapping:
        return mapping[key]
    # Partial match: buscar la clave más larga que sea substring del nombre
    matches = [(len(k), v) for k, v in mapping.items() if k in key or key in k]
    if matches:
        return sorted(matches, reverse=True)[0][1]
    return None

# ── Playwright: Login ──────────────────────────────────────────────
async def screenshot(page, name):
    """Guarda screenshot para debug (solo en GitHub Actions)."""
    try:
        path = f"/tmp/debug_{name}.png"
        await page.screenshot(path=path, full_page=False)
        print(f"  📸 Screenshot: {path}")
    except Exception as e:
        print(f"  📸 Screenshot falló: {e}")


async def login(page):
    print("🔐 Cargando página de login Datalive...")
    # Usar login_new.php — index.php?action=0 muestra "sesión caducada" y falla
    login_url = BASE_URL.replace("index.php", "login_new.php")
    await page.goto(login_url, wait_until="domcontentloaded", timeout=45000)

    # Esperar que el campo usuario esté visible
    print("  ↳ Esperando campo #usu...")
    try:
        await page.wait_for_selector('#usu', state='visible', timeout=15000)
        print("  ↳ Campo #usu encontrado")
    except Exception as e:
        print(f"  ↳ #usu no encontrado: {e}")
        await page.wait_for_selector('input[type="text"]', state='visible', timeout=10000)

    await screenshot(page, '01_login_page')

    # Llenar campos
    await page.fill('#usu', DL_USER)
    await page.wait_for_timeout(500)
    await page.fill('input[type="password"]', DL_PASS)
    await page.wait_for_timeout(500)
    print("  ↳ Credenciales ingresadas")

    # Intentar submit — primero botones con texto específico, luego form submit
    submitted = False
    text_selectors = [
        '.btnLoginModal', 'button[type="submit"]', 'input[type="submit"]',
        'button:has-text("Confirmar")', 'button:has-text("Ingresar")',
        'button:has-text("Iniciar")', 'button:has-text("Entrar")',
        'button:has-text("Acceder")', 'button:has-text("Login")',
    ]
    for sel in text_selectors:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                submitted = True
                print(f"  ↳ Botón clickeado: {sel}")
                break
        except Exception:
            pass

    if not submitted:
        print("  ↳ Botón específico no encontrado, intentando form.submit()...")
        submitted_via_js = await page.evaluate("""() => {
            const pwd = document.querySelector('input[type="password"]');
            if (pwd && pwd.form) { pwd.form.submit(); return true; }
            const form = document.querySelector('form');
            if (form) { form.submit(); return true; }
            return false;
        }""")
        if not submitted_via_js:
            print("  ↳ form.submit() falló, usando Enter...")
            await page.press('input[type="password"]', 'Enter')

    # Esperar navegación fuera del login
    try:
        await page.wait_for_url(
            lambda url: 'login_new.php' not in url,
            timeout=20000
        )
    except Exception:
        await page.wait_for_timeout(3000)

    await screenshot(page, '02_after_login')

    # Verificar por URL — si sigue en login_new.php el login falló
    current_url = page.url
    page_title  = await page.title()
    print(f"  ↳ Post-login URL: {current_url}")
    print(f"  ↳ Post-login title: {page_title}")

    if 'login_new.php' in current_url or 'caducado' in page_title.lower() or 'daducado' in page_title.lower():
        raise RuntimeError(f"❌ Login falló — URL: '{current_url}' | título: '{page_title}'. Verificar DATALIVE_USER y DATALIVE_PASS en GitHub Secrets.")

    print("✅ Login completado")

# ── Playwright: Fetch ventas detalladas ───────────────────────────
async def fetch_detallado(page, fecha_desde: str, fecha_hasta: str, turno_val: str = '') -> str | None:
    """
    Navega al reporte de ventas detalladas y captura la respuesta AJAX.
    Fechas en formato DD/MM/YYYY.
    Si turno_val es '', trae todos los turnos (default).
    Si turno_val es '1' o '2', filtra por turno Mañana o Tarde.
    """
    label = f"turno={turno_val!r}" if turno_val else "todos los turnos"
    print(f"📊 Fetching ventas detalladas {fecha_desde} → {fecha_hasta} [{label}]")

    ajax_html = None
    ajax_url_seen = []

    async def on_response(response):
        nonlocal ajax_html
        # Log any rp_ventas URL for diagnostics
        if "rp_ventas" in response.url:
            ajax_url_seen.append(response.url)
            print(f"  ↳ rp_ventas URL detectada: {response.url}")
        if "rp_ventas_detalladas_sucursalxdia_datos_nuevo" in response.url:
            try:
                ajax_html = await response.text()
                print(f"  ↳ AJAX capturado: {len(ajax_html):,} chars")
            except Exception as e:
                print(f"  ↳ Error leyendo AJAX: {e}")

    page.on("response", on_response)

    # Siempre navegar fresh — garantiza estado limpio para cada llamada
    await page.goto(
        f"{BASE_URL}?action=6&subaction=rp_ventas_detalladas_sucursalxdia_nuevo",
        wait_until="domcontentloaded", timeout=30000
    )

    if not turno_val:
        await screenshot(page, '03_report_page')

    # Setear fechas y disparar change events para que el JS date-picker actualice su modelo
    for attempt in range(3):
        try:
            await page.wait_for_selector('#FechaDesde', state='visible', timeout=10000)
            await page.fill('#FechaDesde', fecha_desde)
            await page.fill('#FechaHasta', fecha_hasta)
            # Forzar eventos change/input para que el picker reconozca el nuevo valor
            await page.evaluate("""() => {
                ['#FechaDesde', '#FechaHasta'].forEach(id => {
                    const el = document.querySelector(id);
                    if (!el) return;
                    el.dispatchEvent(new Event('input',  {bubbles: true}));
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                });
            }""")
            # Verificar que el valor quedó bien
            val_desde = await page.evaluate("() => document.querySelector('#FechaDesde')?.value || 'N/A'")
            val_hasta  = await page.evaluate("() => document.querySelector('#FechaHasta')?.value  || 'N/A'")
            print(f"  ↳ Fechas seteadas: {fecha_desde}→{fecha_hasta} | DOM: {val_desde}→{val_hasta}")
            break
        except Exception as e:
            print(f"  ↳ Reintento fecha ({attempt+1}): {e}")
            await page.wait_for_timeout(2000)

    # Descubrir y loguear opciones de turno (siempre, para diagnóstico)
    opts = await page.evaluate("""() => {
        const sels = ['#Turno','#turno','#IdTurno','#TurnoId',
                      'select[name="Turno"]','select[name="turno"]'];
        for (const s of sels) {
            const el = document.querySelector(s);
            if (el) return {sel: s, opts: Array.from(el.options).map(o=>o.value+':'+o.text.trim())};
        }
        return null;
    }""")
    print(f"  ↳ Turno selector: {opts}")

    # Setear turno si se especifica
    if turno_val and opts:
        turno_set = await page.evaluate(f"""() => {{
            const sels = ['#Turno', '#turno', '#IdTurno', '#TurnoId',
                          'select[name="Turno"]', 'select[name="turno"]'];
            for (const s of sels) {{
                const el = document.querySelector(s);
                if (el) {{
                    el.value = '{turno_val}';
                    el.dispatchEvent(new Event('change', {{bubbles:true}}));
                    return s + ':' + el.value;
                }}
            }}
            return null;
        }}""")
        print(f"  ↳ Turno seteado: {turno_set}")

    # Disparar el reporte
    try:
        await page.evaluate("actualizar_reporte()")
        print("  ↳ actualizar_reporte() ejecutado")
    except Exception as e1:
        print(f"  ↳ actualizar_reporte() falló: {e1}")
        try:
            await page.click('button:has-text("Ver reporte")', timeout=5000)
            print("  ↳ Botón 'Ver reporte' clickeado")
        except Exception as e2:
            print(f"  ↳ Botón falló también: {e2}")

    # Esperar hasta 20s por respuesta AJAX
    for _ in range(40):
        if ajax_html:
            break
        await page.wait_for_timeout(500)

    page.remove_listener("response", on_response)

    if not ajax_html:
        print(f"  ❌ No se recibió respuesta AJAX. URLs vistas: {ajax_url_seen}")
    return ajax_html

# ── Parseo de la tabla AJAX ────────────────────────────────────────
def parse_detallado(html: str) -> dict:
    """
    Parsea la tabla HTML del reporte detallado.
    Devuelve: {producto_norm: {fecha_iso: unidades}}
    La primera columna es el nombre del producto.
    Las columnas siguientes son fechas (DD/MM o DD/MM/YY).
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not table:
        print("  ⚠️  No se encontró tabla en el AJAX")
        return {}

    rows = table.find_all("tr")
    if len(rows) < 2:
        return {}

    # Cabecera: identificar columnas de fecha
    header_cells = rows[0].find_all(['th', 'td'])
    # Log de cabecera para diagnóstico
    header_texts = [c.get_text(strip=True) for c in header_cells[:15]]
    print(f"  ↳ Cabecera (primeras 15 celdas): {header_texts}")

    date_cols = []   # [(col_index, 'YYYY-MM-DD'), ...]
    today = date.today()
    for i, cell in enumerate(header_cells[1:], start=1):
        text = cell.get_text(strip=True)
        # Formato DD/MM o DD/MM/YY o DD/MM/YYYY
        m = re.match(r'(\d{1,2})/(\d{2})(?:/(\d{2,4}))?', text)
        if m:
            day = int(m.group(1))
            mon = int(m.group(2))
            yr_str = m.group(3)
            if yr_str:
                yr = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
            else:
                yr = today.year
                if mon > today.month:
                    yr -= 1
            date_cols.append((i, f"{yr}-{mon:02d}-{day:02d}"))

    if date_cols:
        print(f"  ↳ Columnas fecha: {[d for _,d in date_cols[:5]]} ... ({len(date_cols)} total)")
    else:
        print(f"  ↳ ⚠️  No se detectaron columnas de fecha — posible cambio de formato")

    result = {}
    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        if not cells:
            continue
        name_raw = cells[0].get_text(strip=True)
        name_norm = normalize(name_raw)
        if not name_norm or name_norm in ('total', 'subtotal', 'totales'):
            continue

        day_data = {}
        for col_i, fecha in date_cols:
            if col_i < len(cells):
                v = cells[col_i].get_text(strip=True).replace('.', '').replace(',', '').strip()
                try:
                    day_data[fecha] = int(v) if v and v not in ('-', '') else 0
                except ValueError:
                    day_data[fecha] = 0
        result[name_norm] = day_data

    print(f"  ↳ {len(result)} productos parseados, {len(date_cols)} días")
    return result

# ── Agregaciones ───────────────────────────────────────────────────
def daily_totals_by_keywords(parsed: dict, keywords: list[str]) -> dict:
    """Suma diaria de todos los productos cuyo nombre contiene algún keyword (normalizado)."""
    daily = defaultdict(int)
    for prod_norm, dias in parsed.items():
        if any(kw in prod_norm for kw in keywords):
            for fecha, units in dias.items():
                daily[fecha] += units
    return dict(sorted(daily.items()))

def monthly_totals_mapped(parsed: dict, mapping: dict) -> dict:
    """
    Suma mensual por producto usando el mapping Datalive→Dashboard.
    Devuelve {dashboard_name: total_units_del_mes}
    """
    totals = defaultdict(int)
    for prod_norm, dias in parsed.items():
        dash_name = dl_to_dashboard(prod_norm, mapping)
        if dash_name:
            totals[dash_name] += sum(dias.values())
        else:
            print(f"  ⚠️  Sin mapeo: '{prod_norm}'")
    return dict(totals)

# ── Actualización del HTML ─────────────────────────────────────────
def update_js_dict(html: str, var_name: str, new_entries: dict[str, int]) -> str:
    """
    Actualiza un dict JS: const VAR_NAME = {'YYYY-MM-DD': N, ...};
    Hace merge: preserva entradas existentes, sobreescribe las de new_entries.
    """
    pattern = rf"(const {re.escape(var_name)}\s*=\s*\{{)([\s\S]*?)(\}};)"
    match = re.search(pattern, html)
    if not match:
        print(f"  ⚠️  Variable JS '{var_name}' no encontrada")
        return html

    # Parsear existentes
    existing = {}
    for m in re.finditer(r"'(\d{4}-\d{2}-\d{2})'\s*:\s*(\d+)", match.group(2)):
        existing[m.group(1)] = int(m.group(2))

    before = len(existing)
    existing.update(new_entries)
    after  = len(existing)

    # Reconstruir ordenado
    items = sorted(existing.items())
    new_body = ', '.join(f"'{k}':{v}" for k, v in items)
    result = html[:match.start()] + match.group(1) + new_body + match.group(3) + html[match.end():]
    print(f"  ✓ {var_name}: {before} → {after} entradas (+{len(new_entries)} nuevas)")
    return result


def update_monthly_col(html: str, array_name: str, product_name: str, col_idx: int, new_value: int) -> str:
    """
    Actualiza una celda mensual en arrays como EMPANADAS/PIZZAS:
      ['Producto', total_acum, [m0, m1, ..., m_n]]
    Actualiza total_acum recalculándolo.
    """
    # Buscar la fila del producto — usa comillas simples en el HTML
    # Escape de caracteres especiales en el nombre
    name_pattern = re.escape(product_name)
    row_pattern = rf"(\['{name_pattern}',\s*)(\d+)(,\s*\[)([^\]]+)(\])"
    match = re.search(row_pattern, html)
    if not match:
        print(f"  ⚠️  '{product_name}' no encontrado en {array_name}")
        return html

    vals_str = match.group(4)
    vals = [v.strip() for v in vals_str.split(',')]
    if col_idx >= len(vals):
        print(f"  ⚠️  col_idx {col_idx} fuera de rango para '{product_name}'")
        return html

    old_val = int(vals[col_idx])
    vals[col_idx] = str(new_value)
    new_total = sum(int(v) for v in vals)

    new_row = match.group(1) + str(new_total) + match.group(3) + ', '.join(vals) + match.group(5)
    html = html[:match.start()] + new_row + html[match.end():]
    print(f"  ✓ {product_name}[{col_idx}]: {old_val}→{new_value} (total: {new_total})")
    return html

# ── Revenue diario estimado (unidades × precio) ────────────────────
def compute_daily_revenue(parsed: dict, month_pfx: str) -> dict:
    """
    Estima revenue diario multiplicando unidades × precio de carta.
    Devuelve {'YYYY-MM-DD': revenue_int} solo para días del mes actual.
    """
    ALL_MAP = {**EMPANADA_MAP, **PIZZA_MAP, **BEBIDA_MAP}
    for kw in MEDIALUNA_KEYWORDS:
        ALL_MAP[kw] = 'Medialunas'

    daily_rev = defaultdict(int)
    for prod_norm, dias in parsed.items():
        dash_name = dl_to_dashboard(prod_norm, ALL_MAP)
        if not dash_name:
            continue
        precio = PRECIO_DASHBOARD.get(dash_name, 0)
        if precio == 0:
            continue
        for fecha_iso, units in dias.items():
            if fecha_iso.startswith(month_pfx):
                daily_rev[fecha_iso] += units * precio
    return dict(sorted(daily_rev.items()))


def update_ventas_mes(html: str, month_num: int, daily_rev: dict) -> str:
    """
    Actualiza const VENTAS_MES = [...] con entradas de revenue diario.
    Preserva comandas existentes; no sobreescribe entradas con revenue=0.
    """
    month_name = MONTH_NAMES_ES[month_num]
    var_name   = f'VENTAS_{month_name}'
    pattern    = rf'(const {re.escape(var_name)}\s*=\s*\[)([\s\S]*?)(\];)'
    match      = re.search(pattern, html)
    if not match:
        print(f"  ⚠️  {var_name} no encontrado en el HTML")
        return html

    # Parsear entradas existentes
    existing = {}
    entry_re = re.compile(
        r"\{\s*fecha:\s*'([^']+)',\s*revenue:\s*(\d+)(?:,\s*comandas:\s*(\d+))?\s*\}"
    )
    today = date.today()
    for m in entry_re.finditer(match.group(2)):
        fecha_str = m.group(1)           # '01/06 Lun'
        rev       = int(m.group(2))
        cmd       = int(m.group(3)) if m.group(3) else None
        # Reconstruir clave ISO
        day_s, _ = fecha_str.replace('*', '').split(' ', 1)
        d_n, mo_n = day_s.split('/')
        yr = today.year if int(mo_n) <= today.month else today.year - 1
        key = f'{yr}-{mo_n}-{d_n}'
        existing[key] = {'fecha': fecha_str, 'revenue': rev, 'comandas': cmd}

    before = len(existing)

    # Merge nuevas entradas
    for date_iso, revenue in daily_rev.items():
        if revenue == 0:
            continue
        d   = date.fromisoformat(date_iso)
        fec = f"{d.day:02d}/{d.month:02d} {DOW_ES[d.weekday()]}"
        if date_iso in existing:
            existing[date_iso]['revenue'] = revenue   # actualizar revenue, preservar comandas
        else:
            existing[date_iso] = {'fecha': fec, 'revenue': revenue, 'comandas': None}

    after = len(existing)

    # Reconstruir array ordenado
    lines = []
    for _, e in sorted(existing.items()):
        fec = e['fecha']
        rev = e['revenue']
        cmd = e['comandas']
        if cmd is not None:
            lines.append(f"  {{ fecha: '{fec}',  revenue: {rev:>9}, comandas: {cmd} }},")
        else:
            lines.append(f"  {{ fecha: '{fec}',  revenue: {rev:>9} }},")

    new_body = '\n' + '\n'.join(lines) + '\n'
    result = html[:match.start()] + match.group(1) + new_body + match.group(3) + html[match.end():]
    print(f"  ✓ {var_name}: {before} → {after} entradas (+{after-before} nuevas)")
    return result


def update_dow_promedios(html: str, month_num: int, daily_rev: dict) -> str:
    """
    Recalcula DOW_PROMEDIOS_MES con los datos disponibles del mes.
    Excluye días con revenue muy bajo (feriados < 600K).
    """
    month_name = MONTH_NAMES_ES[month_num]
    var_name   = f'DOW_PROMEDIOS_{month_name}'
    pattern    = rf'(const {re.escape(var_name)}\s*=\s*\[)([\s\S]*?)(\];)'
    match      = re.search(pattern, html)
    if not match:
        print(f"  ⚠️  {var_name} no encontrado en el HTML")
        return html

    dow_vals = defaultdict(list)
    for date_iso, rev in daily_rev.items():
        if rev < 600000:   # probable feriado
            continue
        d = date.fromisoformat(date_iso)
        if d.weekday() <= 5:   # Lun–Sáb
            dow_vals[d.weekday()].append(rev)

    DOW_LABELS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    lines = []
    for i, label in enumerate(DOW_LABELS):
        vals = dow_vals[i]
        avg  = round(sum(vals) / len(vals)) if vals else 0
        lines.append(f"  {{ dia: '{label}',{'':5} avg: {avg} }},")

    new_body = '\n' + '\n'.join(lines) + '\n'
    result = html[:match.start()] + match.group(1) + new_body + match.group(3) + html[match.end():]
    print(f"  ✓ {var_name}: actualizado con {sum(len(v) for v in dow_vals.values())} días")
    return result


def update_scraper_debug(html: str, info: dict) -> str:
    """
    Escribe const SCRAPER_DEBUG = {...}; al HTML para diagnóstico.
    Si la variable no existe, la inserta antes del primer <script> o donde sea viable.
    """
    import json
    val = json.dumps(info, ensure_ascii=False, indent=None, separators=(',', ':'))
    new_block = f"const SCRAPER_DEBUG = {val};"
    pattern = r'const SCRAPER_DEBUG\s*=\s*\{[\s\S]*?\};'
    if re.search(pattern, html):
        html = re.sub(pattern, new_block, html)
    else:
        # Insertar antes del primer closing de la primera sección de constantes JS
        # Buscar la línea con EMP_DIARIAS_M para insertar cerca
        insert_after = 'const EMP_DIARIAS_T = {};'
        if insert_after in html:
            html = html.replace(insert_after, insert_after + f'\n{new_block}', 1)
        else:
            # Último recurso: insertar al final del primer bloque <script>
            html = html.replace('</script>', f'{new_block}\n</script>', 1)
    print(f"  ✓ SCRAPER_DEBUG escrito: {info}")
    return html


# ── Main ───────────────────────────────────────────────────────────
async def main() -> int:
    today       = date.today()
    month_start = today.replace(day=1)
    fecha_desde = month_start.strftime('%d/%m/%Y')
    fecha_hasta = today.strftime('%d/%m/%Y')
    cur_idx     = month_idx(today)
    month_pfx   = today.strftime('%Y-%m')

    print(f"\n{'='*55}")
    print(f"Dashboard updater · {today} · mes-idx={cur_idx}")
    print(f"Período: {fecha_desde} → {fecha_hasta}")
    print(f"{'='*55}\n")

    # ── Scraping ──────────────────────────────────────────
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page    = await (await browser.new_context()).new_page()

        await login(page)
        ajax_html = await fetch_detallado(page, fecha_desde, fecha_hasta)
        ajax_M    = await fetch_detallado(page, fecha_desde, fecha_hasta, turno_val='1')
        ajax_T    = await fetch_detallado(page, fecha_desde, fecha_hasta, turno_val='2')
        await browser.close()

    if not ajax_html:
        print("❌ ABORT: no hay datos de Datalive")
        return 1

    # ── Parseo ────────────────────────────────────────────
    parsed   = parse_detallado(ajax_html)
    parsed_M = parse_detallado(ajax_M) if ajax_M else {}
    parsed_T = parse_detallado(ajax_T) if ajax_T else {}

    # Muestra de productos parseados para diagnóstico
    sample_prods = list(parsed.keys())[:8]
    # Muestra de fechas encontradas en el primer producto
    sample_dates = []
    for prod_norm, dias in parsed.items():
        if dias:
            sample_dates = sorted(dias.keys())[:5]
            break

    print(f"\n--- Diagnóstico parseo ---")
    print(f"  Productos: {len(parsed)} | M: {len(parsed_M)} | T: {len(parsed_T)}")
    print(f"  Sample prods: {sample_prods}")
    print(f"  Sample fechas: {sample_dates}")

    if not parsed:
        print("❌ ABORT: tabla vacía")
        return 1

    # ── Diarios por categoría (solo mes actual) ───────────
    # Nota: 'medialuna' se detecta por keyword
    med_daily  = {k: v for k, v in daily_totals_by_keywords(parsed, MEDIALUNA_KEYWORDS).items()
                  if k.startswith(month_pfx)}

    # Para empanadas: todo excepto pizzas, medialunas, bebidas, faina, panchos
    PIZZA_EXCL   = ['pizza', 'mega', 'fugazza', 'calabresa', 'napolitana', 'especial',
                    'muzzarella', 'roquefort pizza', 'provolone']
    NON_EMP      = MEDIALUNA_KEYWORDS + PIZZA_EXCL + ['bebida', 'coca', 'fanta', 'sprite',
                                                       'agua', 'cerveza', 'faina', 'pancho']
    emp_daily = {}
    for prod_norm, dias in parsed.items():
        if any(excl in prod_norm for excl in NON_EMP):
            continue
        # Verificar si es empanada (tiene mapeo o contiene keyword de empanada)
        if dl_to_dashboard(prod_norm, EMPANADA_MAP) or 'empanada' in prod_norm:
            for fecha, units in dias.items():
                if fecha.startswith(month_pfx):
                    emp_daily[fecha] = emp_daily.get(fecha, 0) + units

    pizza_g_daily = defaultdict(int)
    pizza_m_daily = defaultdict(int)
    for prod_norm, dias in parsed.items():
        dash = dl_to_dashboard(prod_norm, PIZZA_MAP)
        if not dash:
            continue
        is_mega = 'mega' in prod_norm
        target = pizza_m_daily if is_mega else pizza_g_daily
        for fecha, units in dias.items():
            if fecha.startswith(month_pfx):
                target[fecha] += units

    # Suma diaria medialunas
    med_daily_agg = defaultdict(int)
    for prod_norm, dias in parsed.items():
        if any(kw in prod_norm for kw in MEDIALUNA_KEYWORDS):
            for fecha, units in dias.items():
                if fecha.startswith(month_pfx):
                    med_daily_agg[fecha] += units
    med_daily = dict(med_daily_agg)

    # ── Per-shift dailies ─────────────────────────────────
    emp_daily_M = {}
    for prod_norm, dias in parsed_M.items():
        if any(excl in prod_norm for excl in NON_EMP):
            continue
        if dl_to_dashboard(prod_norm, EMPANADA_MAP) or 'empanada' in prod_norm:
            for fecha, units in dias.items():
                if fecha.startswith(month_pfx):
                    emp_daily_M[fecha] = emp_daily_M.get(fecha, 0) + units

    emp_daily_T = {}
    for prod_norm, dias in parsed_T.items():
        if any(excl in prod_norm for excl in NON_EMP):
            continue
        if dl_to_dashboard(prod_norm, EMPANADA_MAP) or 'empanada' in prod_norm:
            for fecha, units in dias.items():
                if fecha.startswith(month_pfx):
                    emp_daily_T[fecha] = emp_daily_T.get(fecha, 0) + units

    med_daily_M = defaultdict(int)
    for prod_norm, dias in parsed_M.items():
        if any(kw in prod_norm for kw in MEDIALUNA_KEYWORDS):
            for fecha, units in dias.items():
                if fecha.startswith(month_pfx):
                    med_daily_M[fecha] += units
    med_daily_M = dict(med_daily_M)

    med_daily_T = defaultdict(int)
    for prod_norm, dias in parsed_T.items():
        if any(kw in prod_norm for kw in MEDIALUNA_KEYWORDS):
            for fecha, units in dias.items():
                if fecha.startswith(month_pfx):
                    med_daily_T[fecha] += units
    med_daily_T = dict(med_daily_T)

    # ── Totales mensuales por producto ────────────────────
    emp_monthly   = monthly_totals_mapped(parsed, EMPANADA_MAP)
    pizza_monthly = monthly_totals_mapped(parsed, PIZZA_MAP)

    print(f"\nEmpanadas mes: {emp_monthly}")
    print(f"Pizzas mes:    {pizza_monthly}")

    # ── Leer HTML ─────────────────────────────────────────
    with open(DASHBOARD, encoding='utf-8') as f:
        html = f.read()
    original_len = len(html)

    # ── Actualizar DIARIAS ────────────────────────────────
    print("\n--- Actualizando DIARIAS ---")
    html = update_js_dict(html, 'EMP_DIARIAS',     emp_daily)
    html = update_js_dict(html, 'MED_DIARIAS',     med_daily)
    html = update_js_dict(html, 'PIZZA_DIARIAS_G', dict(pizza_g_daily))
    html = update_js_dict(html, 'PIZZA_DIARIAS_M', dict(pizza_m_daily))
    html = update_js_dict(html, 'EMP_DIARIAS_M',   emp_daily_M)
    html = update_js_dict(html, 'EMP_DIARIAS_T',   emp_daily_T)
    html = update_js_dict(html, 'MED_DIARIAS_M',   med_daily_M)
    html = update_js_dict(html, 'MED_DIARIAS_T',   med_daily_T)

    # ── Actualizar totales mensuales EMPANADAS ────────────
    print("\n--- Actualizando EMPANADAS mensuales ---")
    for prod, total in emp_monthly.items():
        if total > 0:
            html = update_monthly_col(html, 'EMPANADAS', prod, cur_idx, total)

    # ── Actualizar totales mensuales PIZZAS ───────────────
    print("\n--- Actualizando PIZZAS mensuales ---")
    for prod, total in pizza_monthly.items():
        if total > 0:
            html = update_monthly_col(html, 'PIZZAS', prod, cur_idx, total)

    # ── Revenue diario estimado y VENTAS_MES ─────────────
    print("\n--- Actualizando VENTAS mensuales (revenue estimado) ---")
    daily_rev = compute_daily_revenue(parsed, month_pfx)
    print(f"  Revenue diario calculado: {len(daily_rev)} días")
    if daily_rev:
        html = update_ventas_mes(html, today.month, daily_rev)
        html = update_dow_promedios(html, today.month, daily_rev)

    # ── Debug info visible en el HTML ────────────────────
    debug_info = {
        'date': str(today),
        'period': f'{fecha_desde}→{fecha_hasta}',
        'ajaxOk': bool(ajax_html),
        'ajaxMOk': bool(ajax_M),
        'ajaxTOk': bool(ajax_T),
        'productsAll': len(parsed),
        'productsM': len(parsed_M),
        'productsT': len(parsed_T),
        'empDailyDays': len(emp_daily),
        'medDailyDays': len(med_daily),
        'revDays': len(daily_rev),
        'empDailyM': len(emp_daily_M),
        'empDailyT': len(emp_daily_T),
        'sampleProds': sample_prods,
        'sampleDates': sample_dates,
        'sampleEmpDates': sorted(emp_daily.keys())[:5],
    }
    html = update_scraper_debug(html, debug_info)

    # ── Guardar ───────────────────────────────────────────
    with open(DASHBOARD, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ Dashboard guardado ({original_len:,} → {len(html):,} chars)")
    print(f"   Empanadas diarias: {len(emp_daily)} días")
    print(f"   Medialunas diarias: {len(med_daily)} días")
    print(f"   Pizzas G diarias: {len(pizza_g_daily)} días")
    print(f"   Pizzas M diarias: {len(pizza_m_daily)} días")
    print(f"   Revenue diario: {len(daily_rev)} días")
    print(f"   Empanadas M: {len(emp_daily_M)} días, T: {len(emp_daily_T)} días")
    print(f"   Medialunas M: {len(med_daily_M)} días, T: {len(med_daily_T)} días")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(asyncio.run(main()))
