# conteo-stock/enviar_email.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from productos import CATEGORIAS, columnas_de

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

DESTINATARIO = "central.recoleta.4@gmail.com"
REMITENTE    = os.environ.get("GMAIL_FROM", "central.recoleta.4@gmail.com")
GMAIL_PASS   = os.environ.get("GMAIL_APP_PASS", "")

CSS = """
body{font-family:Arial,sans-serif;font-size:13px;color:#222}
h2{color:#1e1e2e}h3{color:#4f46e5;margin-top:24px;margin-bottom:6px}
table{border-collapse:collapse;width:100%;margin-bottom:16px}
th{background:#f0f4ff;padding:6px 10px;border:1px solid #ccc;text-align:center;font-size:11px;text-transform:uppercase}
td{padding:6px 10px;border:1px solid #ddd;text-align:center}
.nombre{text-align:left;font-weight:600}.total{background:#e8ffe8;font-weight:700}
.pos{color:#dc2626;font-weight:700}.neg{color:#2563eb;font-weight:700}.zero{color:#16a34a}
"""


def build_html_body(data: dict) -> str:
    fecha = data.get("fecha", "")
    hora  = data.get("hora", "")
    turno = data.get("turno", "")
    resp  = data.get("responsable", "")
    conteo = data.get("conteo", {})

    parts = [f"<html><head><style>{CSS}</style></head><body>",
             f"<h2>📋 Conteo de Stock — Central Recoleta 4</h2>",
             f"<p><b>Fecha:</b> {fecha} {hora} &nbsp;|&nbsp; <b>Turno:</b> {turno} &nbsp;|&nbsp; <b>Responsable:</b> {resp}</p>"]

    for cat in CATEGORIAS:
        cols = columnas_de(cat["tipo"])
        col_ths = "".join(f"<th>{c.replace('_',' ').upper()}</th>" for c in cols)
        parts.append(f"<h3>{cat['nombre']}</h3><table><tr><th style='text-align:left'>PRODUCTO</th>{col_ths}<th>TOTAL</th><th>SISTEMA</th><th>DIF.</th></tr>")
        for prod in cat["productos"]:
            d = conteo.get(prod, {})
            tds = "".join(f"<td>{d.get(c,'')}</td>" for c in cols)
            total = d.get("total", "")
            sis   = d.get("sistema", "")
            dif   = d.get("dif", "")
            if isinstance(dif, (int, float)):
                cls    = "pos" if dif > 0 else ("neg" if dif < 0 else "zero")
                dif_s  = (f"+{dif}" if dif > 0 else str(dif))
            else:
                cls, dif_s = "", str(dif)
            parts.append(f"<tr><td class='nombre'>{prod}</td>{tds}<td class='total'>{total}</td><td>{sis}</td><td class='{cls}'>{dif_s}</td></tr>")
        parts.append("</table>")

    parts.append("</body></html>")
    return "".join(parts)


def enviar(data: dict) -> None:
    html   = build_html_body(data)
    asunto = f"Conteo de Stock – Central Recoleta 4 – {data.get('fecha','')} Turno {data.get('turno','')}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = REMITENTE
    msg["To"]      = DESTINATARIO
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(REMITENTE, GMAIL_PASS)
        smtp.sendmail(REMITENTE, DESTINATARIO, msg.as_string())
    print(f"✅ Email enviado a {DESTINATARIO}")
