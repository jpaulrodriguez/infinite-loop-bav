"""
Brand Intelligence Engine — Anti-Hallucination Layer
Procesa datos reales del BRANDS array, calcula promedios de sector,
genera narrativa EPIC personalizada. Nunca inventa datos.
"""
import math
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════════════════
# BASE DE DATOS — 82 MARCAS COLOMBIA BAV 2026
# ═══════════════════════════════════════════════════════════
RAW_BRANDS = [
  # cx_kpi = CX Strategy · Síndrome de París
  # Fórmula: percentil_rank(brand_asset_rank_usuarios - brand_asset_rank_no_usuarios) × 100
  # Fuente: Brandscape Colombia 2026 — Usuarios vs No Usuarios (81/82 marcas)
  {"marca":"Aguila","bx":58.4,"co":38.3,"cx":56.6,"brand_asset":57.7,"bav_pulse":59.0,"commerce":38.3,"cx_kpi":78.7,"loyalty":51.9},
  {"marca":"Alkosto","bx":64.2,"co":79.0,"cx":39.1,"brand_asset":84.6,"bav_pulse":43.8,"commerce":79.0,"cx_kpi":48.9,"loyalty":53.2},
  {"marca":"American Airlines","bx":48.3,"co":96.3,"cx":34.8,"brand_asset":26.9,"bav_pulse":69.8,"commerce":96.3,"cx_kpi":18.2,"loyalty":59.5},
  {"marca":"Andina (beer)","bx":14.0,"co":56.8,"cx":37.0,"brand_asset":6.4,"bav_pulse":21.6,"commerce":56.8,"cx_kpi":63.0,"loyalty":19.0},
  {"marca":"Arturo Calle","bx":65.7,"co":76.5,"cx":40.5,"brand_asset":91.0,"bav_pulse":40.4,"commerce":76.5,"cx_kpi":41.7,"loyalty":72.2},
  {"marca":"Avianca","bx":60.1,"co":23.5,"cx":71.1,"brand_asset":60.3,"bav_pulse":59.9,"commerce":23.5,"cx_kpi":51.4,"loyalty":75.9},
  {"marca":"BMW","bx":73.7,"co":45.7,"cx":47.9,"brand_asset":71.8,"bav_pulse":75.6,"commerce":45.7,"cx_kpi":55.3,"loyalty":62.0},
  {"marca":"Bavaria","bx":41.6,"co":14.8,"cx":91.2,"brand_asset":None,"bav_pulse":41.6,"commerce":14.8,"cx_kpi":63.0,"loyalty":None},
  {"marca":"Biomax","bx":18.4,"co":84.0,"cx":66.5,"brand_asset":7.7,"bav_pulse":29.0,"commerce":84.0,"cx_kpi":91.3,"loyalty":35.4},
  {"marca":"Budweiser","bx":58.8,"co":14.8,"cx":42.0,"brand_asset":50.0,"bav_pulse":67.6,"commerce":14.8,"cx_kpi":45.5,"loyalty":27.8},
  {"marca":"Carulla","bx":34.8,"co":48.1,"cx":9.5,"brand_asset":33.3,"bav_pulse":36.4,"commerce":48.1,"cx_kpi":17.4,"loyalty":16.5},
  {"marca":"Cencosud","bx":40.2,"co":27.2,"cx":25.1,"brand_asset":21.8,"bav_pulse":58.6,"commerce":27.2,"cx_kpi":22.1,"loyalty":7.6},
  {"marca":"Cerveza BBC","bx":44.6,"co":14.8,"cx":44.5,"brand_asset":42.3,"bav_pulse":46.9,"commerce":14.8,"cx_kpi":44.0,"loyalty":26.6},
  {"marca":"Chevignon","bx":37.1,"co":25.9,"cx":40.9,"brand_asset":44.9,"bav_pulse":29.3,"commerce":25.9,"cx_kpi":63.0,"loyalty":50.6},
  {"marca":"Chevrolet","bx":68.2,"co":42.0,"cx":80.5,"brand_asset":52.6,"bav_pulse":83.9,"commerce":42.0,"cx_kpi":58.9,"loyalty":74.7},
  {"marca":"Claro","bx":40.5,"co":13.6,"cx":33.5,"brand_asset":29.5,"bav_pulse":51.6,"commerce":13.6,"cx_kpi":34.9,"loyalty":63.3},
  {"marca":"Club Colombia","bx":74.5,"co":14.8,"cx":73.7,"brand_asset":78.2,"bav_pulse":70.7,"commerce":14.8,"cx_kpi":41.7,"loyalty":94.9},
  {"marca":"Coca-Cola","bx":86.2,"co":75.3,"cx":86.1,"brand_asset":96.2,"bav_pulse":76.2,"commerce":75.3,"cx_kpi":63.0,"loyalty":77.2},
  {"marca":"Colombiana Postobón","bx":57.8,"co":32.1,"cx":41.5,"brand_asset":83.3,"bav_pulse":32.4,"commerce":32.1,"cx_kpi":41.7,"loyalty":54.4},
  {"marca":"Colpatria","bx":17.8,"co":3.7,"cx":46.4,"brand_asset":5.1,"bav_pulse":30.5,"commerce":3.7,"cx_kpi":15.3,"loyalty":17.7},
  {"marca":"Copa Airlines","bx":45.9,"co":59.3,"cx":31.5,"brand_asset":43.6,"bav_pulse":48.1,"commerce":59.3,"cx_kpi":27.0,"loyalty":41.8},
  {"marca":"Corona (beer)","bx":81.2,"co":14.8,"cx":74.2,"brand_asset":87.2,"bav_pulse":75.3,"commerce":14.8,"cx_kpi":96.7,"loyalty":79.7},
  {"marca":"Cruz Verde","bx":54.8,"co":63.0,"cx":71.0,"brand_asset":66.7,"bav_pulse":42.9,"commerce":63.0,"cx_kpi":63.0,"loyalty":57.0},
  {"marca":"D1","bx":70.1,"co":88.9,"cx":49.4,"brand_asset":93.6,"bav_pulse":46.6,"commerce":88.9,"cx_kpi":27.0,"loyalty":98.7},
  {"marca":"Decameron","bx":60.2,"co":4.9,"cx":71.7,"brand_asset":61.5,"bav_pulse":59.0,"commerce":4.9,"cx_kpi":82.1,"loyalty":67.1},
  {"marca":"Droguerías Olímpica","bx":24.1,"co":51.9,"cx":61.5,"brand_asset":38.5,"bav_pulse":9.8,"commerce":51.9,"cx_kpi":95.7,"loyalty":24.1},
  {"marca":"ETB","bx":24.2,"co":7.4,"cx":20.7,"brand_asset":19.2,"bav_pulse":29.3,"commerce":7.4,"cx_kpi":71.1,"loyalty":11.4},
  {"marca":"Easy Fly","bx":18.6,"co":30.9,"cx":26.2,"brand_asset":9.0,"bav_pulse":28.1,"commerce":30.9,"cx_kpi":39.4,"loyalty":6.3},
  {"marca":"El Corral","bx":53.6,"co":72.8,"cx":36.1,"brand_asset":56.4,"bav_pulse":50.9,"commerce":72.8,"cx_kpi":7.0,"loyalty":70.9},
  {"marca":"Esso","bx":24.2,"co":90.1,"cx":50.2,"brand_asset":15.4,"bav_pulse":33.0,"commerce":90.1,"cx_kpi":86.9,"loyalty":32.9},
  {"marca":"Exito","bx":66.7,"co":48.1,"cx":86.8,"brand_asset":74.4,"bav_pulse":58.9,"commerce":48.1,"cx_kpi":63.0,"loyalty":84.8},
  {"marca":"Falabella","bx":85.9,"co":65.4,"cx":88.7,"brand_asset":97.4,"bav_pulse":74.4,"commerce":65.4,"cx_kpi":78.7,"loyalty":83.5},
  {"marca":"Farmacia Pasteur","bx":18.6,"co":81.5,"cx":26.9,"brand_asset":2.6,"bav_pulse":34.6,"commerce":81.5,"cx_kpi":21.3,"loyalty":3.8},
  {"marca":"Farmatodo","bx":58.1,"co":70.4,"cx":55.0,"brand_asset":76.9,"bav_pulse":39.2,"commerce":70.4,"cx_kpi":29.8,"loyalty":93.7},
  {"marca":"Ford","bx":70.0,"co":80.2,"cx":65.3,"brand_asset":73.1,"bav_pulse":67.0,"commerce":80.2,"cx_kpi":94.3,"loyalty":46.8},
  {"marca":"Frisby","bx":74.2,"co":67.9,"cx":80.6,"brand_asset":100.0,"bav_pulse":48.4,"commerce":67.9,"cx_kpi":63.0,"loyalty":89.9},
  {"marca":"Grupo Aval","bx":28.8,"co":1.2,"cx":18.1,"brand_asset":16.7,"bav_pulse":40.8,"commerce":1.2,"cx_kpi":45.5,"loyalty":10.1},
  {"marca":"H&M","bx":54.8,"co":50.6,"cx":61.6,"brand_asset":35.9,"bav_pulse":73.8,"commerce":50.6,"cx_kpi":18.2,"loyalty":49.4},
  {"marca":"Hatsu","bx":35.6,"co":32.1,"cx":32.7,"brand_asset":37.2,"bav_pulse":34.0,"commerce":32.1,"cx_kpi":29.6,"loyalty":30.4},
  {"marca":"Heineken","bx":55.0,"co":56.8,"cx":57.3,"brand_asset":53.8,"bav_pulse":56.2,"commerce":56.8,"cx_kpi":24.5,"loyalty":65.8},
  {"marca":"Honda","bx":74.4,"co":39.5,"cx":30.3,"brand_asset":69.2,"bav_pulse":79.6,"commerce":39.5,"cx_kpi":91.8,"loyalty":45.6},
  {"marca":"Hyundai","bx":64.1,"co":92.6,"cx":72.9,"brand_asset":59.0,"bav_pulse":69.2,"commerce":92.6,"cx_kpi":70.3,"loyalty":64.6},
  {"marca":"JetSmart","bx":21.4,"co":71.6,"cx":38.9,"brand_asset":12.8,"bav_pulse":29.9,"commerce":71.6,"cx_kpi":31.9,"loyalty":20.3},
  {"marca":"Jumbo","bx":68.0,"co":27.2,"cx":66.8,"brand_asset":89.7,"bav_pulse":46.3,"commerce":27.2,"cx_kpi":48.3,"loyalty":88.6},
  {"marca":"KFC","bx":60.5,"co":55.6,"cx":None,"brand_asset":None,"bav_pulse":60.5,"commerce":55.6,"cx_kpi":None,"loyalty":None},
  {"marca":"Kia","bx":72.3,"co":69.1,"cx":66.8,"brand_asset":75.6,"bav_pulse":69.1,"commerce":69.1,"cx_kpi":38.3,"loyalty":78.5},
  {"marca":"Koaj","bx":43.0,"co":82.7,"cx":48.0,"brand_asset":55.1,"bav_pulse":30.9,"commerce":82.7,"cx_kpi":0.9,"loyalty":68.4},
  {"marca":"Makro","bx":45.3,"co":44.4,"cx":10.1,"brand_asset":39.7,"bav_pulse":50.9,"commerce":44.4,"cx_kpi":6.8,"loyalty":13.9},
  {"marca":"Manzana Postobón","bx":51.2,"co":32.1,"cx":24.0,"brand_asset":67.9,"bav_pulse":34.6,"commerce":32.1,"cx_kpi":13.8,"loyalty":34.2},
  {"marca":"Mazda","bx":82.2,"co":87.7,"cx":44.9,"brand_asset":79.5,"bav_pulse":84.9,"commerce":87.7,"cx_kpi":48.9,"loyalty":82.3},
  {"marca":"McDonald's","bx":82.2,"co":66.7,"cx":59.0,"brand_asset":65.4,"bav_pulse":99.1,"commerce":66.7,"cx_kpi":81.3,"loyalty":39.2},
  {"marca":"Mercado Libre","bx":89.6,"co":86.4,"cx":51.8,"brand_asset":94.9,"bav_pulse":84.3,"commerce":86.4,"cx_kpi":44.0,"loyalty":91.1},
  {"marca":"Mercado Zapatoca","bx":18.4,"co":85.2,"cx":18.8,"brand_asset":14.1,"bav_pulse":22.8,"commerce":85.2,"cx_kpi":2.4,"loyalty":0.0},
  {"marca":"Metro","bx":39.0,"co":27.2,"cx":64.6,"brand_asset":51.3,"bav_pulse":26.8,"commerce":27.2,"cx_kpi":83.1,"loyalty":36.7},
  {"marca":"Movistar","bx":43.5,"co":8.6,"cx":47.2,"brand_asset":41.0,"bav_pulse":46.0,"commerce":8.6,"cx_kpi":42.6,"loyalty":58.2},
  {"marca":"Nissan","bx":79.2,"co":64.2,"cx":70.5,"brand_asset":82.1,"bav_pulse":76.2,"commerce":64.2,"cx_kpi":63.0,"loyalty":81.0},
  {"marca":"OXXO","bx":62.0,"co":43.2,"cx":48.9,"brand_asset":48.7,"bav_pulse":75.3,"commerce":43.2,"cx_kpi":83.7,"loyalty":15.2},
  {"marca":"Olímpica","bx":46.0,"co":51.9,"cx":21.5,"brand_asset":62.8,"bav_pulse":29.3,"commerce":51.9,"cx_kpi":95.7,"loyalty":38.0},
  {"marca":"Petrobras","bx":24.2,"co":98.8,"cx":50.1,"brand_asset":1.3,"bav_pulse":47.2,"commerce":98.8,"cx_kpi":83.1,"loyalty":12.7},
  {"marca":"Poker (beer)","bx":42.4,"co":14.8,"cx":40.9,"brand_asset":28.2,"bav_pulse":56.5,"commerce":14.8,"cx_kpi":24.5,"loyalty":43.0},
  {"marca":"Postobón","bx":70.5,"co":32.1,"cx":65.4,"brand_asset":92.3,"bav_pulse":48.8,"commerce":32.1,"cx_kpi":55.3,"loyalty":60.8},
  {"marca":"Primax","bx":27.9,"co":97.5,"cx":42.3,"brand_asset":11.5,"bav_pulse":44.4,"commerce":97.5,"cx_kpi":7.6,"loyalty":73.4},
  {"marca":"Quatro","bx":35.6,"co":32.1,"cx":54.6,"brand_asset":46.2,"bav_pulse":25.0,"commerce":32.1,"cx_kpi":78.7,"loyalty":44.3},
  {"marca":"Rappi","bx":79.5,"co":40.7,"cx":69.0,"brand_asset":85.9,"bav_pulse":73.1,"commerce":40.7,"cx_kpi":86.9,"loyalty":48.1},
  {"marca":"Renault","bx":88.5,"co":77.8,"cx":69.3,"brand_asset":88.5,"bav_pulse":88.6,"commerce":77.8,"cx_kpi":52.5,"loyalty":97.5},
  {"marca":"Satena","bx":23.0,"co":74.1,"cx":40.8,"brand_asset":17.9,"bav_pulse":28.1,"commerce":74.1,"cx_kpi":50.3,"loyalty":22.8},
  {"marca":"Seguros Bolivar","bx":31.0,"co":2.5,"cx":39.1,"brand_asset":25.6,"bav_pulse":36.4,"commerce":2.5,"cx_kpi":24.5,"loyalty":55.7},
  {"marca":"Stella Artois","bx":48.4,"co":14.8,"cx":35.1,"brand_asset":30.8,"bav_pulse":66.0,"commerce":14.8,"cx_kpi":81.3,"loyalty":21.5},
  {"marca":"Sura","bx":70.0,"co":0.0,"cx":54.2,"brand_asset":80.8,"bav_pulse":59.3,"commerce":0.0,"cx_kpi":97.7,"loyalty":87.3},
  {"marca":"Suzuki","bx":76.0,"co":46.9,"cx":74.8,"brand_asset":70.5,"bav_pulse":81.5,"commerce":46.9,"cx_kpi":88.7,"loyalty":69.6},
  {"marca":"Telefónica","bx":28.3,"co":8.6,"cx":17.5,"brand_asset":20.5,"bav_pulse":36.1,"commerce":8.6,"cx_kpi":22.1,"loyalty":1.3},
  {"marca":"Tennis (clothing)","bx":35.8,"co":24.7,"cx":32.1,"brand_asset":47.4,"bav_pulse":24.1,"commerce":24.7,"cx_kpi":4.7,"loyalty":40.5},
  {"marca":"Terpel","bx":66.3,"co":90.1,"cx":86.2,"brand_asset":64.1,"bav_pulse":68.5,"commerce":90.1,"cx_kpi":76.5,"loyalty":100.0},
  {"marca":"Texaco","bx":21.5,"co":93.8,"cx":98.1,"brand_asset":3.8,"bav_pulse":39.2,"commerce":93.8,"cx_kpi":91.8,"loyalty":96.2},
  {"marca":"Tiendas Isimo","bx":10.6,"co":51.9,"cx":10.7,"brand_asset":10.3,"bav_pulse":10.8,"commerce":51.9,"cx_kpi":15.3,"loyalty":2.5},
  {"marca":"Tigo","bx":41.7,"co":11.1,"cx":68.7,"brand_asset":32.1,"bav_pulse":51.2,"commerce":11.1,"cx_kpi":47.8,"loyalty":86.1},
  {"marca":"Tigo UNE","bx":38.5,"co":12.3,"cx":35.8,"brand_asset":34.6,"bav_pulse":42.3,"commerce":12.3,"cx_kpi":27.0,"loyalty":31.6},
  {"marca":"Totto","bx":43.5,"co":61.7,"cx":44.5,"brand_asset":None,"bav_pulse":43.5,"commerce":61.7,"cx_kpi":68.6,"loyalty":25.3},
  {"marca":"Toyota","bx":92.2,"co":95.1,"cx":94.3,"brand_asset":98.7,"bav_pulse":85.8,"commerce":95.1,"cx_kpi":73.0,"loyalty":92.4},
  {"marca":"United Airlines","bx":38.4,"co":100.0,"cx":24.4,"brand_asset":23.1,"bav_pulse":53.7,"commerce":100.0,"cx_kpi":63.0,"loyalty":5.1},
  {"marca":"WOM","bx":26.2,"co":6.2,"cx":13.2,"brand_asset":0.0,"bav_pulse":52.5,"commerce":6.2,"cx_kpi":32.3,"loyalty":8.9},
  {"marca":"Wingo","bx":27.1,"co":59.3,"cx":53.3,"brand_asset":24.4,"bav_pulse":29.9,"commerce":59.3,"cx_kpi":83.7,"loyalty":29.1},
]

# ═══════════════════════════════════════════════════════════
# CLASIFICACIÓN DE CATEGORÍAS
# ═══════════════════════════════════════════════════════════
CATEGORIES = {
    "Retail Gran Superficie": [
        "Makro","D1","Jumbo","Exito","Carulla","Olímpica","Metro",
        "Alkosto","Cencosud","Mercado Zapatoca","Tiendas Isimo"
    ],
    "Retail Especializado y Moda": [
        "Falabella","Arturo Calle","Chevignon","H&M","Koaj","Tennis (clothing)","Totto"
    ],
    "Aerolíneas": [
        "Avianca","American Airlines","Copa Airlines","JetSmart","Wingo","Satena","Easy Fly","United Airlines"
    ],
    "Telecomunicaciones": [
        "Claro","Movistar","Tigo","Tigo UNE","ETB","WOM","Telefónica"
    ],
    "Automotriz": [
        "BMW","Chevrolet","Ford","Honda","Hyundai","Kia","Mazda","Nissan","Renault","Suzuki","Toyota"
    ],
    "Cervezas y Bebidas Alcohólicas": [
        "Aguila","Andina (beer)","Bavaria","Budweiser","Cerveza BBC",
        "Club Colombia","Corona (beer)","Heineken","Poker (beer)","Stella Artois"
    ],
    "Bebidas No Alcohólicas": [
        "Coca-Cola","Colombiana Postobón","Hatsu","Manzana Postobón","Postobón","Quatro"
    ],
    "Comidas Rápidas": [
        "McDonald's","KFC","Frisby","El Corral"
    ],
    "Farmacias y Salud": [
        "Cruz Verde","Droguerías Olímpica","Farmacia Pasteur","Farmatodo"
    ],
    "Combustibles y Estaciones": [
        "Biomax","Esso","Petrobras","Primax","Terpel","Texaco"
    ],
    "Finanzas y Seguros": [
        "Colpatria","Grupo Aval","Sura","Seguros Bolivar"
    ],
    "E-commerce y Delivery": [
        "Mercado Libre","Rappi","OXXO"
    ],
    "Turismo y Hotelería": [
        "Decameron"
    ],
}

# ═══════════════════════════════════════════════════════════
# ANTI-HALLUCINATION: VALIDACIÓN ESTRICTA
# ═══════════════════════════════════════════════════════════

def validate_brand(nombre: str) -> dict:
    """Retorna los datos de la marca o lanza error verificable."""
    brand = next((b for b in RAW_BRANDS if b["marca"] == nombre), None)
    if brand is None:
        raise ValueError(f"Marca '{nombre}' no existe en la base de datos.")
    return brand

def safe_val(v, default=None):
    """Retorna None si el valor es nulo, NaN o no es número."""
    if v is None:
        return default
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return default
        return round(f, 1)
    except (TypeError, ValueError):
        return default

def _avg(values):
    """Promedio solo de valores válidos."""
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 1) if clean else None

def get_category(nombre: str) -> str:
    for cat, brands in CATEGORIES.items():
        if nombre in brands:
            return cat
    return "Mercado General"

def get_sector_brands(nombre: str) -> list:
    """Retorna todas las marcas del mismo sector con datos validados."""
    cat = get_category(nombre)
    peers = CATEGORIES.get(cat, [])
    result = []
    for b in RAW_BRANDS:
        if b["marca"] in peers:
            result.append(b)
    return result

def compute_sector_avg(sector_brands: list, exclude: str) -> dict:
    """
    Calcula promedios reales del sector excluyendo la marca analizada.
    Solo promedia valores no-null.
    """
    peers = [b for b in sector_brands if b["marca"] != exclude]
    fields = ["bx","co","cx","brand_asset","bav_pulse","commerce","cx_kpi","loyalty"]
    avgs = {}
    for f in fields:
        vals = [safe_val(b.get(f)) for b in peers]
        avgs[f] = _avg([v for v in vals if v is not None])
    avgs["_n"] = len(peers)
    return avgs

def rank_in_sector(brand_name: str, field: str, sector_brands: list) -> tuple:
    """
    Retorna (posición, total) de la marca en el sector para un campo dado.
    Posición 1 = mejor. Excluye null values.
    """
    valid = [(b["marca"], safe_val(b.get(field)))
             for b in sector_brands if safe_val(b.get(field)) is not None]
    valid.sort(key=lambda x: x[1], reverse=True)
    total = len(valid)
    for i, (nm, _) in enumerate(valid, 1):
        if nm == brand_name:
            return (i, total)
    return (None, total)

def semaphore(v) -> str:
    if v is None: return "sin_dato"
    if v < 34: return "rojo"
    if v < 67: return "amarillo"
    return "verde"

# ═══════════════════════════════════════════════════════════
# MOTOR ÉPIC: ANÁLISIS PERSONALIZADO
# ═══════════════════════════════════════════════════════════

def _gap_label(gap: float) -> str:
    """Convierte un gap numérico a lenguaje humano."""
    abs_g = abs(gap)
    direction = "por encima" if gap > 0 else "por debajo"
    if abs_g < 5:
        return f"prácticamente igual al promedio del sector"
    if abs_g < 15:
        return f"{abs_g:.0f} puntos {direction} del sector"
    if abs_g < 30:
        return f"{abs_g:.0f} puntos {direction} del sector — brecha significativa"
    return f"{abs_g:.0f} puntos {direction} del sector — brecha crítica"

def _score_label(v) -> str:
    if v is None: return "sin dato disponible"
    if v < 20: return "muy bajo"
    if v < 34: return "bajo"
    if v < 50: return "medio-bajo"
    if v < 67: return "medio"
    if v < 80: return "alto"
    return "muy alto"

def generate_dominant_idea(b: dict, avg: dict, sector: str) -> str:
    """
    Idea dominante generada en dos capas:
    1. Diagnóstico de sub-indicadores para entender el PORQUÉ del score
    2. Cruce de tensiones entre frentes para encontrar el insight no obvio
    La regla: nunca quedarse con el primer hallazgo (score más bajo = palanca).
    Siempre bajar un nivel más para explicar la causa raíz.
    """
    bx      = safe_val(b.get("bx"))
    co      = safe_val(b.get("co"))
    cx      = safe_val(b.get("cx"))
    ba      = safe_val(b.get("brand_asset"))    # sub-BX: equity percibido (D,R,E,F BAV)
    pulse   = safe_val(b.get("bav_pulse"))       # sub-BX: presencia digital GT+Wiki+Social
    loyalty = safe_val(b.get("loyalty"))         # sub-CX: conocimiento familiar (eFam)
    cx_kpi  = safe_val(b.get("cx_kpi"))          # sub-CX: síndrome de París (usuarios vs no usuarios)
    commerce= safe_val(b.get("commerce"))        # sub-CO: eficiencia ingresos/activos

    avg_bx  = avg.get("bx")
    avg_co  = avg.get("co")
    avg_cx  = avg.get("cx")
    nombre  = b["marca"]

    gaps = {}
    if bx is not None and avg_bx is not None:
        gaps["bx"] = round(bx - avg_bx, 1)
    if co is not None and avg_co is not None:
        gaps["co"] = round(co - avg_co, 1)
    if cx is not None and avg_cx is not None:
        gaps["cx"] = round(cx - avg_cx, 1)

    # ── CAPA 1: ANÁLISIS DE SUB-INDICADORES ────────────────────────────────
    # Antes de etiquetar un frente como "débil", examinar qué lo compone y por qué.

    # ─ BX Diagnóstico: distinguir si el problema es brand equity o visibilidad digital
    bx_gap_origen = None
    if bx is not None and ba is not None and pulse is not None:
        if ba > 60 and pulse < 35:
            bx_gap_origen = "digital_invisible"   # marca fuerte offline, invisible online
        elif ba < 35 and pulse > 55:
            bx_gap_origen = "digital_sin_sustancia"  # presencia digital sin equity real
        elif ba < 35 and pulse < 35:
            bx_gap_origen = "bx_doble_debilidad"   # débil en los dos frentes del BX

    # ─ CX Diagnóstico: distinguir si el problema es lealtad o experiencia de usuario actual
    cx_gap_origen = None
    if cx is not None and loyalty is not None and cx_kpi is not None:
        if loyalty > 65 and cx_kpi < 35:
            cx_gap_origen = "conocido_pero_no_elegido"  # lo conocen bien pero los usuarios no lo prefieren más
        elif loyalty < 30 and cx_kpi > 60:
            cx_gap_origen = "usuarios_fieles_poca_masa"  # usuarios actuales la adoran pero base pequeña
        elif loyalty < 30 and cx_kpi < 35:
            cx_gap_origen = "cx_doble_debilidad"   # ni conocimiento ni preferencia de usuarios

    # ── CAPA 2: PATRONES CRUZADOS DE ALTA ESPECIFICIDAD ────────────────────
    # Cada patrón cruza al menos dos dimensiones + sub-indicador para llegar al insight real.

    # ── LIDERAZGO Y AMENAZAS DE MARCA FUERTE ───────────────────────────────

    # Liderazgo absoluto — diagnóstico de dónde está el riesgo real
    if bx is not None and co is not None and cx is not None and bx >= 65 and co >= 65 and cx >= 65:
        if loyalty is not None and pulse is not None:
            if pulse < 50:
                return (f"{nombre} lidera en los tres frentes del Capital Intangible "
                        f"(BX {bx:.0f} · CO {co:.0f} · CX {cx:.0f}/100), pero su presencia digital "
                        f"({pulse:.0f}/100 en BAV Pulse) está por debajo de lo que su posición de mercado exige. "
                        f"Una marca de este calibre que no domina el espacio digital cede territorio "
                        f"a competidores más pequeños pero más visibles en los canales donde se forma "
                        f"la primera intención de compra.")
            elif loyalty is not None and loyalty > 75:
                return (f"{nombre} opera en el cuadrante de liderazgo con una base de clientes "
                        f"que recompra (lealtad {loyalty:.0f}/100). "
                        f"El riesgo no viene de dentro sino de afuera: en mercados maduros, "
                        f"las marcas líderes pierden cuota no por ejecutar mal "
                        f"sino por sobreestimar la inercia del consumidor. "
                        f"La agenda estratégica es anticipación competitiva, no optimización del status quo.")
        return (f"{nombre} lidera en marca, ventas y experiencia. "
                f"El reto no es construir sino defender: los líderes pierden posición "
                f"cuando optimizan lo que ya funciona en lugar de anticipar el siguiente movimiento del mercado.")

    # BX fuerte + CO fuerte + CX con problema de causa raíz
    if bx is not None and co is not None and cx is not None and bx > 60 and co > 55 and cx < 50:
        if cx_gap_origen == "conocido_pero_no_elegido":
            return (f"{nombre} convierte bien (CO {co:.0f}/100) y tiene marca reconocida "
                    f"(BX {bx:.0f}/100), pero el Síndrome de París revela una señal de alerta: "
                    f"los No Usuarios valoran la marca casi igual que los Usuarios ({cx_kpi:.0f}/100 en CX Strategy). "
                    f"Eso significa que la experiencia real no supera la expectativa — "
                    f"el consumidor llega con una imagen fuerte y sale sin una historia que contar. "
                    f"La palanca no es más marketing sino elevar el gap entre lo que promete y lo que entrega.")
        if loyalty is not None and loyalty < 35:
            return (f"{nombre} vende (CO {co:.0f}/100) pero no retiene: lealtad en {loyalty:.0f}/100. "
                    f"Con BX {bx:.0f}/100, la marca tiene el reconocimiento para atraer — "
                    f"el problema ocurre después de la primera compra. "
                    f"Cada cliente que no regresa es un costo de adquisición perdido. "
                    f"El cuello de botella está en la experiencia post-venta, no en el embudo de entrada.")

    # ── PATRONES CO BAJO CON DIAGNÓSTICO DE CAUSA ─────────────────────────

    # CO muy bajo + BX alto: marca que no convierte — ¿por qué?
    if co is not None and co < 20 and bx is not None and bx > 50:
        if cx is not None and cx > 60:
            # CX también alto: el problema no es la experiencia sino el modelo comercial
            return (f"{nombre} tiene marca reconocida (BX {bx:.0f}/100) y clientes satisfechos "
                    f"(CX {cx:.0f}/100), pero un CO de {co:.0f}/100 señala que el modelo comercial "
                    f"no está capturando esa demanda. "
                    f"La marca genera deseo y la experiencia lo sostiene — lo que falla "
                    f"es la activación: los puntos de contacto donde el interés se convierte en transacción. "
                    f"{'La lealtad de ' + str(int(loyalty)) + '/100 confirma que quien llega, vuelve — el problema es que llegan pocos.' if loyalty and loyalty > 55 else ''}")
        elif loyalty is not None and loyalty > 65:
            # Clientes fieles pero pocos: embudo de entrada estrecho
            return (f"{nombre} tiene clientes leales (lealtad {loyalty:.0f}/100) y una marca visible "
                    f"(BX {bx:.0f}/100), pero CO en {co:.0f}/100 indica que el embudo de adquisición "
                    f"es muy estrecho. "
                    f"La base actual es fiel pero pequeña: la marca retiene bien a quien ya convirtió "
                    f"pero no está atrayendo suficientes clientes nuevos. "
                    f"La palanca es expansión de cobertura, no profundización de la relación existente.")
        else:
            return (f"Con BX {bx:.0f}/100, {nombre} ocupa espacio mental en el mercado, "
                    f"pero CO {co:.0f}/100 indica que ese espacio no se traduce en transacciones. "
                    f"La hipótesis más probable: hay fricción entre la intención y la compra — "
                    f"ya sea en distribución, precio, o accesibilidad del producto. "
                    f"El siguiente paso diagnóstico es mapear dónde se rompe el journey del consumidor.")

    # CO crítico absoluto + BX bajo: doble problema de origen
    if co is not None and co < 10 and bx is not None and bx < 35:
        return (f"{nombre} enfrenta un problema de base: CO {co:.0f}/100 y BX {bx:.0f}/100 "
                f"indican que ni la marca ni el modelo comercial están funcionando. "
                f"No hay un frente ancla desde el que construir — intentar activar ventas "
                f"sin marca es costoso y frágil. "
                f"La secuencia correcta: primero generar reconocimiento y diferenciación, "
                f"luego activar la conversión sobre esa base.")

    # ── PATRONES CX CON DIAGNÓSTICO DE CAUSA RAÍZ ─────────────────────────

    # CX bajo por síndrome de París: los no usuarios la valoran igual que los usuarios
    if cx_gap_origen == "conocido_pero_no_elegido" and cx is not None and cx < 45:
        return (f"El Síndrome de París de {nombre} ({cx_kpi:.0f}/100) revela el problema de fondo: "
                f"los No Usuarios valoran la marca casi igual que los Usuarios actuales. "
                f"Eso indica que la experiencia real no genera una ventaja perceptual sobre la expectativa. "
                f"La marca atrae pero no sorprende — y sin esa sorpresa, la lealtad se construye "
                f"sobre precio o conveniencia, no sobre el valor diferencial de la marca misma. "
                f"La prioridad es elevar el gap experiencial: que los clientes actuales "
                f"tengan razones concretas para preferirla que los no-clientes no pueden imaginar.")

    # CX bajo porque la base de usuarios fieles es pequeña
    if cx_gap_origen == "usuarios_fieles_poca_masa" and cx is not None and cx < 50:
        co_txt = f" CO {co:.0f}/100 confirma que el volumen transaccional no acompaña esa intensidad." if co is not None and co < 45 else ""
        return (f"{nombre} tiene usuarios que la valoran intensamente (CX Strategy {cx_kpi:.0f}/100), "
                f"pero la lealtad baja ({loyalty:.0f}/100) indica que esa base es pequeña. "
                f"El problema no es la calidad de la experiencia sino su alcance: "
                f"la marca no está llegando a suficientes personas.{co_txt} "
                f"La palanca es ampliar la cobertura sin diluir lo que hace especial "
                f"la experiencia para quienes ya la conocen.")

    # CX doble debilidad — solo si CO no es el frente dominante (evita ocultar el insight CO > BX)
    if cx_gap_origen == "cx_doble_debilidad" and cx is not None and cx < 40 and (co is None or co < 55):
        return (f"{nombre} enfrenta presión en los dos componentes de la experiencia: "
                f"lealtad baja ({loyalty:.0f}/100) y CX Strategy débil ({cx_kpi:.0f}/100). "
                f"Poca masa de usuarios fieles y una experiencia que no diferencia "
                f"a la marca de sus competidores desde la perspectiva del consumidor actual. "
                f"La reconstrucción de CX debe empezar por identificar el momento "
                f"del journey donde la experiencia pierde valor — no por añadir puntos de contacto.")

    # ── PATRONES RELATIVOS CON EXPLICACIÓN CAUSAL ─────────────────────────

    # BX fuerte + CO débil vs sector — con diagnóstico
    if gaps.get("bx", 0) > 10 and gaps.get("co", 0) < -10:
        if pulse is not None and pulse > 55:
            return (f"{nombre} tiene más presencia de marca que su sector "
                    f"(BX {bx:.0f}/100 vs {avg_bx:.0f}/100 promedio, impulso digital {pulse:.0f}/100), "
                    f"pero ese capital no se traduce en conversión comercial "
                    f"(CO {co:.0f}/100 vs {avg_co:.0f}/100 del sector). "
                    f"La demanda existe y la marca la genera — el cuello de botella "
                    f"está en la última milla: el proceso de compra tiene fricción "
                    f"que la inversión en marca no puede resolver sola.")
        return (f"{nombre} tiene más reconocimiento que su sector (BX {bx:.0f} vs {avg_bx:.0f}/100) "
                f"pero menos conversión (CO {co:.0f} vs {avg_co:.0f}/100). "
                f"La marca llegó a la mente antes que a la transacción. "
                f"La hipótesis: el modelo de captación no está diseñado para aprovechar "
                f"el volumen de intención que la marca genera.")

    # CO fuerte + BX débil vs sector — vende sin marca
    if gaps.get("co", 0) > 10 and gaps.get("bx", 0) < -10:
        loyalty_txt = (f" Con lealtad de {loyalty:.0f}/100, el modelo funciona hoy — "
                       f"pero si el precio o la conveniencia cambian, la razón de compra desaparece."
                       if loyalty and loyalty < 40 else "")
        return (f"{nombre} convierte por encima del sector (CO {co:.0f} vs {avg_co:.0f}/100) "
                f"con una marca más débil que sus pares (BX {bx:.0f} vs {avg_bx:.0f}/100). "
                f"Eso significa que las ventas actuales descansan sobre precio, distribución o conveniencia — "
                f"no sobre preferencia de marca.{loyalty_txt} "
                f"El riesgo: cualquier competidor con mejor ejecución en esos mismos factores "
                f"puede erosionar el volumen sin que {nombre} tenga un activo de marca que lo defienda.")

    # CX fuerte + CO débil vs sector — entrega bien pero no captura
    if gaps.get("cx", 0) > 15 and gaps.get("co", 0) < -5:
        cx_causa = ""
        if cx_kpi is not None and cx_kpi > 60:
            cx_causa = (f" El CX Strategy {cx_kpi:.0f}/100 confirma que los usuarios actuales "
                        f"la prefieren claramente sobre quienes no la usan — "
                        f"la experiencia diferencial existe pero no está siendo monetizada.")
        return (f"{nombre} genera experiencias superiores a su sector (CX {cx:.0f} vs {avg_cx:.0f}/100), "
                f"pero su conversión comercial queda por debajo (CO {co:.0f} vs {avg_co:.0f}/100).{cx_causa} "
                f"La desconexión es estructural: la marca entrega valor pero no ha construido "
                f"los mecanismos para capturarlo — ya sea en pricing, distribución o activación de la demanda.")

    # CO fuerte + CX débil vs sector — vende pero la experiencia erosiona la base
    if gaps.get("co", 0) > 15 and gaps.get("cx", 0) < -5:
        return (f"{nombre} convierte por encima del sector (CO {co:.0f} vs {avg_co:.0f}/100), "
                f"pero la experiencia del cliente queda por debajo (CX {cx:.0f} vs {avg_cx:.0f}/100). "
                f"El modelo comercial funciona en el corto plazo — pero una experiencia "
                f"por debajo del estándar del sector acumula insatisfacción. "
                f"{'Con lealtad de ' + str(int(loyalty)) + '/100, la señal de alerta ya es visible.' if loyalty and loyalty < 40 else 'A medida que los competidores mejoran la experiencia, la brecha de retención se amplía.'}")

    # ── PERFIL EQUILIBRADO: análisis de tensión interna con sub-indicadores ──

    scores_disp = [(f, v) for f, v in [("bx", bx), ("co", co), ("cx", cx)] if v is not None]
    if scores_disp:
        min_f, min_v = min(scores_disp, key=lambda x: x[1])
        max_f, max_v = max(scores_disp, key=lambda x: x[1])
        frente_names = {"bx": "fuerza de marca", "co": "conversión comercial", "cx": "experiencia del cliente"}

        if max_v - min_v >= 20:
            # Ir al sub-indicador del frente más bajo para dar el insight real
            if min_f == "bx" and ba is not None and pulse is not None:
                causa = ("la presencia digital insuficiente" if pulse < ba - 15
                         else "la percepción de valor no diferenciada" if ba < 45
                         else "una combinación de señales mixtas entre activo y visibilidad")
                return (f"{nombre} muestra tensión entre {frente_names[max_f]} ({max_v:.0f}/100) "
                        f"y fuerza de marca ({min_v:.0f}/100). "
                        f"El análisis de componentes apunta a {causa} como origen: "
                        f"Brand Asset {ba:.0f}/100 y BAV Pulse {pulse:.0f}/100. "
                        f"Elevar BX no es una sola palanca — es un trabajo simultáneo "
                        f"de construcción de equity y visibilidad digital.")
            elif min_f == "cx" and loyalty is not None and cx_kpi is not None:
                causa = ("la base de usuarios fieles es pequeña" if loyalty < 35
                         else "los usuarios no perciben una experiencia significativamente mejor que las expectativas previas" if cx_kpi < 40
                         else "la experiencia no está siendo comunicada de forma que amplifique la preferencia")
                return (f"{nombre} tiene {frente_names[max_f]} sólida ({max_v:.0f}/100) "
                        f"pero la experiencia del cliente ({min_v:.0f}/100) limita el potencial de retención. "
                        f"La causa raíz: {causa} "
                        f"(lealtad {loyalty:.0f}/100 · CX Strategy {cx_kpi:.0f}/100). "
                        f"La inversión en CX debe atacar ese componente específico, "
                        f"no el frente de experiencia en general.")
            elif min_f == "co":
                return (f"{nombre} tiene {frente_names[max_f]} en {max_v:.0f}/100 "
                        f"pero su conversión comercial ({min_v:.0f}/100) limita la captura de valor. "
                        f"La eficiencia comercial — medida como retorno de ingresos sobre activos — "
                        f"está por debajo de lo que el perfil de marca justificaría. "
                        f"La pregunta estratégica no es 'qué comunicar' sino 'cómo convertir' "
                        f"el capital de marca existente en volumen de negocio.")

        # Perfil equilibrado sin brecha dominante: análisis de nivel absoluto
        avg_score = sum(v for _, v in scores_disp) / len(scores_disp)
        bx_s = f"{bx:.0f}" if bx is not None else "—"
        co_s = f"{co:.0f}" if co is not None else "—"
        cx_s = f"{cx:.0f}" if cx is not None else "—"
        if avg_score > 60:
            if pulse is not None and pulse < 55:
                palanca = f"presencia digital ({pulse:.0f}/100 en BAV Pulse) si la prioridad es captación"
            elif loyalty is not None and loyalty < 55:
                palanca = f"lealtad ({loyalty:.0f}/100) si la prioridad es retención"
            else:
                palanca = "diferenciación de la propuesta de valor para sostener la posición de liderazgo"
            return (f"{nombre} muestra un perfil equilibrado y por encima de la media "
                    f"(BX {bx_s} · CO {co_s} · CX {cx_s}/100). "
                    f"Sin una brecha dominante, la palanca de crecimiento está en "
                    f"profundizar el sub-indicador con mayor potencial según el contexto competitivo: "
                    f"{palanca}.")
        else:
            return (f"{nombre} tiene un perfil consistente pero con oportunidad de crecimiento en los tres frentes "
                    f"(BX {bx_s} · CO {co_s} · CX {cx_s}/100). "
                    f"La estrategia más efectiva en este perfil no es atacar el frente más bajo "
                    f"sino identificar cuál de los tres tiene mayor elasticidad al esfuerzo "
                    f"en el contexto competitivo de {sector}.")

    # ── PATRONES BX BAJO CON DIAGNÓSTICO DE SUB-INDICADORES ──────────────
    # Se evalúan al final para no bloquear patrones relativos (ej: CO alto + BX bajo)

    # BX bajo por invisibilidad digital (Brand Asset OK pero sin presencia digital)
    if bx_gap_origen == "digital_invisible" and bx is not None and bx < 50:
        return (f"{nombre} tiene un activo de marca sólido en percepción (Brand Asset {ba:.0f}/100) — "
                f"el mercado la reconoce y la estima — pero su presencia digital es baja ({pulse:.0f}/100 en BAV Pulse). "
                f"Esto significa que la marca existe en la mente del consumidor pero no donde "
                f"el consumidor busca: Google Trends, Wikipedia y redes sociales muestran "
                f"una presencia insuficiente para el tamaño de su reputación. "
                f"El riesgo: una marca que no existe digitalmente cede espacio a competidores "
                f"más pequeños pero más visibles en el momento de la búsqueda.")

    # BX bajo por falta de sustancia (alta presencia digital sin equity real)
    if bx_gap_origen == "digital_sin_sustancia" and bx is not None and bx < 50:
        return (f"{nombre} tiene presencia digital razonable ({pulse:.0f}/100 en BAV Pulse) "
                f"pero el Brand Asset ({ba:.0f}/100) muestra que esa visibilidad no se convierte "
                f"en percepción de valor. "
                f"El mercado ve la marca pero no la diferencia ni la prefiere. "
                f"El problema no es el volumen de comunicación sino su contenido: "
                f"la marca comunica pero no posiciona. La prioridad es construir "
                f"diferenciación real antes de invertir más en medios.")

    # BX doble debilidad (bajo en brand asset Y en digital)
    if bx_gap_origen == "bx_doble_debilidad" and bx is not None and bx < 40:
        return (f"{nombre} registra debilidad en los dos componentes del BX: "
                f"Brand Asset {ba:.0f}/100 (percepción de valor) y BAV Pulse {pulse:.0f}/100 (presencia digital). "
                f"No hay una base desde la cual palancarse: la marca no está construida "
                f"ni está siendo buscada. "
                f"El punto de partida es la identidad — qué hace diferente a {nombre} "
                f"y por qué debería importarle al consumidor — antes de cualquier inversión en medios.")

    # BX muy bajo sin datos de sub-indicadores
    if bx is not None and bx < 25:
        return (f"Con BX {bx:.0f}/100, {nombre} aún no ha construido la presencia "
                f"que le permita competir de igual a igual en {sector}. "
                f"Sin reconocimiento ni diferenciación clara, cualquier inversión en conversión "
                f"o experiencia opera sobre una base inestable.")

    return (f"{nombre} presenta un perfil en construcción en {sector}. "
            f"El primer paso es establecer cuál de los tres frentes — marca, ventas o experiencia — "
            f"tiene la mayor palanca de crecimiento dado el contexto competitivo actual.")

def generate_bx_analysis(b: dict, avg: dict) -> str:
    nombre = b["marca"]
    bx = safe_val(b.get("bx"))
    ba = safe_val(b.get("brand_asset"))
    pulse = safe_val(b.get("bav_pulse"))
    avg_bx = avg.get("bx")

    if bx is None:
        return "No hay dato de BX disponible para esta marca."

    gap = round(bx - avg_bx, 1) if avg_bx is not None else None
    sl = _score_label(bx)

    parts = [f"Fuerza de marca {sl} ({bx}/100)."]
    if gap is not None:
        parts.append(_gap_label(gap) + ".")
    if ba is not None:
        if ba > 75:
            parts.append(f"El activo de marca ({ba}/100) es sólido — el mercado reconoce la marca y la diferencia de la competencia.")
        elif ba > 40:
            parts.append(f"El activo de marca ({ba}/100) está en construcción — hay reconocimiento pero la diferenciación aún no es clara.")
        else:
            parts.append(f"El activo de marca es débil ({ba}/100) — la marca no se percibe como diferente ni preferida.")
    if pulse is not None:
        if pulse > 65:
            parts.append(f"Presencia digital alta ({pulse}/100): el sector ve a {nombre} en medios digitales.")
        elif pulse > 35:
            parts.append(f"Presencia digital media ({pulse}/100): visible pero no dominante en canales digitales.")
        else:
            parts.append(f"Presencia digital baja ({pulse}/100): el sector no encuentra fácilmente a {nombre} en digital.")
    return " ".join(parts)

def generate_co_analysis(b: dict, avg: dict) -> str:
    nombre = b["marca"]
    co = safe_val(b.get("co"))
    commerce = safe_val(b.get("commerce"))
    avg_co = avg.get("co")

    if co is None:
        return "No hay dato de CO disponible para esta marca."

    gap = round(co - avg_co, 1) if avg_co is not None else None
    sl = _score_label(co)

    parts = [f"Conversión comercial {sl} ({co}/100)."]
    if gap is not None:
        parts.append(_gap_label(gap) + ".")
    if co < 30:
        parts.append(f"Por cada $100 que el sector genera, {nombre} captura significativamente menos. Hay demanda que se escapa antes de convertirse en venta.")
    elif co > 70:
        parts.append(f"{nombre} convierte eficientemente — los consumidores que llegan al punto de compra, compran.")
    else:
        parts.append(f"La eficiencia comercial es media. Hay oportunidades de mejora en el proceso de conversión y en la propuesta de valor en punto de venta.")
    return " ".join(parts)

def generate_cx_analysis(b: dict, avg: dict) -> str:
    nombre = b["marca"]
    cx = safe_val(b.get("cx"))
    cx_kpi = safe_val(b.get("cx_kpi"))
    loyalty = safe_val(b.get("loyalty"))
    avg_cx = avg.get("cx")

    if cx is None:
        return "No hay dato de CX disponible para esta marca."

    gap = round(cx - avg_cx, 1) if avg_cx is not None else None
    sl = _score_label(cx)

    parts = [f"Experiencia del cliente {sl} ({cx}/100)."]
    if gap is not None:
        parts.append(_gap_label(gap) + ".")
    if cx_kpi is not None:
        if cx_kpi < 20:
            parts.append(f"La experiencia en punto de contacto es crítica ({cx_kpi}/100): los clientes salen del proceso con fricciones no resueltas.")
        elif cx_kpi > 70:
            parts.append(f"Los puntos de contacto generan buena experiencia ({cx_kpi}/100).")
    if loyalty is not None:
        if loyalty < 20:
            parts.append(f"La lealtad es muy baja ({loyalty}/100): menos de 20 de cada 100 clientes repiten o recomiendan activamente la marca.")
        elif loyalty > 70:
            parts.append(f"Alta lealtad ({loyalty}/100): los clientes vuelven y recomiendan — el activo más valioso que tiene la marca.")
        else:
            parts.append(f"Lealtad media ({loyalty}/100): hay clientes recurrentes pero el potencial de recomendación activa no se está aprovechando.")
    return " ".join(parts)

def generate_movements(b: dict, avg: dict, sector_brands: list) -> list:
    """
    Genera 3 movimientos estratégicos priorizados por impacto real.
    Orden: brecha más crítica → segunda brecha → consolidación del mejor frente.
    """
    nombre = b["marca"]
    fields_map = {
        "cx": ("cx_kpi", "loyalty"),
        "co": ("commerce",),
        "bx": ("brand_asset", "bav_pulse"),
    }

    gaps = {}
    for f in ["bx", "co", "cx"]:
        v = safe_val(b.get(f))
        a = avg.get(f)
        if v is not None and a is not None:
            gaps[f] = round(v - a, 1)

    # Ordenar por brecha (de más negativo a más positivo)
    sorted_gaps = sorted(gaps.items(), key=lambda x: x[1])

    movements = []

    timing = ["90 días", "3 a 9 meses", "9 a 18 meses"]
    for idx, (frente, gap) in enumerate(sorted_gaps[:3]):
        v = safe_val(b.get(frente))
        a = avg.get(frente)
        rank_pos, rank_total = rank_in_sector(nombre, frente, sector_brands)

        if frente == "cx":
            cx_kpi = safe_val(b.get("cx_kpi"))
            loyalty = safe_val(b.get("loyalty"))
            if v is not None and v < 30:
                title = "Resolver las fricciones críticas de la experiencia"
                body = (f"Con CX en {v}/100 ({gap:+.0f} vs sector), el primer movimiento es identificar "
                        f"y eliminar los 3 principales puntos de abandono en el recorrido del cliente. "
                        f"No se puede construir lealtad sobre una experiencia rota.")
                meta = f"Meta: CX de {v:.0f} → {min(v+20, 60):.0f} en 12 meses"
            elif gap < -10:
                title = "Cerrar la brecha de experiencia con el sector"
                body = (f"El sector promedia {a:.0f} en CX; {nombre} está en {v:.0f}. "
                        f"Identificar las prácticas de los 2-3 competidores mejor rankeados "
                        f"e implementar los cambios de mayor impacto en el corto plazo.")
                meta = f"Meta: llegar al promedio del sector ({a:.0f}) en 18 meses"
            else:
                title = "Profundizar la ventaja de experiencia"
                body = (f"Con CX por encima del sector ({gap:+.0f} pts), el movimiento es "
                        f"convertir esa experiencia en un diferenciador activo en la comunicación. "
                        f"Los clientes que viven buenas experiencias deben poder compartirlas.")
                loyalty_str = f"{loyalty:.0f}" if loyalty is not None else "N/D"
                meta = f"Meta: aumentar lealtad de {loyalty_str} → {min((loyalty or 0)+15, 95):.0f}/100"

        elif frente == "co":
            if v is not None and v < 30:
                title = "Activar la demanda reprimida con incentivos de conversión"
                body = (f"La marca genera interés pero CO en {v:.0f}/100 indica que ese interés no llega "
                        f"a la compra. Revisar la propuesta en punto de venta, la facilidad de pago "
                        f"y los catalizadores de decisión más frecuentes del consumidor.")
                meta = f"Meta: CO de {v:.0f} → {min(v+15, 75):.0f} en 12 meses"
            elif gap < -10:
                title = "Reducir la brecha comercial con el sector"
                body = (f"El sector convierte a {a:.0f}/100; {nombre} a {v:.0f}/100. "
                        f"Analizar el funnel completo desde la intención hasta la transacción "
                        f"e identificar dónde se pierden más clientes potenciales.")
                meta = f"Meta: alcanzar promedio del sector ({a:.0f}) en CO"
            else:
                title = "Capitalizar la fortaleza comercial en canales de mayor margen"
                body = (f"Con CO {gap:+.0f} sobre el sector, el movimiento es redirigir "
                        f"ese volumen hacia los productos o servicios con mejor margen. "
                        f"Volumen sin rentabilidad es crecimiento sin destino.")
                meta = f"Meta: mantener CO >{a:.0f} mejorando mix de producto"

        else:  # bx
            ba = safe_val(b.get("brand_asset"))
            pulse = safe_val(b.get("bav_pulse"))
            if v is not None and v < 25:
                title = "Construir presencia y reconocimiento de marca desde cero"
                body = (f"BX en {v:.0f}/100 indica que la marca aún no es reconocida ni diferenciada "
                        f"por la mayoría del mercado. El foco debe ser visibilidad básica: "
                        f"presencia constante en los canales donde vive la audiencia objetivo.")
                meta = f"Meta: BX de {v:.0f} → {min(v+20, 55):.0f} en 18 meses"
            elif gap < -10:
                title = "Fortalecer los atributos de diferenciación de marca"
                body = (f"El sector promedia {a:.0f} en BX; {nombre} está en {v:.0f}. "
                        f"Clarificar qué hace única a la marca y comunicarlo con consistencia "
                        f"es lo que convierte reconocimiento en preferencia.")
                meta = f"Meta: cerrar brecha de {abs(gap):.0f} pts con el sector en 18 meses"
            else:
                title = "Monetizar el capital de marca acumulado"
                body = (f"Con BX {gap:+.0f} sobre el sector, {nombre} tiene reputación que no está "
                        f"siendo totalmente aprovechada. Extensiones, ediciones especiales o "
                        f"alianzas estratégicas pueden capitalizar ese activo.")
                meta = f"Meta: mantener BX >{a:.0f} expandiendo presencia"

        movements.append({
            "num": f"0{idx+1}",
            "timing": timing[idx],
            "title": title,
            "body": body,
            "meta": meta,
            "frente": frente.upper(),
            "gap": gap,
        })

    return movements

def generate_frente_descriptions(b: dict, avg: dict, sem: dict, sector: str, sector_brands: list) -> dict:
    """
    Genera descripciones personalizadas para cada frente (Slide 3).
    Cada texto incluye el score real, el gap vs sector y una conclusión específica.
    """
    nombre = b["marca"]
    bx = safe_val(b.get("bx")); co = safe_val(b.get("co")); cx = safe_val(b.get("cx"))
    ba = safe_val(b.get("brand_asset")); pulse = safe_val(b.get("bav_pulse"))
    loyalty = safe_val(b.get("loyalty")); cx_kpi = safe_val(b.get("cx_kpi"))
    avg_bx = avg.get("bx"); avg_co = avg.get("co"); avg_cx = avg.get("cx")
    n = len([s for s in sector_brands if s["marca"] != nombre])

    bx_gap = round(bx - avg_bx, 1) if (bx is not None and avg_bx is not None) else None
    co_gap = round(co - avg_co, 1) if (co is not None and avg_co is not None) else None
    cx_gap = round(cx - avg_cx, 1) if (cx is not None and avg_cx is not None) else None

    bx_rank, bx_tot = rank_in_sector(nombre, "bx", sector_brands)
    co_rank, co_tot = rank_in_sector(nombre, "co", sector_brands)
    cx_rank, cx_tot = rank_in_sector(nombre, "cx", sector_brands)

    # ── BX ──
    if bx is None:
        bx_desc = f"No hay dato de Fuerza de Marca disponible para {nombre}."
    else:
        bx_rank_txt = f"posición {bx_rank} de {bx_tot}" if bx_rank else "sin ranking"
        bx_gap_txt = f"{bx_gap:+.0f} vs el sector" if bx_gap is not None else "sin comparativa"
        if sem.get("bx") == "verde":
            bx_desc = (f"{nombre} está en {bx}/100 en BX — {bx_rank_txt} en {sector} ({bx_gap_txt}). "
                      f"La marca es reconocida y diferenciada. "
                      f"{'El activo de marca en ' + str(ba) + '/100 confirma que el mercado la valora como preferencia.' if ba and ba > 60 else 'El reto es monetizar ese reconocimiento en resultados comerciales.'}")
        elif sem.get("bx") == "amarillo":
            bx_desc = (f"{nombre} tiene una fuerza de marca media: {bx}/100 ({bx_rank_txt} en {sector}, {bx_gap_txt}). "
                      f"Hay reconocimiento, pero la diferenciación frente a los competidores directos aún no es definitiva. "
                      f"{'La presencia digital en ' + str(pulse) + '/100 es el puente para mejorar.' if pulse else 'Fortalecer la narrativa de marca es el paso siguiente.'}")
        else:
            bx_desc = (f"BX en {bx}/100 es una alerta: {nombre} está en {bx_rank_txt} del sector ({bx_gap_txt}). "
                      f"La marca no es suficientemente reconocida ni diferenciada para competir en igualdad de condiciones. "
                      f"Sin visibilidad no hay preferencia — y sin preferencia, los demás indicadores no mejoran solos.")

    # ── CO ──
    if co is None:
        co_desc = f"No hay dato de Commerce Score disponible para {nombre}."
    else:
        co_rank_txt = f"posición {co_rank} de {co_tot}" if co_rank else "sin ranking"
        co_gap_txt = f"{co_gap:+.0f} vs el sector" if co_gap is not None else "sin comparativa"
        if sem.get("co") == "verde":
            co_desc = (f"{nombre} convierte bien: CO {co}/100 ({co_rank_txt} en {sector}, {co_gap_txt}). "
                      f"El mercado no solo conoce la marca — la compra. "
                      f"{'La fortaleza está en mantener ese volumen y migrar a categorías de mayor margen.' if co > 75 else 'El desafío es crecer el volumen sin perder la eficiencia de conversión actual.'}")
        elif sem.get("co") == "amarillo":
            co_desc = (f"{nombre} convierte a {co}/100 en CO — {co_rank_txt} en {sector} ({co_gap_txt}). "
                      f"La eficiencia comercial es media: hay demanda pero una parte se escapa antes de convertirse en venta. "
                      f"{'Hay margen real para crecer cerrando las fugas en el funnel de compra.' if co_gap and co_gap > -15 else 'La brecha con el sector sugiere revisar el proceso de conversión en punto de venta.'}")
        else:
            co_desc = (f"CO en {co}/100 es una alerta crítica: {co_rank_txt} en {sector} ({co_gap_txt}). "
                      f"La marca genera interés pero casi no lo convierte en transacción. "
                      f"{'Dado el BX de ' + str(bx) + '/100, la demanda existe — el problema está en la conversión, no en el producto.' if bx and bx > 40 else 'El proceso desde el interés hasta la compra tiene fricciones que deben resolverse con prioridad.'}")

    # ── CX ──
    if cx is None:
        cx_desc = f"No hay dato de Experiencia del Cliente disponible para {nombre}."
    else:
        cx_rank_txt = f"posición {cx_rank} de {cx_tot}" if cx_rank else "sin ranking"
        cx_gap_txt = f"{cx_gap:+.0f} vs el sector" if cx_gap is not None else "sin comparativa"
        if sem.get("cx") == "verde":
            cx_desc = (f"{nombre} genera buena experiencia: CX {cx}/100 ({cx_rank_txt} en {sector}, {cx_gap_txt}). "
                      f"{'La lealtad de ' + str(loyalty) + '/100 confirma que los clientes no solo vienen — vuelven.' if loyalty and loyalty > 60 else 'El reto es convertir esa buena experiencia en lealtad activa y recomendación.'} "
                      f"{'El KPI de experiencia en ' + str(cx_kpi) + '/100 sostiene el puntaje general.' if cx_kpi and cx_kpi > 65 else ''}")
        elif sem.get("cx") == "amarillo":
            cx_desc = (f"{nombre} está en {cx}/100 en CX — {cx_rank_txt} en {sector} ({cx_gap_txt}). "
                      f"La experiencia es funcional pero no diferenciadora. "
                      f"{'La lealtad en ' + str(loyalty) + '/100 indica clientes recurrentes, pero el NPS potencial es mayor.' if loyalty else 'Identificar los momentos clave del recorrido del cliente permitiría mejorar este indicador con inversión focalizada.'}")
        else:
            cx_desc = (f"CX en {cx}/100 es el frente más urgente: {cx_rank_txt} en {sector} ({cx_gap_txt}). "
                      f"Los clientes salen con fricciones no resueltas y el riesgo de no retorno es alto. "
                      f"{'La lealtad de ' + str(loyalty) + '/100 confirma el impacto: menos de la mitad de los clientes vuelven activamente.' if loyalty and loyalty < 40 else 'Sin mejorar CX, las inversiones en marca y ventas generan clientes de una sola vez.'}")

    return {"bx": bx_desc, "co": co_desc, "cx": cx_desc}


def generate_comparative_insight(b: dict, avg: dict, gaps: dict) -> str:
    """
    Insight personalizado para Slide 4 (marca vs sector — todos los indicadores).
    Identifica el patrón más relevante en el perfil completo de la marca.
    """
    nombre = b["marca"]
    bx = safe_val(b.get("bx")); co = safe_val(b.get("co")); cx = safe_val(b.get("cx"))
    ba = safe_val(b.get("brand_asset")); pulse = safe_val(b.get("bav_pulse"))
    loyalty = safe_val(b.get("loyalty")); cx_kpi = safe_val(b.get("cx_kpi"))

    valid_gaps = {f: v for f, v in gaps.items() if v is not None and avg.get(f) is not None}
    if not valid_gaps:
        # Sin peers: análisis absoluto de la marca
        scores = [(f, safe_val(b.get(f))) for f in ["bx","co","cx"] if safe_val(b.get(f)) is not None]
        if scores:
            min_f, min_v = min(scores, key=lambda x: x[1])
            max_f, max_v = max(scores, key=lambda x: x[1])
            fn_abs = {"bx":"fuerza de marca","co":"conversión comercial","cx":"experiencia del cliente"}
            if max_v - min_v >= 20:
                return (f"{nombre} muestra una tensión interna clara: {fn_abs.get(max_f,'fortaleza')} "
                       f"en {max_v:.0f}/100 contrasta con {fn_abs.get(min_f,'debilidad')} en {min_v:.0f}/100. "
                       f"Sin referentes sectoriales directos, el benchmarking debe hacerse contra el mercado general. "
                       f"La prioridad interna es elevar el frente más bajo para tener un perfil coherente.")
        return f"{nombre} tiene un perfil único sin referentes directos. El análisis se basa en los scores absolutos del modelo BAV."

    best_f = max(valid_gaps, key=lambda f: valid_gaps[f])
    worst_f = min(valid_gaps, key=lambda f: valid_gaps[f])
    best_v = valid_gaps[best_f]
    worst_v = valid_gaps[worst_f]

    fn = {
        "bx": "la fuerza de marca", "co": "la conversión comercial",
        "cx": "la experiencia", "brand_asset": "el activo de marca",
        "bav_pulse": "la presencia digital", "commerce": "el volumen de ventas",
        "cx_kpi": "la experiencia en punto de contacto", "loyalty": "la lealtad"
    }
    score_actual = {
        "bx": bx, "co": co, "cx": cx, "brand_asset": ba,
        "bav_pulse": pulse, "loyalty": loyalty, "cx_kpi": cx_kpi
    }

    best_score = score_actual.get(best_f)
    worst_score = score_actual.get(worst_f)
    worst_avg = avg.get(worst_f)

    # Si hay un indicador claramente por encima del sector
    if best_v > 8 and worst_v < -8:
        return (f"{nombre} tiene un perfil asimétrico: {fn.get(best_f,'su mejor indicador')} supera al sector "
                f"({'+' + str(round(best_v)):>4} pts) mientras {fn.get(worst_f,'el indicador más débil')} "
                f"queda {abs(worst_v):.0f} pts por debajo. La tensión entre fortaleza y debilidad define la "
                f"estrategia: capitalizar lo que funciona mientras se corrige lo que frena el crecimiento.")
    elif worst_v < -15:
        ws_txt = f"{worst_score:.0f}" if worst_score is not None else "—"
        wa_txt = f"{worst_avg:.0f}" if worst_avg is not None else "—"
        return (f"La brecha más urgente de {nombre} está en {fn.get(worst_f,'el indicador clave')}: "
                f"{ws_txt}/100 contra {wa_txt}/100 del sector ({worst_v:.0f} pts). "
                f"Es el indicador con mayor potencial de impacto si se prioriza en los próximos 12 meses.")
    elif best_v > 15:
        return (f"{fn.get(best_f,'El mejor indicador').capitalize()} es la ventaja competitiva de {nombre} "
                f"vs el sector (+{best_v:.0f} pts). El trabajo es mantener esa ventaja mientras se "
                f"eleva el piso de los demás indicadores para que el perfil sea coherente.")
    elif all(v >= -8 for v in valid_gaps.values()):
        all_scores = [(fn.get(f,''), v) for f, v in valid_gaps.items()]
        return (f"{nombre} tiene un perfil equilibrado vs el sector — sin brechas críticas ni ventajas dominantes. "
                f"En mercados competitivos, equilibrio sin diferenciación es invisibilidad. "
                f"El movimiento es elegir un frente donde ser el mejor del sector, no el promedio.")
    else:
        ws_txt = f"{worst_score:.0f}" if worst_score is not None else "—"
        return (f"{nombre} muestra indicadores mixtos vs el sector. "
                f"El foco debe ir en {fn.get(worst_f,'el indicador más débil')} "
                f"({ws_txt}/100 · {worst_v:.0f} pts vs sector): "
                f"es donde una mejora moderada generaría el mayor salto en el perfil competitivo.")


def generate_strength_insight(b: dict, avg: dict, best_field: str, best_gap: float) -> str:
    """
    Insight personalizado para Slide 5 (la mayor fortaleza).
    """
    nombre = b["marca"]
    fn = {"bx":"Fuerza de Marca","co":"Commerce Score","cx":"Experiencia del Cliente",
          "brand_asset":"Activo de Marca","bav_pulse":"Presencia Digital"}
    field_name = fn.get(best_field, "indicador")
    score = safe_val(b.get(best_field))
    score_txt = f"{score:.0f}/100" if score else "—"
    loyalty = safe_val(b.get("loyalty"))
    avg_val = avg.get(best_field)

    # Sin peers sectoriales — análisis absoluto
    if avg_val is None:
        bx = safe_val(b.get("bx")); co = safe_val(b.get("co")); cx = safe_val(b.get("cx"))
        strongest = max([(f,v) for f,v in [("bx",bx),("co",co),("cx",cx)] if v is not None],
                       key=lambda x: x[1], default=(best_field, 0))
        sf_name = fn.get(strongest[0], "el indicador más fuerte")
        return (f"{nombre} no tiene referentes sectoriales directos, pero su perfil interno muestra fortaleza en {sf_name} "
               f"({strongest[1]:.0f}/100). El benchmarking debe realizarse contra el mercado general. "
               f"{'La lealtad de ' + str(loyalty) + '/100 indica que los clientes que llegan se quedan.' if loyalty and loyalty > 50 else ''} "
               f"El movimiento es convertir esas fortalezas absolutas en ventajas cuando el sector se amplíe.")

    if best_gap > 15:
        if best_field == "bav_pulse":
            return (f"{nombre} supera al sector en Presencia Digital (+{best_gap:.0f} pts). "
                   f"Esa visibilidad en medios digitales existe pero no está siendo aprovechada suficientemente "
                   f"para impulsar conversión comercial y experiencia. "
                   f"El activo digital debe conectarse con el funnel de ventas — es el paso inmediato.")
        elif best_field == "brand_asset":
            return (f"El Activo de Marca de {nombre} ({score_txt}) supera al sector en +{best_gap:.0f} pts. "
                   f"El mercado reconoce y diferencia la marca — eso es lo más difícil de construir y lo más fácil de no aprovechar. "
                   f"El reto inmediato es conectar ese capital de marca con resultados en ventas y experiencia.")
        elif best_field == "loyalty":
            return (f"La lealtad de {nombre} ({score_txt}) es la mayor ventaja relativa en el sector (+{best_gap:.0f} pts). "
                   f"Una base de clientes que vuelve es el activo más valioso — más barato que adquirir nuevos y más rentable que cualquier campaña. "
                   f"El movimiento es ampliar el embudo de captación sin diluir esa intensidad de relación.")
        else:
            return (f"{nombre} supera al sector en {field_name} con +{best_gap:.0f} pts. "
                   f"Esa ventaja existe pero sola no construye liderazgo — necesita traducirse en los frentes donde la marca está por debajo del sector. "
                   f"Una fortaleza sin palanca estratégica es una oportunidad desperdiciada.")
    elif best_gap > 0:
        return (f"{field_name} es donde {nombre} tiene su menor brecha negativa vs el sector (+{best_gap:.0f} pts). "
               f"No es una ventaja dominante, pero es el punto de partida más sólido para construir. "
               f"Concentrar comunicación y recursos en este frente primero, antes de dispersar esfuerzo.")
    else:
        return (f"{nombre} está por debajo del sector en todos los indicadores evaluados — la menor brecha es en {field_name} ({best_gap:.0f} pts). "
               f"En este escenario, el primer movimiento es elegir UN frente y concentrar el 80% del esfuerzo allí. "
               f"Mejorar todo a la vez en estas condiciones equivale a no mejorar nada.")


def generate_co_footer(b: dict, avg: dict, co_ranking: list, gaps: dict) -> str:
    """Footer personalizado para Slide 6 (CO ranking)."""
    nombre = b["marca"]
    co = safe_val(b.get("co"))
    avg_co = avg.get("co")
    co_gap = gaps.get("co")
    bx = safe_val(b.get("bx"))
    loyalty = safe_val(b.get("loyalty"))

    if co is None:
        return f"No hay datos de CO disponibles para {nombre}."

    top_co = sorted(co_ranking, key=lambda x: x["val"], reverse=True)[:2]
    bottom_co = sorted(co_ranking, key=lambda x: x["val"])[:1]
    other_tops = [d for d in top_co if d["name"] != nombre]
    leader_scores = " y ".join(f"{d['name']} ({d['val']:.0f}/100)" for d in other_tops)
    avg_co_str = f"{avg_co:.0f}" if avg_co is not None else "—"

    # Sin peers — análisis absoluto
    if avg_co is None:
        loyalty_context = f" La lealtad de {loyalty:.0f}/100 indica retención, pero el volumen de conversión ({co:.0f}/100) limita el crecimiento." if loyalty else ""
        if co < 15:
            bx_ctx = f" Con BX en {bx:.0f}/100, la demanda existe — el problema está en el modelo de captación y conversión." if bx and bx > 40 else ""
            return (f"{nombre} registra un CO de {co:.0f}/100 — la conversión comercial es el frente más crítico del perfil.{bx_ctx}{loyalty_context} "
                   f"Sin referentes sectoriales directos, el benchmark más útil es el mercado general.")
        return (f"{nombre} convierte a {co:.0f}/100 — sin referentes sectoriales directos para comparar.{loyalty_context} "
               f"El análisis de conversión debe hacerse contra el mercado general y los estándares de la categoría amplia.")

    if co_gap is not None and co_gap < -20:
        bx_context = f" Con BX en {bx:.0f}/100, la demanda existe — el problema está en la conversión, no en la marca." if bx and bx > 40 else ""
        leader_txt = f"{leader_scores} lideran la conversión en el sector. " if leader_scores else ""
        return (f"{leader_txt}{nombre} está {abs(co_gap):.0f} pts por debajo del promedio ({avg_co_str}/100).{bx_context} "
               f"La brecha es recuperable con una revisión del funnel de compra y los catalizadores de decisión en punto de venta.")
    elif co_gap is not None and co_gap > 10:
        bottom_txt = (f" Comparado con {bottom_co[0]['name']} ({bottom_co[0]['val']:.0f}/100 CO), la ventaja competitiva es real."
                     if bottom_co and bottom_co[0]["name"] != nombre else "")
        return (f"{nombre} convierte por encima del promedio del sector (+{co_gap:.0f} pts sobre {avg_co_str}/100). "
               f"El volumen está — el siguiente movimiento es redirigirlo hacia los productos o servicios de mayor margen.{bottom_txt}")
    else:
        leaders_txt = f"{leader_scores} demuestran que el sector puede llegar a niveles más altos. " if leader_scores else ""
        return (f"{nombre} convierte a {co:.0f}/100 — cerca del promedio del sector ({avg_co_str}/100). "
               f"{leaders_txt}La pregunta es qué hace diferente a esas marcas en el momento de la compra.")


def generate_cx_footer(b: dict, avg: dict, cx_ranking: list, gaps: dict) -> str:
    """Footer personalizado para Slide 7 (CX ranking)."""
    nombre = b["marca"]
    cx = safe_val(b.get("cx"))
    avg_cx = avg.get("cx")
    cx_gap = gaps.get("cx")
    loyalty = safe_val(b.get("loyalty"))
    cx_kpi = safe_val(b.get("cx_kpi"))
    top_cx = sorted(cx_ranking, key=lambda x: x["val"], reverse=True)[:1]

    if cx is None:
        return f"No hay datos de CX disponibles para {nombre}."

    top_name = top_cx[0]["name"] if top_cx else "—"
    top_val = top_cx[0]["val"] if top_cx else 0
    avg_cx_str = f"{avg_cx:.0f}" if avg_cx is not None else "—"
    loyalty_txt = ""
    if loyalty is not None:
        loyalty_txt = f" La lealtad de {loyalty:.0f}/100 {'respalda la experiencia positiva' if loyalty > 60 else 'refleja el impacto de las fricciones en la recurrencia'}."

    # Sin peers — análisis absoluto
    if avg_cx is None:
        return (f"{nombre} registra CX de {cx:.0f}/100 — sin referentes directos en su sector. "
               f"{'El KPI de experiencia en ' + str(cx_kpi) + '/100 detalla la calidad en puntos de contacto.' if cx_kpi else ''}"
               f"{loyalty_txt} "
               f"El benchmark más relevante es el promedio del mercado general.")

    if cx_gap is not None and cx_gap < -15:
        return (f"El promedio del sector está en {avg_cx_str}/100 en CX; {nombre} registra {cx:.0f}/100 ({cx_gap:.0f} pts)."
               f"{loyalty_txt} "
               f"{top_name} ({top_val:.0f}/100) demuestra que el sector puede generar experiencias significativamente mejores. "
               f"Identificar qué hace diferente ese recorrido del cliente es el primer paso para cerrar la brecha.")
    elif cx_gap is not None and cx_gap > 10:
        return (f"{nombre} supera al sector en CX (+{cx_gap:.0f} pts sobre el promedio de {avg_cx_str}/100).{loyalty_txt} "
               f"Esa ventaja experiencial debe comunicarse activamente — los clientes que viven buenas experiencias deben poder compartirlas.")
    else:
        return (f"El promedio del sector en CX es {avg_cx_str}/100; {nombre} está en {cx:.0f}/100.{loyalty_txt} "
               f"{top_name} ({top_val:.0f}/100) es el referente de experiencia del sector. "
               f"Identificar qué hace diferente su recorrido del cliente es el primer paso para cerrar la brecha.")


def generate_next_steps(b: dict, avg: dict, movements: list) -> list:
    nombre = b["marca"]
    steps = []

    # Frente crítico real + su score y gap vs sector
    top_frente = movements[0]["frente"] if movements else "CX"
    fmap = {"CX": "cx", "CO": "co", "BX": "bx"}
    fname = {"CX": "Experiencia del Cliente", "CO": "Commerce", "BX": "Fuerza de Marca"}
    field = fmap.get(top_frente, "cx")
    score_crit = safe_val(b.get(field))
    avg_crit = avg.get(field)
    gap_crit = round(score_crit - avg_crit, 1) if (score_crit is not None and avg_crit is not None) else None
    score_txt = f"{score_crit:.0f}/100" if score_crit is not None else "sin dato"
    gap_txt = f" ({gap_crit:+.0f} vs sector)" if gap_crit is not None else ""

    # Paso 1: dueño del frente crítico — con la cifra que lo justifica
    steps.append({
        "accion": (f"Asignar un líder con autoridad de decisión sobre {top_frente} "
                   f"({fname.get(top_frente, top_frente)}: {score_txt}{gap_txt}) — "
                   f"el frente con mayor potencial de impacto para {nombre}"),
        "resp": "CEO / Dirección General",
        "cuando": "Esta semana",
        "urgencia": "rojo",
    })

    # Paso 2: basado en el movimiento 1 — con dato concreto
    if movements:
        m = movements[0]
        frente = m["frente"]
        if frente == "CX":
            cxk = safe_val(b.get("cx_kpi")); ly = safe_val(b.get("loyalty"))
            detalle = (f"CX Strategy {cxk:.0f} · lealtad {ly:.0f}/100 — empezar por el momento de mayor caída"
                       if cxk is not None and ly is not None else "con datos de queja o abandono reales")
            steps.append({
                "accion": f"Mapear el recorrido del cliente e identificar los 3 momentos de mayor fricción ({detalle})",
                "resp": "Customer Experience + Operaciones",
                "cuando": "Próximas 3 semanas",
                "urgencia": "rojo",
            })
        elif frente == "CO":
            cm = safe_val(b.get("commerce"))
            detalle = (f"Commerce en {cm:.0f}/100: revisar dónde se pierde la intención antes de la compra"
                       if cm is not None else "identificar dónde se rompe el funnel")
            steps.append({
                "accion": f"Auditar el funnel de conversión desde el primer contacto hasta la transacción ({detalle})",
                "resp": "Comercial + Marketing",
                "cuando": "Próximas 3 semanas",
                "urgencia": "rojo",
            })
        else:
            ba = safe_val(b.get("brand_asset")); pulse = safe_val(b.get("bav_pulse"))
            detalle = (f"Brand Asset {ba:.0f} · BAV Pulse {pulse:.0f}/100: atacar el componente más bajo primero"
                       if ba is not None and pulse is not None else "consistencia en todos los canales")
            steps.append({
                "accion": f"Definir los 2-3 atributos de diferenciación de marca y comunicarlos de forma consistente ({detalle})",
                "resp": "Marketing + Marca",
                "cuando": "Próximas 3 semanas",
                "urgencia": "rojo",
            })

    # Paso 3: basado en movimiento 2
    if len(movements) > 1:
        m2 = movements[1]
        steps.append({
            "accion": f"Diseñar el plan de acción para el frente {m2['frente']}: objetivo, responsable y métricas de seguimiento mensual",
            "resp": "Dirección Comercial / Marketing",
            "cuando": "Próximas 2 semanas",
            "urgencia": "amarillo",
        })

    # Paso 4: métricas
    steps.append({
        "accion": f"Establecer dashboard de seguimiento mensual con BX, CO y CX para {nombre} — incluir benchmarks del sector",
        "resp": "Dirección General + Analítica",
        "cuando": "Próximo mes",
        "urgencia": "amarillo",
    })

    # Paso 5: revisión de resultados
    steps.append({
        "accion": "Programar revisión de resultados a 90 días con el equipo directivo para validar progreso y ajustar prioridades",
        "resp": "Dirección General",
        "cuando": "En 90 días",
        "urgencia": "verde",
    })

    return steps[:5]

# ═══════════════════════════════════════════════════════════
# PUNTO DE ENTRADA: ANÁLISIS COMPLETO DE MARCA
# ═══════════════════════════════════════════════════════════

def analyze_brand(nombre: str) -> dict:
    """
    Retorna el análisis completo de una marca.
    Anti-hallucination: solo usa datos verificados de RAW_BRANDS.
    """
    # 1. Validar existencia
    b = validate_brand(nombre)

    # 2. Clasificar sector
    sector = get_category(nombre)
    sector_brands = get_sector_brands(nombre)

    # 3. Calcular promedios del sector (sin la marca analizada)
    avg = compute_sector_avg(sector_brands, nombre)

    # 4. Validar y limpiar datos de la marca
    validated = {
        "marca": b["marca"],
        "sector": sector,
        "n_sector": len(sector_brands),
        "bx":          safe_val(b.get("bx")),
        "co":          safe_val(b.get("co")),
        "cx":          safe_val(b.get("cx")),
        "brand_asset": safe_val(b.get("brand_asset")),
        "bav_pulse":   safe_val(b.get("bav_pulse")),
        "commerce":    safe_val(b.get("commerce")),
        "cx_kpi":      safe_val(b.get("cx_kpi")),
        "loyalty":     safe_val(b.get("loyalty")),
    }

    # 5. Gaps vs sector
    gaps = {}
    for f in ["bx","co","cx","brand_asset","bav_pulse","commerce","cx_kpi","loyalty"]:
        v = validated.get(f)
        a = avg.get(f)
        gaps[f] = round(v - a, 1) if (v is not None and a is not None) else None

    # 6. Rankings en sector
    rankings = {}
    for f in ["bx","co","cx","loyalty","brand_asset","bav_pulse"]:
        pos, tot = rank_in_sector(nombre, f, sector_brands)
        rankings[f] = {"pos": pos, "total": tot}

    # 7. Semáforos
    semaphores = {f: semaphore(validated.get(f)) for f in ["bx","co","cx"]}

    # 8. Rankings de sector (CO / CX) — deben calcularse antes de la narrativa
    scatter = []
    for sb in sector_brands:
        bx_s = safe_val(sb.get("bx"))
        cx_s = safe_val(sb.get("cx"))
        if bx_s is not None and cx_s is not None:
            scatter.append({"name": sb["marca"], "bx": bx_s, "cx": cx_s})

    co_ranking = []
    for sb in sector_brands:
        co_s = safe_val(sb.get("co"))
        if co_s is not None:
            co_ranking.append({"name": sb["marca"], "val": co_s})
    co_ranking.sort(key=lambda x: x["val"])

    cx_ranking = []
    for sb in sector_brands:
        cx_s = safe_val(sb.get("cx"))
        if cx_s is not None:
            cx_ranking.append({"name": sb["marca"], "val": cx_s})
    cx_ranking.sort(key=lambda x: x["val"])

    # 9. Narrativa EPIC personalizada
    dominant_idea    = generate_dominant_idea(b, avg, sector)
    bx_analysis      = generate_bx_analysis(b, avg)
    co_analysis      = generate_co_analysis(b, avg)
    cx_analysis      = generate_cx_analysis(b, avg)
    movements        = generate_movements(b, avg, sector_brands)
    next_steps       = generate_next_steps(b, avg, movements)
    frente_descs     = generate_frente_descriptions(b, avg, semaphores, sector, sector_brands)
    comparative_ins  = generate_comparative_insight(b, avg, gaps)
    co_footer        = generate_co_footer(b, avg, co_ranking, gaps)
    cx_footer        = generate_cx_footer(b, avg, cx_ranking, gaps)

    # Best field for slide 5
    _gap_candidates = {f: gaps[f] for f in ["bx","co","cx","brand_asset","bav_pulse"] if gaps.get(f) is not None}
    _best_f = max(_gap_candidates, key=lambda f: _gap_candidates[f]) if _gap_candidates else "bav_pulse"
    _best_g = _gap_candidates.get(_best_f, 0)
    strength_ins     = generate_strength_insight(b, avg, _best_f, _best_g)

    return {
        "brand": validated,
        "sector_avg": avg,
        "gaps": gaps,
        "rankings": rankings,
        "semaphores": semaphores,
        "dominant_idea": dominant_idea,
        "bx_analysis": bx_analysis,
        "co_analysis": co_analysis,
        "cx_analysis": cx_analysis,
        "frente_descs": frente_descs,
        "comparative_insight": comparative_ins,
        "strength_insight": strength_ins,
        "strength_field": _best_f,
        "strength_gap": _best_g,
        "co_footer": co_footer,
        "cx_footer": cx_footer,
        "movements": movements,
        "next_steps": next_steps,
        "scatter": scatter,
        "co_ranking": co_ranking,
        "cx_ranking": cx_ranking,
        "sector_brands": [sb["marca"] for sb in sector_brands],
    }
