"""
PPT Server — Flask API + dashboard para generación de decks por marca.
Sirve loop-infinite.html en / y la API en /generate-ppt y /brands.
"""
from flask import Flask, request, send_file, jsonify, session, redirect
from flask_cors import CORS
import traceback, os, hmac, secrets
from datetime import timedelta
from brand_engine import RAW_BRANDS
from brand_ppt import generate_ppt
from precache_ppts import cache_path, CACHE_DIR

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ── ACCESO POR CONTRASEÑA ──────────────────────────────────────────────
# La contraseña se define en la variable de entorno ACCESS_PASSWORD (en Render).
# Si NO está configurada, la puerta queda DESACTIVADA (útil en local) — pero en
# producción DEBE configurarse o el sitio queda abierto a cualquiera con el link.
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "").strip()
# Clave para firmar la cookie de sesión. Fijar SECRET_KEY en Render para que las
# sesiones sobrevivan a reinicios; si no, se usa una aleatoria por arranque.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(days=7)
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

@app.before_request
def _require_login():
    if not ACCESS_PASSWORD:          # puerta desactivada
        return None
    if request.path in OPEN_PATHS or session.get("authed"):
        return None
    # No autenticado: navegación → login; llamadas API → 401
    if request.method == "GET" and request.path == "/":
        return redirect("/login")
    return jsonify({"error": "No autorizado. Inicia sesión en /login."}), 401

def _login_page(error: bool = False) -> str:
    msg = ('<p class="err">Contraseña incorrecta. Intenta de nuevo.</p>'
           if error else '')
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
            return redirect("/")
        return _login_page(error=True), 401
    if session.get("authed"):
        return redirect("/")
    return _login_page()

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

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
