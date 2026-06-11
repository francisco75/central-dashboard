# conteo-stock/productos.py

COLUMNAS_COMIDA = ["batea", "horno", "exhibidora", "freezer"]
COLUMNAS_BEBIDA = ["exhibidora", "bajo_mostrador", "deposito"]
COLUMNAS_SIMPLE = ["cantidad"]

CATEGORIAS = [
    {
        "nombre": "FAINA",
        "tipo": "comida",
        "productos": ["Faina Entera"],
    },
    {
        "nombre": "EMPANADAS",
        "tipo": "comida",
        "productos": [
            "Bondiola", "Capresse", "Carne Cuchillo", "Carne Picante",
            "Carne Suave", "Cebolla y Queso", "Cheeseburger", "Humita",
            "Jamón y Queso", "Pollo", "Roquefort con Jamón", "Verdura",
            "Choclo y Calabaza Integral", "Puerro y Hongos",
            "Carne a la Criolla Vegana", "Pollo al Curry Vegana",
            "Bondiola (integral)",
        ],
    },
    {
        "nombre": "BURRITOS",
        "tipo": "comida",
        "productos": [
            "Burrito de Ternera", "Burrito de Cerdo (Bondiola)",
            "Burrito de Pollo", "Burrito Vegetariano",
        ],
    },
    {
        "nombre": "SANDWICHES",
        "tipo": "comida",
        "productos": [
            "Combo Focaccia", "Combo Panchos",
            "Porciones Bondiola", "Porciones Pollo", "Porciones Ternera",
            "Sandwich Indiv. Bondiola", "Sandwich Indiv. Pollo",
            "Sandwich Indiv. Ternera",
        ],
    },
    {
        "nombre": "INGREDIENTES PIZZAS",
        "tipo": "comida",
        "productos": [
            "Rollo de Muzzarella 380gr (Mega)", "Rollo de Muzzarella 190gr (Grande)",
            "Prepizza de 40cm (Mega)", "Prepizza de 32cm (Grande)",
            "Bollo de Masa de 600gr (Mega)", "Bollo de Masa de 400gr (Grande)",
        ],
    },
    {
        "nombre": "VARIOS",
        "tipo": "comida",
        "productos": ["Medialunas"],
    },
    {
        "nombre": "BEBIDAS",
        "tipo": "bebida",
        "productos": [
            "Fanta 237ml", "Sprite Zero 237ml",
            "Agua Benedictino CON gas 1.5L", "Agua Benedictino CON gas 600ml",
            "Agua Benedictino SIN gas 1.5L", "Agua Benedictino SIN gas 600ml",
            "Coca Cola 237ml", "Coca Cola 600ml",
            "Coca Cola Zero 237ml", "Coca Cola Zero 600ml",
            "Fanta 600ml", "Sprite Zero 600ml", "Sprite 600ml",
            "Coca Cola 1.75L", "Coca Cola Zero 1.75L",
            "Sprite 1.75L", "Sprite Zero 1.75L",
            "Aquarius Pera 1.5L", "Quilmes Lata 473ml", "Monster 437ml",
            "Aquarius Manzana 600ml", "Aquarius Pera 600ml",
            "Aquarius Ananá y Jengibre 600ml", "Aquarius Pera 237ml",
            "Aquarius Pomelo 600ml", "Aquarius Pomelo Rosado 600ml",
            "Aquarius Uva 600ml", "Aquarius Uva 237ml",
            "Chocolatada 600ml", "Chocolatada 200ml",
        ],
    },
    {
        "nombre": "INGREDIENTES",
        "tipo": "simple",
        "productos": [
            "Queso Roquefort", "Queso Provolone", "Tomate redondos",
            "Tomate salsa", "Cebollas", "Jamón cocido gm/fetas",
            "Aceitunas verdes", "Ajo", "Orégano",
        ],
    },
    {
        "nombre": "OTROS",
        "tipo": "simple",
        "productos": [
            "Rollos térmico comandera", "Rollos térmico posnet",
            "Caja Docena", "Caja pizza grande", "Caja pizza mega",
            "Bolsas Kraf chica (3 empanadas)", "Bolsas Kraf grande (6 empanadas)",
            "Bolsa de arranque grandes", "Bolsas de arranque chicas",
            "Bolsa camiseta 40x50 (NO REFORZADAS)", "Banditas elásticas",
            "Toallitas mano", "Servilletas caja", "Papel higiénico",
            "Jabón para manos", "Lavandina", "Líquido para piso",
        ],
    },
]

def columnas_de(tipo: str) -> list[str]:
    """Devuelve las columnas de conteo según el tipo de categoría."""
    if tipo == "bebida":
        return COLUMNAS_BEBIDA
    if tipo == "simple":
        return COLUMNAS_SIMPLE
    return COLUMNAS_COMIDA
