"""
Social Search Score v3 — YouTube + TikTok + Reddit · Colombia 2026
"""
import requests, re, json, time, sys

H_YT = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}
H_TT = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "es-CO,es;q=0.9",
}
H_RD = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}

# ── helpers ──────────────────────────────────────────────────────────────────
def parse_count(text):
    """'120 k suscriptores' / '1.5M' / '34.2B' → int"""
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
    if n>=1_000_000:  return 100
    if n>=500_000:    return 88
    if n>=100_000:    return 74
    if n>=50_000:     return 60
    if n>=10_000:     return 45
    if n>=1_000:      return 28
    if n>0:           return 12
    return 5  # found but no count

def views_score(n):
    if n>=1_000_000_000: return 100
    if n>=500_000_000:   return 92
    if n>=100_000_000:   return 82
    if n>=50_000_000:    return 72
    if n>=10_000_000:    return 62
    if n>=1_000_000:     return 52
    if n>=100_000:       return 38
    if n>=10_000:        return 22
    if n>0:              return 10
    return 5  # page found but no count

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

# ── YOUTUBE ──────────────────────────────────────────────────────────────────
def youtube_score(query):
    try:
        r = requests.get("https://www.youtube.com/results",
            params={"search_query":query, "sp":"EgIQAg=="},
            headers=H_YT, timeout=15)
        m = re.search(r'var ytInitialData = ({.*?});', r.text)
        if not m: return 0,0,"—"
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
                    # subscriber count lives in videoCountText (naming quirk)
                    vct = ch.get("videoCountText",{})
                    sub_text = (vct.get("simpleText","") or
                                vct.get("accessibility",{}).get("accessibilityData",{}).get("label",""))
                    subs = parse_count(sub_text)
                    return subs_score(subs), subs, title
        return 0,0,"—"
    except Exception as e:
        return 0,0,f"err:{e}"

# ── TIKTOK ───────────────────────────────────────────────────────────────────
def tiktok_score(hashtag):
    url = f"https://www.tiktok.com/tag/{hashtag}"
    try:
        r = requests.get(url, headers=H_TT, timeout=15, allow_redirects=True)
        text = r.text
        views, videos = 0, 0

        # Pattern 1: JSON blob __UNIVERSAL_DATA_FOR_REHYDRATION__
        m = re.search(r'__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.+?})\s*</script>', text, re.DOTALL)
        if m:
            try:
                ud = json.loads(m.group(1))
                def walk(obj, keys):
                    results = {k:[] for k in keys}
                    stack = [obj]
                    while stack:
                        curr = stack.pop()
                        if isinstance(curr,dict):
                            for k,v in curr.items():
                                if k in keys: results[k].append(v)
                                stack.append(v)
                        elif isinstance(curr,list):
                            stack.extend(curr)
                    return results
                found = walk(ud, ["viewCount","videoCount","stats"])
                if found["viewCount"]: views = int(found["viewCount"][0])
                if found["videoCount"]: videos = int(found["videoCount"][0])
            except: pass

        # Pattern 2: raw JSON in page
        if views == 0:
            m2 = re.search(r'"viewCount"\s*:\s*"?(\d+)"?', text)
            if m2: views = int(m2.group(1))
        if videos == 0:
            m3 = re.search(r'"videoCount"\s*:\s*"?(\d+)"?', text)
            if m3: videos = int(m3.group(1))

        # Pattern 3: human-formatted numbers
        if views == 0:
            hits = re.findall(r'([\d.]+[KMBkmb]?)\s*(?:views|vistas|visualizaciones)', text, re.I)
            if hits: views = parse_count(hits[0])

        found_page = r.status_code == 200 and len(text) > 2000
        if views > 0: score = views_score(views)
        elif found_page: score = 5
        else: score = 0

        return score, views, videos
    except Exception as e:
        return 0,0,0

# ── REDDIT ────────────────────────────────────────────────────────────────────
def reddit_score(query):
    total_posts, total_karma = 0, 0
    subreddits = ["Colombia","Bogota","medellin","cali","colombia"]
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
                time.sleep(15)
                # retry once
                r2 = requests.get(
                    f"https://www.reddit.com/r/{sub}/search.json",
                    params={"q":query,"restrict_sr":"1","sort":"relevance","t":"year","limit":25},
                    headers=H_RD, timeout=12)
                if r2.status_code == 200:
                    posts = r2.json().get("data",{}).get("children",[])
                    total_posts += len(posts)
                    total_karma += sum(p["data"].get("score",0) for p in posts)
        except: pass
        time.sleep(3)  # generous delay for Reddit
    avg_karma = round(total_karma / max(total_posts,1))
    return posts_score(total_posts, avg_karma), total_posts, avg_karma

# ── Brand list ────────────────────────────────────────────────────────────────
BRANDS = [
  {"id":"D1",              "yt":"D1 supermercado Colombia",   "tt":"d1colombia",       "rd":"D1 supermercado"},
  {"id":"Ara",             "yt":"Ara supermercado Colombia",  "tt":"aracolombia",      "rd":"Ara supermercado"},
  {"id":"Exito",           "yt":"Éxito Colombia",             "tt":"exitocolombia",    "rd":"Exito tienda colombia"},
  {"id":"Olímpica",        "yt":"Olímpica supermercado",      "tt":"olimpica",         "rd":"olimpica supermercado"},
  {"id":"OXXO",            "yt":"OXXO Colombia",              "tt":"oxxo",             "rd":"OXXO tienda colombia"},
  {"id":"Makro",           "yt":"Makro Colombia",             "tt":"makro",            "rd":"Makro colombia"},
  {"id":"Cencosud",        "yt":"Cencosud Colombia",          "tt":"cencosud",         "rd":"Cencosud colombia"},
  {"id":"Falabella",       "yt":"Falabella Colombia",         "tt":"falabella",        "rd":"Falabella colombia"},
  {"id":"Movistar",        "yt":"Movistar Colombia",          "tt":"movistar",         "rd":"Movistar colombia"},
  {"id":"Avianca",         "yt":"Avianca",                    "tt":"avianca",          "rd":"Avianca vuelos"},
  {"id":"Arturo Calle",    "yt":"Arturo Calle Colombia",      "tt":"arturocalle",      "rd":"Arturo Calle colombia"},
  {"id":"Postobón",        "yt":"Postobón Colombia",          "tt":"postobon",         "rd":"Postobon bebida"},
  {"id":"Aguila",          "yt":"Cerveza Águila Colombia",    "tt":"aguila",           "rd":"aguila cerveza colombia"},
  {"id":"Renault",         "yt":"Renault Colombia",           "tt":"renaultcolombia",  "rd":"Renault carro colombia"},
  {"id":"Hyundai",         "yt":"Hyundai Colombia",           "tt":"hyundai",          "rd":"Hyundai colombia"},
  {"id":"Toyota",          "yt":"Toyota Colombia",            "tt":"toyota",           "rd":"Toyota colombia"},
  {"id":"Mazda",           "yt":"Mazda Colombia",             "tt":"mazda",            "rd":"Mazda colombia"},
  {"id":"Chevrolet",       "yt":"Chevrolet Colombia",         "tt":"chevrolet",        "rd":"Chevrolet colombia"},
  {"id":"Rappi",           "yt":"Rappi Colombia",             "tt":"rappi",            "rd":"Rappi domicilios"},
  {"id":"Sura",            "yt":"Sura Colombia",              "tt":"sura",             "rd":"Sura colombia seguros"},
  {"id":"Seguros Bolivar", "yt":"Seguros Bolívar Colombia",   "tt":"segurobolivar",    "rd":"Seguros Bolivar"},
  {"id":"Terpel",          "yt":"Terpel Colombia",            "tt":"terpel",           "rd":"Terpel gasolina"},
  {"id":"Primax",          "yt":"Primax Colombia",            "tt":"primax",           "rd":"Primax colombia"},
  {"id":"Biomax",          "yt":"Biomax Colombia",            "tt":"biomax",           "rd":"Biomax combustible"},
  {"id":"Farmatodo",       "yt":"Farmatodo Colombia",         "tt":"farmatodo",        "rd":"Farmatodo farmacia"},
  {"id":"Cruz Verde",      "yt":"Cruz Verde farmacia",        "tt":"cruzverde",        "rd":"Cruz Verde farmacia"},
  {"id":"Frisby",          "yt":"Frisby restaurante Colombia","tt":"frisby",           "rd":"Frisby pollo colombia"},
  {"id":"Decameron",       "yt":"Decameron hoteles Colombia", "tt":"decameron",        "rd":"Decameron hotel"},
  {"id":"H&M",             "yt":"H&M Colombia",               "tt":"hm",               "rd":"HM ropa colombia"},
  {"id":"Tigo",            "yt":"Tigo Colombia",              "tt":"tigocolombia",     "rd":"Tigo internet colombia"},
  {"id":"Tigo UNE",        "yt":"Tigo UNE Colombia",          "tt":"tigoune",          "rd":"Tigo UNE"},
  {"id":"WOM",             "yt":"WOM Colombia",               "tt":"womcolombia",      "rd":"WOM telefonia colombia"},
  {"id":"McDonald's",      "yt":"McDonald's Colombia",        "tt":"mcdonalds",        "rd":"McDonalds colombia"},
  {"id":"Coca-Cola",       "yt":"Coca-Cola Colombia",         "tt":"cocacola",         "rd":"Coca Cola colombia"},
  {"id":"Poker",           "yt":"Cerveza Poker Colombia",     "tt":"cervezapoker",     "rd":"Poker cerveza colombia"},
  {"id":"Club Colombia",   "yt":"Club Colombia cerveza",      "tt":"clubcolombia",     "rd":"Club Colombia cerveza"},
  {"id":"Corona",          "yt":"Corona cerveza Colombia",    "tt":"coronabeer",       "rd":"corona cerveza"},
  {"id":"Tennis",          "yt":"Tennis ropa Colombia",       "tt":"tennis",           "rd":"Tennis ropa colombia"},
  {"id":"Zapatoca",        "yt":"Mercado Zapatoca Colombia",  "tt":"zapatoca",         "rd":"Zapatoca supermercado"},
  {"id":"Nissan",          "yt":"Nissan Colombia",            "tt":"nissan",           "rd":"Nissan colombia"},
  {"id":"Grupo Aval",      "yt":"Grupo Aval Colombia",        "tt":"grupoaval",        "rd":"Grupo Aval banco"},
  {"id":"Petrobras",       "yt":"Petrobras Colombia",         "tt":"petrobras",        "rd":"Petrobras colombia"},
  {"id":"Suzuki",          "yt":"Suzuki Colombia",            "tt":"suzuki",           "rd":"Suzuki moto colombia"},
  {"id":"Colpatria",       "yt":"Colpatria banco Colombia",   "tt":"colpatria",        "rd":"Colpatria banco"},
  {"id":"American Airlines","yt":"American Airlines",         "tt":"americanairlines", "rd":"American Airlines colombia"},
  {"id":"United Airlines", "yt":"United Airlines",            "tt":"unitedairlines",   "rd":"United Airlines colombia"},
]

if __name__ == "__main__":
    print("="*72)
    print("SOCIAL SEARCH SCORE v3 — YouTube · TikTok · Reddit")
    print("="*72)
    results = {}
    for b in BRANDS:
        bid = b["id"]
        print(f"\n→ {bid}")

        yt_s, yt_subs, yt_name = youtube_score(b["yt"])
        print(f"   YT  {yt_s:3d}  subs={yt_subs:>10,}  '{yt_name}'")
        time.sleep(1.5)

        tt_s, tt_views, tt_vids = tiktok_score(b["tt"])
        print(f"   TT  {tt_s:3d}  views={tt_views:>12,}  vids={tt_vids}")
        time.sleep(2)

        rd_s, rd_posts, rd_karma = reddit_score(b["rd"])
        print(f"   RD  {rd_s:3d}  posts={rd_posts:>4}  avg_karma={rd_karma}")

        ss = round(yt_s*0.40 + tt_s*0.40 + rd_s*0.20, 1)
        print(f"   ── Social={ss}")
        results[bid] = {
            "social_score":ss,
            "yt_score":yt_s,"yt_subs":yt_subs,"yt_channel":yt_name,
            "tt_score":tt_s,"tt_views":tt_views,"tt_videos":tt_vids,
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
