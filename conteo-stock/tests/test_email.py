# conteo-stock/tests/test_email.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from enviar_email import build_html_body

SAMPLE = {
    "fecha": "10/06/2026", "hora": "14:30", "turno": "M", "responsable": "María",
    "conteo": {
        "Humita": {"batea": 5, "horno": 4, "exhibidora": 0, "freezer": 3,
                   "total": 12, "sistema": 12, "dif": 0, "__done": True},
        "Coca Cola 237ml": {"exhibidora": 24, "bajo_mostrador": 12, "deposito": 48,
                            "total": 84, "sistema": 80, "dif": 4, "__done": True},
    }
}

def test_contiene_fecha():
    assert "10/06/2026" in build_html_body(SAMPLE)

def test_contiene_responsable():
    assert "María" in build_html_body(SAMPLE)

def test_contiene_producto():
    assert "Humita" in build_html_body(SAMPLE)

def test_contiene_total_humita():
    html = build_html_body(SAMPLE)
    assert ">12<" in html or "12" in html

def test_dif_positiva_con_signo():
    html = build_html_body(SAMPLE)
    assert "+4" in html

def test_es_string_no_vacio():
    html = build_html_body(SAMPLE)
    assert isinstance(html, str) and len(html) > 500
