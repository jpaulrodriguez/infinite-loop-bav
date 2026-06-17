"""
Total Search FINAL — integra GT + Wiki + BAV + Social
Formula: GT×0.35 + Wiki×0.15 + BAV-R×0.10 + BAV-D×0.10 + Social×0.30
(Si social_scores.json no existe, cae al original sin social)
"""
import json, os

GT = {
  "D1":48.4,"Ara":87.0,"Exito":3.1,"Olímpica":13.8,"OXXO":100,
  "Makro":29.7,"Cencosud":83.4,"Falabella":100,"Movistar":4.3,
  "Avianca":57.8,"Arturo Calle":4.5,"Postobón":0.5,"Aguila":52.1,
  "Renault":100,"Hyundai":100,"Toyota":100,"Mazda":100,"Chevrolet":100,
  "Rappi":100,"Sura":100,"Seguros Bolivar":100,"Terpel":100,"Primax":85.3,
  "Biomax":0.0,"Farmatodo":100,"Cruz Verde":100,"Frisby":7.6,
  "Decameron":100,"H&M":100,"Tigo":100,"Tigo UNE":100,"WOM":100,
  "McDonald's":100,"Coca-Cola":61.0,"Poker":100,"Club Colombia":74.1,
  "Corona":0.9,"Tennis":0.4,"Zapatoca":14.2,"Nissan":100,
  "Grupo Aval":28.5,"Petrobras":3.6,"Suzuki":100,"Colpatria":100,
  "American Airlines":100,"United Airlines":35.7,
}

WIKI = {
  "Coca-Cola":100,"McDonald's":95,"Toyota":90,"H&M":85,"Chevrolet":85,
  "Renault":80,"Hyundai":80,"Nissan":80,"Mazda":75,"Suzuki":75,
  "Corona":70,"Avianca":65,"American Airlines":65,"United Airlines":60,
  "Falabella":55,"Cencosud":55,"Movistar":55,"Makro":50,"OXXO":50,
  "Rappi":50,"Grupo Aval":45,"Petrobras":45,"Tigo":40,"Sura":40,
  "Terpel":40,"Exito":35,"Olímpica":35,"D1":15,"Ara":15,
  "Arturo Calle":15,"Postobón":30,"Aguila":25,"Club Colombia":25,
  "Frisby":15,"Farmatodo":20,"Cruz Verde":15,"Decameron":20,
  "Tigo UNE":20,"WOM":20,"Tennis":10,"Zapatoca":10,
  "Seguros Bolivar":20,"Primax":20,"Biomax":15,"Colpatria":20,
  "Poker":15,
}

BAV = {
  "D1":{"D":77.4,"R":99.0,"E":89.0,"K":95.0,"CX":92.0,"loop":90.5},
  "Ara":{"D":90.8,"R":92.8,"E":88.0,"K":90.0,"CX":89.0,"loop":90.1},
  "Exito":{"D":47.5,"R":85.4,"E":72.0,"K":88.0,"CX":80.0,"loop":74.6},
  "Olímpica":{"D":41.6,"R":84.0,"E":68.0,"K":85.0,"CX":76.5,"loop":71.0},
  "OXXO":{"D":79.8,"R":62.8,"E":60.0,"K":72.0,"CX":66.0,"loop":68.1},
  "Makro":{"D":28.1,"R":74.3,"E":55.0,"K":70.0,"CX":62.5,"loop":58.0},
  "Cencosud":{"D":21.1,"R":41.4,"E":35.0,"K":45.0,"CX":40.0,"loop":36.5},
  "Falabella":{"D":95.1,"R":83.9,"E":85.0,"K":88.0,"CX":86.5,"loop":87.7},
  "Movistar":{"D":30.6,"R":51.9,"E":45.0,"K":55.0,"CX":50.0,"loop":46.5},
  "Avianca":{"D":39.6,"R":70.3,"E":60.0,"K":75.0,"CX":67.5,"loop":62.5},
  "Arturo Calle":{"D":86.5,"R":72.8,"E":80.0,"K":70.0,"CX":75.0,"loop":76.9},
  "Postobón":{"D":77.8,"R":76.5,"E":78.0,"K":80.0,"CX":79.0,"loop":78.3},
  "Aguila":{"D":70.5,"R":54.6,"E":65.0,"K":60.0,"CX":62.5,"loop":62.5},
  "Renault":{"D":67.0,"R":81.9,"E":75.0,"K":82.0,"CX":78.5,"loop":76.9},
  "Hyundai":{"D":71.1,"R":59.8,"E":65.0,"K":65.0,"CX":65.0,"loop":65.2},
  "Toyota":{"D":92.7,"R":85.3,"E":90.0,"K":88.0,"CX":89.0,"loop":89.0},
  "Mazda":{"D":84.9,"R":70.5,"E":78.0,"K":72.0,"CX":75.0,"loop":75.7},
  "Chevrolet":{"D":25.0,"R":75.5,"E":60.0,"K":78.0,"CX":69.0,"loop":61.5},
  "Rappi":{"D":93.8,"R":78.3,"E":82.0,"K":80.0,"CX":81.0,"loop":83.0},
  "Sura":{"D":60.0,"R":83.8,"E":72.0,"K":80.0,"CX":76.0,"loop":74.4},
  "Seguros Bolivar":{"D":10.5,"R":52.8,"E":40.0,"K":55.0,"CX":47.5,"loop":41.2},
  "Terpel":{"D":50.7,"R":70.7,"E":62.0,"K":72.0,"CX":67.0,"loop":64.5},
  "Primax":{"D":7.2,"R":37.5,"E":28.0,"K":40.0,"CX":34.0,"loop":29.3},
  "Biomax":{"D":15.5,"R":32.5,"E":25.0,"K":35.0,"CX":30.0,"loop":27.6},
  "Farmatodo":{"D":53.0,"R":87.2,"E":75.0,"K":85.0,"CX":80.0,"loop":76.0},
  "Cruz Verde":{"D":44.4,"R":84.1,"E":70.0,"K":82.0,"CX":76.0,"loop":71.3},
  "Frisby":{"D":97.3,"R":95.2,"E":92.0,"K":90.0,"CX":91.0,"loop":93.1},
  "Decameron":{"D":71.5,"R":69.5,"E":70.0,"K":72.0,"CX":71.0,"loop":70.8},
  "H&M":{"D":82.5,"R":67.4,"E":72.0,"K":68.0,"CX":70.0,"loop":72.0},
  "Tigo":{"D":32.0,"R":44.3,"E":38.0,"K":48.0,"CX":43.0,"loop":41.1},
  "Tigo UNE":{"D":38.2,"R":37.3,"E":35.0,"K":42.0,"CX":38.5,"loop":38.2},
  "WOM":{"D":37.4,"R":11.5,"E":22.0,"K":18.0,"CX":20.0,"loop":21.8},
  "McDonald's":{"D":75.1,"R":55.2,"E":65.0,"K":60.0,"CX":62.5,"loop":63.6},
  "Coca-Cola":{"D":96.3,"R":71.9,"E":88.0,"K":78.0,"CX":83.0,"loop":83.4},
  "Poker":{"D":39.5,"R":21.7,"E":32.0,"K":28.0,"CX":30.0,"loop":30.2},
  "Club Colombia":{"D":77.0,"R":80.7,"E":78.0,"K":80.0,"CX":79.0,"loop":78.9},
  "Corona":{"D":90.4,"R":71.4,"E":80.0,"K":72.0,"CX":76.0,"loop":77.9},
  "Tennis":{"D":74.7,"R":58.0,"E":65.0,"K":60.0,"CX":62.5,"loop":64.0},
  "Zapatoca":{"D":46.8,"R":31.7,"E":38.0,"K":35.0,"CX":36.5,"loop":37.6},
  "Nissan":{"D":92.8,"R":66.4,"E":75.0,"K":68.0,"CX":71.5,"loop":74.7},
  "Grupo Aval":{"D":21.0,"R":19.1,"E":22.0,"K":25.0,"CX":23.5,"loop":22.1},
  "Petrobras":{"D":8.4,"R":20.2,"E":15.0,"K":22.0,"CX":18.5,"loop":16.8},
  "Suzuki":{"D":83.6,"R":71.5,"E":76.0,"K":72.0,"CX":74.0,"loop":75.0},
  "Colpatria":{"D":4.1,"R":24.0,"E":18.0,"K":26.0,"CX":22.0,"loop":18.8},
  "American Airlines":{"D":22.2,"R":36.8,"E":30.0,"K":40.0,"CX":35.0,"loop":32.8},
  "United Airlines":{"D":41.1,"R":36.9,"E":38.0,"K":42.0,"CX":40.0,"loop":39.6},
}

# Load social scores if available
SOCIAL = {}
if os.path.exists("social_scores.json"):
    with open("social_scores.json") as f:
        raw = json.load(f)
    SOCIAL = {k: v["social_score"] for k,v in raw.items()}
    print(f"✓ Cargados social scores para {len(SOCIAL)} marcas")
else:
    print("⚠ social_scores.json no encontrado, usando 0 para social")

def ts_score(brand):
    gt   = GT.get(brand, 0)
    wiki = WIKI.get(brand, 0)
    R    = BAV[brand]["R"]
    D    = BAV[brand]["D"]
    E    = BAV[brand]["E"]
    K    = BAV[brand]["K"]
    CX   = BAV[brand]["CX"]
    loop = BAV[brand]["loop"]
    soc  = SOCIAL.get(brand, 0)

    if soc > 0:
        score = round(gt*0.35 + wiki*0.15 + R*0.10 + D*0.10 + soc*0.30, 1)
    else:
        score = round(gt*0.50 + wiki*0.20 + R*0.15 + D*0.15, 1)

    gap = round(R - D, 1)
    return {
        "id": brand,
        "ts_score": score,
        "gt_score": gt,
        "wiki_score": wiki,
        "social_score": soc,
        "R": R, "D": D, "E": E, "K": K, "CX": CX, "loop": loop,
        "search_gap": gap,
        "brand_architecture": round((D+E)/2, 1),
        "paris_syndrome": max(0, round(100-abs(D-CX))),
    }

output = sorted([ts_score(b) for b in BAV.keys()], key=lambda x: -x["ts_score"])

print(f"\n{'Marca':22s} {'TS':>6} {'GT':>5} {'Wiki':>4} {'Soc':>4} {'R':>5} {'D':>5} {'Gap':>6}  Diagnóstico")
print("-"*90)
for b in output:
    if b["search_gap"] > 20:
        diag = "⚡ Alta demanda, baja diferenciación"
    elif b["search_gap"] < -15:
        diag = "🎯 Alta diferenciación, escalar visibilidad"
    elif b["ts_score"] < 30:
        diag = "⚠ Visibilidad crítica"
    elif b["ts_score"] > 70:
        diag = "✓ Presencia sólida cross-canal"
    else:
        diag = "→ Posición media"
    print(f"{b['id']:22s} {b['ts_score']:>6.1f} {b['gt_score']:>5.1f} {b['wiki_score']:>4} {b['social_score']:>4.0f} {b['R']:>5.1f} {b['D']:>5.1f} {b['search_gap']:>+6.1f}  {diag}")

with open("totalsearch_final.json","w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(f"\n✓ {len(output)} marcas → totalsearch_final.json")
