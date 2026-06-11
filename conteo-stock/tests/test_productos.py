# conteo-stock/tests/test_productos.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from productos import CATEGORIAS, COLUMNAS_COMIDA, COLUMNAS_BEBIDA, COLUMNAS_SIMPLE, columnas_de

def test_categorias_tienen_productos():
    for cat in CATEGORIAS:
        assert len(cat["productos"]) > 0, f"{cat['nombre']} sin productos"

def test_columnas_comida():
    assert COLUMNAS_COMIDA == ["batea", "horno", "exhibidora", "freezer"]

def test_columnas_bebida():
    assert COLUMNAS_BEBIDA == ["exhibidora", "bajo_mostrador", "deposito"]

def test_columnas_simple():
    assert COLUMNAS_SIMPLE == ["cantidad"]

def test_categorias_contienen_empanadas():
    nombres = [c["nombre"] for c in CATEGORIAS]
    assert "EMPANADAS" in nombres

def test_empanadas_tienen_17_productos():
    emp = next(c for c in CATEGORIAS if c["nombre"] == "EMPANADAS")
    assert len(emp["productos"]) == 17

def test_bebidas_tienen_tipo_bebida():
    beb = next(c for c in CATEGORIAS if c["nombre"] == "BEBIDAS")
    assert beb["tipo"] == "bebida"

def test_ingredientes_tienen_tipo_simple():
    ing = next(c for c in CATEGORIAS if c["nombre"] == "INGREDIENTES")
    assert ing["tipo"] == "simple"

def test_columnas_de_comida():
    assert columnas_de("comida") == ["batea", "horno", "exhibidora", "freezer"]

def test_columnas_de_bebida():
    assert columnas_de("bebida") == ["exhibidora", "bajo_mostrador", "deposito"]

def test_columnas_de_simple():
    assert columnas_de("simple") == ["cantidad"]
