"""
PPT Server — Flask API + dashboard para generación de decks por marca.
Sirve loop-infinite.html en / y la API en /generate-ppt y /brands.
"""
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io, traceback, os
from brand_engine import analyze_brand, RAW_BRANDS
from brand_ppt import generate_ppt

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
        analysis = analyze_brand(nombre)
        brand = analysis["brand"]
        sector = brand["sector"]
        n_sector = brand["n_sector"]

        print(f"[PPT] Generando: {nombre} | Sector: {sector} | Peers: {n_sector}")
        print(f"[PPT] Datos: BX={brand['bx']} CO={brand['co']} CX={brand['cx']}")
        print(f"[PPT] Avg sector: BX={analysis['sector_avg'].get('bx')} CO={analysis['sector_avg'].get('co')} CX={analysis['sector_avg'].get('cx')}")

        ppt_bytes = generate_ppt(nombre)

        filename = f"{nombre.replace(' ','_')}_Brand_Intelligence_2026.pptx"
        return send_file(
            io.BytesIO(ppt_bytes),
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
