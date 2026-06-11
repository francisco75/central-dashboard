# conteo-stock/tests/test_math_parser.py
import re, math

def safe_eval(expr: str):
    if not expr: return None
    if not re.match(r'^[\d\s\+\-\*\/\.]+$', expr): return None
    try:
        result = eval(expr, {"__builtins__": {}})
        if isinstance(result, (int, float)) and math.isfinite(result):
            return round(result * 100) / 100
    except Exception:
        pass
    return None

def test_suma():           assert safe_eval("3+2") == 5
def test_resta():          assert safe_eval("10-3") == 7
def test_numero_simple():  assert safe_eval("7") == 7
def test_con_espacios():   assert safe_eval("3 + 2") == 5
def test_invalida():       assert safe_eval("abc") is None
def test_vacia():          assert safe_eval("") is None
def test_decimal():        assert safe_eval("1.5+1.5") == 3.0
def test_no_injection():   assert safe_eval("__import__('os')") is None
