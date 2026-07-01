"""
PPT Server — Flask API + dashboard para generación de decks por marca.
Sirve loop-infinite.html en / y la API en /generate-ppt y /brands.
"""
from flask import Flask, request, send_file, jsonify, session, redirect
from flask_cors import CORS
import traceback, os, hmac, secrets, time
from datetime import timedelta
from brand_engine import RAW_BRANDS
from brand_ppt import generate_ppt
from precache_ppts import cache_path, CACHE_DIR
import analytics_store as an

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)
an.init_db()

def _client_ip():
    return (request.headers.get("X-Forwarded-For", request.remote_addr or "")
            .split(",")[0].strip())

# ── ACCESO POR CONTRASEÑA ──────────────────────────────────────────────
# La contraseña se define en la variable de entorno ACCESS_PASSWORD (en Render).
# Si NO está configurada, la puerta queda DESACTIVADA (útil en local) — pero en
# producción DEBE configurarse o el sitio queda abierto a cualquiera con el link.
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "").strip()
# Clave para firmar la cookie de sesión. Fijar SECRET_KEY en Render para que las
# sesiones sobrevivan a reinicios; si no, se usa una aleatoria por arranque.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
# Cierre por INACTIVIDAD: la sesión expira tras N minutos sin actividad
# (configurable con SESSION_IDLE_MINUTES; por defecto 30).
IDLE_MINUTES = int(os.environ.get("SESSION_IDLE_MINUTES", "30"))
IDLE_SECONDS = IDLE_MINUTES * 60
app.permanent_session_lifetime = timedelta(minutes=IDLE_MINUTES)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),  # HTTPS en Render
)

# Rutas siempre abiertas (health para Render; login/logout para la puerta misma)
OPEN_PATHS = {"/health", "/login", "/logout"}

if not ACCESS_PASSWORD:
    print("⚠  ACCESS_PASSWORD no configurada — el sitio está ABIERTO. "
          "Configúrala en Render (Environment) antes de compartir el link.")

# ── ANALYTICS (solo para el propietario) ───────────────────────────────
# Contraseña INDEPENDIENTE de ACCESS_PASSWORD — las 20 personas que usan el
# dashboard nunca ven /analytics aunque conozcan la contraseña del sitio.
ANALYTICS_PASSWORD = os.environ.get("ANALYTICS_PASSWORD", "").strip()
ADMIN_OPEN_PATHS = {"/analytics/login"}

def _reject(expired: bool = False):
    """Navegación → redirige al login; llamadas API → 401 JSON."""
    if request.method == "GET" and request.path == "/":
        return redirect("/login?expired=1" if expired else "/login")
    return jsonify({"error": "Sesión expirada por inactividad." if expired
                    else "No autorizado. Inicia sesión en /login."}), 401

@app.before_request
def _require_login():
    # /analytics tiene su PROPIO gate, totalmente independiente del sitio
    # (contraseña distinta; los 20 usuarios del dashboard no pueden entrar aquí).
    if request.path.startswith("/analytics"):
        if request.path in ADMIN_OPEN_PATHS:
            return None
        if not ANALYTICS_PASSWORD:
            return jsonify({"error": "Analytics no configurado."}), 404
        if not session.get("analytics_authed"):
            return redirect("/analytics/login")
        return None

    if not ACCESS_PASSWORD:          # puerta desactivada
        return None
    if request.path in OPEN_PATHS:
        return None
    if not session.get("authed"):
        return _reject()
    # Cierre por inactividad: si pasó el umbral desde la última actividad, expira
    now = time.time()
    last = session.get("last_active", now)
    if now - last > IDLE_SECONDS:
        session.clear()
        return _reject(expired=True)
    # Actividad válida → refrescar la ventana de inactividad
    session["last_active"] = now
    session.permanent = True
    return None

@app.route("/ping", methods=["POST"])
def ping():
    # Keep-alive del dashboard (client-side). El before_request ya validó sesión
    # y refrescó last_active; aquí solo confirmamos.
    return jsonify({"ok": True})

def _login_page(error: bool = False, expired: bool = False) -> str:
    if error:
        msg = '<p class="err">Contraseña incorrecta. Intenta de nuevo.</p>'
    elif expired:
        msg = '<p class="note">Tu sesión se cerró por inactividad. Ingresa de nuevo.</p>'
    else:
        msg = ''
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Acceso · Capital Intangible</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{min-height:100vh;display:flex;align-items:center;justify-content:center;
  background:#070B19;background-image:
    radial-gradient(ellipse 60% 50% at 30% 20%,rgba(255,122,0,.10) 0%,transparent 60%),
    radial-gradient(ellipse 50% 40% at 80% 90%,rgba(0,210,106,.06) 0%,transparent 55%);
  color:#fff;font-family:-apple-system,'SF Pro Display',Helvetica Neue,sans-serif;padding:24px}}
.card{{width:100%;max-width:380px;background:rgba(18,26,47,.7);
  border:1px solid rgba(255,255,255,.08);border-radius:20px;padding:36px 32px;
  box-shadow:0 24px 64px rgba(0,0,0,.5),inset 0 1px 0 rgba(255,255,255,.06);
  backdrop-filter:blur(12px)}}
.badge{{display:inline-flex;align-items:center;gap:8px;font-size:10px;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;color:#FF7A00;margin-bottom:18px}}
.dot{{width:6px;height:6px;border-radius:50%;background:#FF7A00;box-shadow:0 0 8px #FF7A00}}
h1{{font-size:22px;font-weight:800;letter-spacing:-.02em;margin-bottom:6px}}
p.sub{{font-size:13px;color:rgba(163,168,184,.75);line-height:1.5;margin-bottom:24px}}
label{{display:block;font-size:11px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:rgba(163,168,184,.7);margin-bottom:8px}}
input{{width:100%;background:rgba(7,11,25,.6);border:1px solid rgba(255,255,255,.12);
  border-radius:12px;padding:14px 16px;color:#fff;font-size:15px;outline:none;
  transition:border-color .2s}}
input:focus{{border-color:#FF7A00}}
button{{width:100%;margin-top:18px;background:linear-gradient(135deg,#FF7A00,#FF9A00);
  color:#fff;border:none;border-radius:100px;padding:15px;font-size:15px;font-weight:700;
  cursor:pointer;box-shadow:0 8px 24px rgba(255,122,0,.3);transition:transform .2s}}
button:hover{{transform:translateY(-2px)}}
button:active{{transform:translateY(0) scale(.98)}}
.err{{color:#FF3B30;font-size:13px;font-weight:600;margin-top:14px;text-align:center}}
.note{{color:#f4a261;font-size:12.5px;font-weight:500;margin-top:14px;text-align:center;line-height:1.4}}
.foot{{margin-top:22px;font-size:10.5px;color:rgba(163,168,184,.35);text-align:center;letter-spacing:.04em}}
</style></head><body>
<form class="card" method="POST" action="/login" autocomplete="off">
  <div class="badge"><span class="dot"></span>Acceso restringido</div>
  <h1>Capital Intangible</h1>
  <p class="sub">Brand Intelligence Loop · ingresa la contraseña para acceder al diagnóstico.</p>
  <label for="p">Contraseña</label>
  <input id="p" name="password" type="password" autofocus required/>
  <button type="submit">Ingresar</button>
  {msg}
  <p class="foot">Brand Asset Valuator · WPP Colombia · 2026</p>
</form></body></html>"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if not ACCESS_PASSWORD:
        return redirect("/")
    if request.method == "POST":
        entered = request.form.get("password", "")
        if hmac.compare_digest(entered, ACCESS_PASSWORD):
            session.permanent = True
            session["authed"] = True
            session["last_active"] = time.time()
            session["sid"] = secrets.token_hex(8)
            an.log_event(session["sid"], "login", ip=_client_ip(), ua=request.headers.get("User-Agent", ""))
            return redirect("/")
        return _login_page(error=True), 401
    if session.get("authed"):
        return redirect("/")
    return _login_page(expired=request.args.get("expired") == "1")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/track", methods=["POST"])
def track():
    """Keep-alive de eventos del dashboard (clicks, selects). Requiere sesión
    del sitio (antes ya validada por before_request) — evita spam externo."""
    data = request.get_json(silent=True) or {}
    event = str(data.get("event", "")).strip()[:40]
    if not event:
        return jsonify({"ok": False}), 400
    an.log_event(session.get("sid"), event, data.get("label"), None,
                 _client_ip(), request.headers.get("User-Agent", ""))
    return jsonify({"ok": True})

# ═══════════════════════════════════════════════════════════
# ANALYTICS — hoja privada, solo para el propietario
# ═══════════════════════════════════════════════════════════

def _admin_login_page(error: bool = False) -> str:
    msg = '<p class="err">Contraseña incorrecta.</p>' if error else ''
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Analytics · Capital Intangible</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{min-height:100vh;display:flex;align-items:center;justify-content:center;
  background:#070B19;color:#fff;font-family:-apple-system,'SF Pro Display',Helvetica Neue,sans-serif;padding:24px}}
.card{{width:100%;max-width:380px;background:rgba(18,26,47,.7);border:1px solid rgba(255,255,255,.08);
  border-radius:20px;padding:36px 32px;box-shadow:0 24px 64px rgba(0,0,0,.5);backdrop-filter:blur(12px)}}
.badge{{display:inline-flex;align-items:center;gap:8px;font-size:10px;font-weight:700;letter-spacing:.14em;
  text-transform:uppercase;color:#7C8CFF;margin-bottom:18px}}
.dot{{width:6px;height:6px;border-radius:50%;background:#7C8CFF;box-shadow:0 0 8px #7C8CFF}}
h1{{font-size:20px;font-weight:800;margin-bottom:6px}}
p.sub{{font-size:13px;color:rgba(163,168,184,.75);margin-bottom:24px}}
label{{display:block;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
  color:rgba(163,168,184,.7);margin-bottom:8px}}
input{{width:100%;background:rgba(7,11,25,.6);border:1px solid rgba(255,255,255,.12);border-radius:12px;
  padding:14px 16px;color:#fff;font-size:15px;outline:none}}
input:focus{{border-color:#7C8CFF}}
button{{width:100%;margin-top:18px;background:linear-gradient(135deg,#5A6CFF,#7C8CFF);color:#fff;border:none;
  border-radius:100px;padding:15px;font-size:15px;font-weight:700;cursor:pointer}}
.err{{color:#FF3B30;font-size:13px;font-weight:600;margin-top:14px;text-align:center}}
</style></head><body>
<form class="card" method="POST" action="/analytics/login">
  <div class="badge"><span class="dot"></span>Solo propietario</div>
  <h1>Analytics</h1>
  <p class="sub">Sesiones, clicks y descargas · acceso independiente del dashboard.</p>
  <label for="p">Contraseña de analytics</label>
  <input id="p" name="password" type="password" autofocus required/>
  <button type="submit">Entrar</button>
  {msg}
</form></body></html>"""

@app.route("/analytics/login", methods=["GET", "POST"])
def analytics_login():
    if not ANALYTICS_PASSWORD:
        return jsonify({"error": "ANALYTICS_PASSWORD no configurada."}), 404
    if request.method == "POST":
        entered = request.form.get("password", "")
        if hmac.compare_digest(entered, ANALYTICS_PASSWORD):
            session["analytics_authed"] = True
            return redirect("/analytics")
        return _admin_login_page(error=True), 401
    if session.get("analytics_authed"):
        return redirect("/analytics")
    return _admin_login_page()

@app.route("/analytics/logout")
def analytics_logout():
    session.pop("analytics_authed", None)
    return redirect("/analytics/login")

def _bars(items, color="#FF7A00"):
    if not items:
        return '<p class="empty">Sin datos todavía.</p>'
    maxn = max(n for _, n in items) or 1
    rows = ""
    for label, n in items:
        pct = int((n / maxn) * 100)
        safe_label = str(label).replace("<", "&lt;").replace(">", "&gt;")
        rows += (f'<div class="brow"><span class="blabel">{safe_label}</span>'
                 f'<div class="btrack"><div class="bfill" style="width:{pct}%;background:{color}"></div></div>'
                 f'<span class="bval">{n}</span></div>')
    return rows

def _daily_chart(series):
    if not series:
        return '<p class="empty">Sin datos todavía.</p>'
    maxn = max(n for _, n in series) or 1
    bars = ""
    for d, n in series:
        h = max(int((n / maxn) * 100), 6)
        bars += f'<div class="dbar" style="height:{h}%" title="{d}: {n} sesiones"><span>{n}</span></div>'
    return f'<div class="dchart">{bars}</div>'

def _recent_rows(events):
    if not events:
        return '<tr><td colspan="4" class="empty">Sin actividad todavía.</td></tr>'
    rows = ""
    for e in events:
        label = (e["label"] or "—").replace("<", "&lt;").replace(">", "&gt;")
        sid = (e["session_id"] or "—")[:8]
        rows += (f'<tr><td class="mono">{e["ts"][11:19]}</td><td>{e["event_type"]}</td>'
                 f'<td>{label}</td><td class="mono">{sid}</td></tr>')
    return rows

def _analytics_page(period_days) -> str:
    s = an.summary(days=period_days)
    top_brands     = an.top_labels("brand_select",   days=period_days, limit=8)
    top_categories = an.top_labels("category_select", days=period_days, limit=6)
    top_ppt        = an.top_labels("ppt_download",   days=period_days, limit=8)
    top_kpi        = an.top_labels("kpi_click",      days=period_days, limit=6)
    top_concepts   = an.top_labels("concept_click",  days=period_days, limit=8)
    daily          = an.daily_sessions(days=14)
    recent         = an.recent_events(limit=60)

    periods = [(1, "Hoy"), (7, "7 días"), (30, "30 días"), (None, "Todo")]
    period_pills = "".join(
        f'<a href="/analytics?period={p if p is not None else "all"}" '
        f'class="pp{" active" if p == period_days else ""}">{lbl}</a>'
        for p, lbl in periods
    )
    storage_note = ("almacenamiento persistente (Postgres) — los datos se conservan entre deploys."
                     if an.BACKEND == "postgres" else
                     "⚠ SQLite local sin DATABASE_URL configurada: los datos se pierden en cada redeploy.")

    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Analytics · Capital Intangible</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#070B19;color:#fff;font-family:-apple-system,'SF Pro Display',Helvetica Neue,sans-serif;
  padding:32px 40px 60px;font-size:14px}}
h1{{font-size:24px;font-weight:800;letter-spacing:-.02em}}
.top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:12px}}
.sub{{color:rgba(163,168,184,.6);font-size:12px;margin-bottom:24px}}
.periods{{display:flex;gap:6px}}
.pp{{color:rgba(163,168,184,.7);text-decoration:none;font-size:12px;font-weight:600;padding:6px 14px;
  border-radius:100px;border:1px solid rgba(255,255,255,.08)}}
.pp.active{{background:#FF7A00;color:#fff;border-color:#FF7A00}}
.logout{{color:rgba(163,168,184,.5);text-decoration:none;font-size:11px}}
.grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:28px}}
.stat{{background:rgba(18,26,47,.7);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:18px}}
.stat .n{{font-size:30px;font-weight:800;color:#FF7A00;font-variant-numeric:tabular-nums}}
.stat .l{{font-size:10.5px;color:rgba(163,168,184,.6);text-transform:uppercase;letter-spacing:.06em;margin-top:4px}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}}
.panel{{background:rgba(18,26,47,.7);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:20px}}
.panel h2{{font-size:13px;font-weight:700;margin-bottom:14px;color:rgba(255,255,255,.9)}}
.brow{{display:flex;align-items:center;gap:10px;margin-bottom:9px;font-size:12px}}
.blabel{{width:150px;flex-shrink:0;color:rgba(163,168,184,.85);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.btrack{{flex:1;height:8px;background:rgba(255,255,255,.06);border-radius:4px;overflow:hidden}}
.bfill{{height:100%;border-radius:4px}}
.bval{{width:28px;text-align:right;color:#fff;font-weight:700;font-variant-numeric:tabular-nums}}
.empty{{color:rgba(163,168,184,.4);font-size:12px;font-style:italic}}
.dchart{{display:flex;align-items:flex-end;gap:5px;height:110px;margin-top:6px}}
.dbar{{flex:1;background:linear-gradient(180deg,#FF9A00,#FF7A00);border-radius:3px 3px 0 0;position:relative;min-width:8px}}
.dbar span{{position:absolute;top:-16px;left:0;right:0;text-align:center;font-size:9px;color:rgba(163,168,184,.7)}}
table{{width:100%;border-collapse:collapse;font-size:11.5px}}
th{{text-align:left;color:#FF7A00;font-weight:700;padding:6px 8px;border-bottom:1px solid rgba(255,255,255,.08)}}
td{{padding:6px 8px;border-bottom:1px solid rgba(255,255,255,.04);color:rgba(163,168,184,.9)}}
.mono{{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;color:rgba(163,168,184,.55)}}
.recent{{max-height:420px;overflow-y:auto}}
@media(max-width:1100px){{.grid{{grid-template-columns:repeat(2,1fr)}}.cols{{grid-template-columns:1fr}}}}
</style></head><body>
<div class="top">
  <div><h1>Analytics · Capital Intangible</h1></div>
  <div style="display:flex;align-items:center;gap:16px">
    <div class="periods">{period_pills}</div>
    <a class="logout" href="/analytics/logout">Cerrar sesión de analytics</a>
  </div>
</div>
<p class="sub">Uso interno · {storage_note}</p>

<div class="grid">
  <div class="stat"><div class="n">{s['sessions']}</div><div class="l">Sesiones (logins únicos)</div></div>
  <div class="stat"><div class="n">{s['logins']}</div><div class="l">Inicios de sesión</div></div>
  <div class="stat"><div class="n">{s['pageviews']}</div><div class="l">Vistas de dashboard</div></div>
  <div class="stat"><div class="n">{s['downloads']}</div><div class="l">Descargas de PPT</div></div>
  <div class="stat"><div class="n">{s['total']}</div><div class="l">Eventos totales</div></div>
</div>

<div class="panel" style="margin-bottom:24px">
  <h2>Sesiones por día (14 días)</h2>
  {_daily_chart(daily)}
</div>

<div class="cols">
  <div class="panel"><h2>Marcas más consultadas</h2>{_bars(top_brands)}</div>
  <div class="panel"><h2>PPTs más descargados</h2>{_bars(top_ppt, "#00D26A")}</div>
  <div class="panel"><h2>Categorías más exploradas</h2>{_bars(top_categories, "#7C8CFF")}</div>
  <div class="panel"><h2>Clicks en tarjetas KPI</h2>{_bars(top_kpi, "#FF3B30")}</div>
</div>

<div class="panel" style="margin-bottom:24px">
  <h2>Clicks en conceptos (ⓘ)</h2>
  {_bars(top_concepts, "#F4A261")}
</div>

<div class="panel">
  <h2>Actividad reciente</h2>
  <div class="recent"><table>
    <tr><th>Hora</th><th>Evento</th><th>Detalle</th><th>Sesión</th></tr>
    {_recent_rows(recent)}
  </table></div>
</div>
</body></html>"""

@app.route("/analytics")
def analytics_page():
    period_arg = request.args.get("period", "7")
    period_days = None if period_arg == "all" else int(period_arg)
    return _analytics_page(period_days)

VALID_BRANDS = {b["marca"] for b in RAW_BRANDS}

@app.route("/")
def index():
    return app.send_static_file("loop-infinite.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok", "brands": len(VALID_BRANDS)})

@app.route("/brands")
def brands():
    return jsonify(sorted(VALID_BRANDS))

@app.route("/download-base")
def download_base():
    path = os.path.join(os.path.dirname(__file__), "BAV_Brand_Intelligence_Colombia_2026_Base_Maestra.xlsx")
    if not os.path.exists(path):
        return jsonify({"error": "Archivo no encontrado."}), 404
    return send_file(
        path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="BAV_Brand_Intelligence_Colombia_2026_Base_Maestra.xlsx"
    )

@app.route("/generate-ppt")
def generate():
    nombre = request.args.get("brand", "").strip()

    if not nombre:
        return jsonify({"error": "Parámetro 'brand' requerido."}), 400

    if nombre not in VALID_BRANDS:
        return jsonify({
            "error": f"Marca '{nombre}' no existe en la base de datos.",
            "hint": "Usa /brands para ver las marcas disponibles."
        }), 404

    brand_data = next(b for b in RAW_BRANDS if b["marca"] == nombre)
    available = {k: v for k, v in brand_data.items() if v is not None and k != "marca"}
    if len(available) < 3:
        return jsonify({
            "error": f"Datos insuficientes para '{nombre}'. Solo {len(available)} indicadores disponibles.",
            "available_fields": list(available.keys())
        }), 422

    try:
        path = cache_path(nombre)

        # Cache hit → servir el PPT pre-generado (instantáneo, sin CPU de generación)
        if os.path.exists(path):
            print(f"[PPT] Cache hit: {nombre}")
        else:
            # Fallback perezoso: el build no lo dejó listo → generar y cachear una vez
            print(f"[PPT] Cache miss → generando on-demand: {nombre}")
            os.makedirs(CACHE_DIR, exist_ok=True)
            tmp = f"{path}.{os.getpid()}.tmp"   # único por worker → sin colisión
            with open(tmp, "wb") as f:
                f.write(generate_ppt(nombre))
            os.replace(tmp, path)  # escritura atómica: nunca se sirve un archivo a medias

        # Log server-side: más confiable que trackear desde el cliente (no
        # depende de que el navegador termine de ejecutar el JS de descarga).
        an.log_event(session.get("sid"), "ppt_download", nombre, None,
                     _client_ip(), request.headers.get("User-Agent", ""))

        filename = f"{nombre.replace(' ','_')}_Brand_Intelligence_2026.pptx"
        return send_file(
            path,
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        return jsonify({"error": "Error interno generando PPT.", "detail": traceback.format_exc()}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    print(f"Brand Intelligence Server · Puerto {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
