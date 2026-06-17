"""
Social Score builder — YouTube (scraped) + TikTok (curated) + Reddit (scraped)
Corre YouTube y Reddit con social_scores_v3.py; TikTok curado por presencia conocida
"""
import requests, re, json, time, sys

# ── TikTok curated scores (presencia conocida Colombia 2024-2025) ────────────
# Escala 0-100: 100=10M+ vistas/tag global, 80=5M+, 60=1M+, 40=100k+, 20=visible, 0=sin presencia
TT_CURATED = {
  "Rappi":           85,  # viral en LATAM, 10M+ vistas hashtag
  "McDonald's":      80,  # global fuerte TT
  "Coca-Cola":       78,  # global pero menor actividad Colombia
  "H&M":             72,  # global moda TT activo
  "Avianca":         65,  # frecuente en TT Colombia viajes
  "Falabella":       65,  # activa en TT Colombia/LATAM
  "Exito":           60,  # éxito Colombia activa
  "Movistar":        58,  # telco activo en TT
  "Tigo":            55,  # telco TT Colombia
  "WOM":             52,  # WOM activa en redes
  "D1":              50,  # D1 creciendo en TT Colombia
  "Ara":             48,  # Ara Colombia activa
  "Renault":         60,  # autos TT activo
  "Toyota":          58,  # autos TT global
  "Chevrolet":       55,  # Chevrolet Colombia TT
  "Hyundai":         52,  # Hyundai Colombia TT
  "Nissan":          50,  # Nissan Colombia TT
  "Mazda":           48,  # Mazda Colombia TT
  "Suzuki":          45,  # Suzuki moto Colombia TT
  "Corona":          62,  # Cerveza Corona global viral
  "Aguila":          55,  # Cerveza Águila Colombia TT
  "Club Colombia":   50,  # Club Colombia cerveza TT
  "Poker":           42,  # Poker cerveza TT
  "Postobón":        48,  # Postobón Colombia TT
  "Arturo Calle":    52,  # moda Colombia TT activo
  "Tennis":          48,  # Tennis ropa Colombia TT
  "Farmatodo":       40,  # farmacia TT Colombia
  "Cruz Verde":      38,  # farmacia TT Colombia
  "Frisby":          60,  # Frisby viral Colombia TT
  "Decameron":       55,  # Decameron viajes TT
  "Sura":            35,  # seguros TT menos activo
  "Seguros Bolivar": 30,  # seguros TT menor presencia
  "Terpel":          35,  # combustible TT Colombia
  "Primax":          25,  # Primax Colombia TT bajo
  "Biomax":          20,  # Biomax TT mínimo
  "Olímpica":        42,  # Olímpica Colombia TT
  "OXXO":            45,  # OXXO Colombia TT
  "Makro":           35,  # Makro TT Colombia
  "Cencosud":        30,  # Cencosud TT
  "Tigo UNE":        30,  # Tigo UNE TT bajo
  "Zapatoca":        25,  # Zapatoca TT Colombia
  "Grupo Aval":      20,  # banco TT Colombia
  "Petrobras":       15,  # Petrobras TT Colombia bajo
  "Colpatria":       20,  # banco TT Colombia
  "American Airlines":55, # American Airlines TT viajes
  "United Airlines": 48,  # United Airlines TT viajes
}

# ── Headers ──────────────────────────────────────────────────────────────────
H_YT = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}
H_RD = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}

def parse_count(text):
    if not text: return 0
    s = str(text).replace("\xa0"," ").replace(",",".").strip().upper()
    m = re.search(r"([\d]+(?:[.,]\d+)?)\s*([KMB]?)", s)
    if not m: return 0
    n = float(m.group(1).replace(",","."))
    u = m.group(2)
    if u=="K": return int(n*1_000)
    if u=="M": return int(n*1_000_000)
    if u=="B": return int(n*1_000_000_000)
    return int(n)

def subs_score(n):
    if n>=1_000_000: return 100
    if n>=500_000:   return 88
    if n>=100_000:   return 74
    if n>=50_000:    return 60
    if n>=10_000:    return 45
    if n>=1_000:     return 28
    if n>0:          return 12
    return 5

def posts_score(n, avg_karma=0):
    if n==0: return 0
    if n>=50:   s=100
    elif n>=25: s=80
    elif n>=10: s=60
    elif n>=5:  s=40
    else:       s=20
    if avg_karma>200: s=min(100,s+15)
    elif avg_karma>50: s=min(100,s+8)
    return s

def youtube_score(query):
    try:
        r = requests.get("https://www.youtube.com/results",
            params={"search_query":query, "sp":"EgIQAg=="},
            headers=H_YT, timeout=15)
        m = re.search(r'var ytInitialData = ({.*?});', r.text)
        if not m: return 5,0,"—"
        data = json.loads(m.group(1))
        sections = (data.get("contents",{})
                       .get("twoColumnSearchResultsRenderer",{})
                       .get("primaryContents",{})
                       .get("sectionListRenderer",{})
                       .get("contents",[]))
        for sec in sections:
            for item in sec.get("itemSectionRenderer",{}).get("contents",[]):
                if "channelRenderer" in item:
                    ch = item["channelRenderer"]
                    title = ch.get("title",{}).get("simpleText","—")
                    vct = ch.get("videoCountText",{})
                    sub_text = (vct.get("simpleText","") or
                                vct.get("accessibility",{}).get("accessibilityData",{}).get("label",""))
                    subs = parse_count(sub_text)
                    return subs_score(subs), subs, title
        return 5,0,"—"
    except Exception as e:
        return 5,0,f"err:{e}"

def reddit_score(query):
    total_posts, total_karma = 0, 0
    subreddits = ["Colombia","Bogota","medellin","colombia"]
    for sub in subreddits:
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/search.json",
                params={"q":query,"restrict_sr":"1","sort":"relevance","t":"year","limit":25},
                headers=H_RD, timeout=12)
            if r.status_code == 200:
                posts = r.json().get("data",{}).get("children",[])
                total_posts += len(posts)
                total_karma += sum(p["data"].get("score",0) for p in posts)
            elif r.status_code == 429:
                time.sleep(20)
        except: pass
        time.sleep(4)
    avg_karma = round(total_karma / max(total_posts,1))
    return posts_score(total_posts, avg_karma), total_posts, avg_karma

# ── Brand list ────────────────────────────────────────────────────────────────
BRANDS = [
  {"id":"D1",              "yt":"D1 supermercado Colombia",    "rd":"D1 supermercado"},
  {"id":"Ara",             "yt":"Ara supermercado Colombia",   "rd":"Ara supermercado"},
  {"id":"Exito",           "yt":"Éxito supermercado Colombia", "rd":"Exito tienda colombia"},
  {"id":"Olímpica",        "yt":"Olímpica supermercado",       "rd":"olimpica supermercado"},
  {"id":"OXXO",            "yt":"OXXO Colombia",               "rd":"OXXO tienda colombia"},
  {"id":"Makro",           "yt":"Makro Colombia",              "rd":"Makro colombia"},
  {"id":"Cencosud",        "yt":"Cencosud Colombia",           "rd":"Cencosud colombia"},
  {"id":"Falabella",       "yt":"Falabella Colombia tienda",   "rd":"Falabella colombia"},
  {"id":"Movistar",        "yt":"Movistar Colombia oficial",   "rd":"Movistar colombia"},
  {"id":"Avianca",         "yt":"Avianca aerolinea",           "rd":"Avianca vuelos"},
  {"id":"Arturo Calle",    "yt":"Arturo Calle moda Colombia",  "rd":"Arturo Calle colombia"},
  {"id":"Postobón",        "yt":"Postobón bebidas Colombia",   "rd":"Postobon bebida"},
  {"id":"Aguila",          "yt":"Cerveza Águila Colombia",     "rd":"aguila cerveza colombia"},
  {"id":"Renault",         "yt":"Renault Colombia autos",      "rd":"Renault carro colombia"},
  {"id":"Hyundai",         "yt":"Hyundai Colombia autos",      "rd":"Hyundai colombia"},
  {"id":"Toyota",          "yt":"Toyota Colombia oficial",     "rd":"Toyota colombia"},
  {"id":"Mazda",           "yt":"Mazda Colombia autos",        "rd":"Mazda colombia"},
  {"id":"Chevrolet",       "yt":"Chevrolet Colombia autos",    "rd":"Chevrolet colombia"},
  {"id":"Rappi",           "yt":"Soy Rappi Colombia",          "rd":"Rappi domicilios"},
  {"id":"Sura",            "yt":"Sura seguros Colombia",       "rd":"Sura colombia seguros"},
  {"id":"Seguros Bolivar", "yt":"Seguros Bolívar Colombia",    "rd":"Seguros Bolivar"},
  {"id":"Terpel",          "yt":"Terpel Colombia gasolina",    "rd":"Terpel gasolina"},
  {"id":"Primax",          "yt":"Primax Colombia",             "rd":"Primax colombia"},
  {"id":"Biomax",          "yt":"Biomax Colombia combustible", "rd":"Biomax combustible"},
  {"id":"Farmatodo",       "yt":"Farmatodo farmacia Colombia", "rd":"Farmatodo farmacia"},
  {"id":"Cruz Verde",      "yt":"Cruz Verde farmacia Colombia","rd":"Cruz Verde farmacia"},
  {"id":"Frisby",          "yt":"Frisby pollo Colombia",       "rd":"Frisby pollo colombia"},
  {"id":"Decameron",       "yt":"Decameron hoteles Colombia",  "rd":"Decameron hotel"},
  {"id":"H&M",             "yt":"H&M Colombia moda",           "rd":"HM ropa colombia"},
  {"id":"Tigo",            "yt":"Tigo Colombia internet",      "rd":"Tigo internet colombia"},
  {"id":"Tigo UNE",        "yt":"Tigo UNE Colombia",           "rd":"Tigo UNE"},
  {"id":"WOM",             "yt":"WOM Colombia telefonia",      "rd":"WOM telefonia colombia"},
  {"id":"McDonald's",      "yt":"McDonalds Colombia",          "rd":"McDonalds colombia"},
  {"id":"Coca-Cola",       "yt":"Coca Cola Colombia oficial",  "rd":"Coca Cola colombia"},
  {"id":"Poker",           "yt":"Cerveza Poker Colombia",      "rd":"Poker cerveza colombia"},
  {"id":"Club Colombia",   "yt":"Club Colombia cerveza oficial","rd":"Club Colombia cerveza"},
  {"id":"Corona",          "yt":"Cerveza Corona Colombia",     "rd":"corona cerveza"},
  {"id":"Tennis",          "yt":"Tennis ropa deportiva Colombia","rd":"Tennis ropa colombia"},
  {"id":"Zapatoca",        "yt":"Mercado Zapatoca Colombia",   "rd":"Zapatoca supermercado"},
  {"id":"Nissan",          "yt":"Nissan Colombia autos",       "rd":"Nissan colombia"},
  {"id":"Grupo Aval",      "yt":"Grupo Aval banco Colombia",   "rd":"Grupo Aval banco"},
  {"id":"Petrobras",       "yt":"Petrobras Colombia",          "rd":"Petrobras colombia"},
  {"id":"Suzuki",          "yt":"Suzuki Colombia motos",       "rd":"Suzuki moto colombia"},
  {"id":"Colpatria",       "yt":"Banco Colpatria Colombia",    "rd":"Colpatria banco"},
  {"id":"American Airlines","yt":"American Airlines Colombia", "rd":"American Airlines colombia"},
  {"id":"United Airlines", "yt":"United Airlines Colombia",    "rd":"United Airlines colombia"},
]

if __name__ == "__main__":
    print("="*72)
    print("SOCIAL SCORE — YouTube(scraped) + TikTok(curado) + Reddit(scraped)")
    print("="*72)
    results = {}
    for b in BRANDS:
        bid = b["id"]
        print(f"\n→ {bid}")

        yt_s, yt_subs, yt_name = youtube_score(b["yt"])
        print(f"   YT  {yt_s:3d}  subs={yt_subs:>10,}  '{yt_name}'")
        time.sleep(2)

        tt_s = TT_CURATED.get(bid, 20)
        print(f"   TT  {tt_s:3d}  (curado)")

        rd_s, rd_posts, rd_karma = reddit_score(b["rd"])
        print(f"   RD  {rd_s:3d}  posts={rd_posts}  avg_karma={rd_karma}")

        ss = round(yt_s*0.40 + tt_s*0.40 + rd_s*0.20, 1)
        print(f"   ── Social={ss}")
        results[bid] = {
            "social_score":ss,
            "yt_score":yt_s,"yt_subs":yt_subs,"yt_channel":yt_name,
            "tt_score":tt_s,"tt_curated":True,
            "rd_score":rd_s,"rd_posts":rd_posts,
        }

    print("\n"+"="*72)
    print(f"{'Marca':22s} {'Social':>7} {'YT':>5} {'TT':>5} {'RD':>5}")
    print("-"*46)
    for k,v in sorted(results.items(), key=lambda x:-x[1]["social_score"]):
        print(f"{k:22s} {v['social_score']:>7.1f} {v['yt_score']:>5} {v['tt_score']:>5} {v['rd_score']:>5}")
    with open("social_scores.json","w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ social_scores.json actualizado")
