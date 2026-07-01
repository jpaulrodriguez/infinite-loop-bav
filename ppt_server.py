"""
PPT Server — Flask API + dashboard para generación de decks por marca.
Sirve loop-infinite.html en / y la API en /generate-ppt y /brands.
"""
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import traceback, os
from brand_engine import RAW_BRANDS
from brand_ppt import generate_ppt
from precache_ppts import cache_path, CACHE_DIR

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

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
