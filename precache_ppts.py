"""
Pre-generación de los PPTs de todas las marcas válidas.

Los datos de las 82 marcas son estáticos, así que cada PPT es determinista:
generarlos una vez y servirlos desde disco convierte la descarga en instantánea
y con CPU casi nula. Se ejecuta en el build de Render (cache caliente desde el
arranque) y el servidor tiene además un fallback perezoso por si faltara alguno.
"""
import os
from brand_engine import RAW_BRANDS
from brand_ppt import generate_ppt

CACHE_DIR = os.path.join(os.path.dirname(__file__), "ppt_cache")


def cache_key(nombre: str) -> str:
    """Nombre de archivo estable y seguro para el sistema de archivos."""
    return "".join(c if c.isalnum() else "_" for c in nombre) + ".pptx"


def cache_path(nombre: str) -> str:
    return os.path.join(CACHE_DIR, cache_key(nombre))


def _has_enough_data(b: dict) -> bool:
    return len([v for k, v in b.items() if v is not None and k != "marca"]) >= 3


def build_all() -> dict:
    """Genera y cachea el PPT de cada marca con datos suficientes."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    ok, skipped, failed = 0, [], []
    for b in RAW_BRANDS:
        nombre = b["marca"]
        if not _has_enough_data(b):
            skipped.append(nombre)
            continue
        try:
            with open(cache_path(nombre), "wb") as f:
                f.write(generate_ppt(nombre))
            ok += 1
        except Exception as e:  # noqa: BLE001 — reportar y seguir con el resto
            failed.append((nombre, str(e)))
    return {"ok": ok, "skipped": skipped, "failed": failed}


if __name__ == "__main__":
    r = build_all()
    print(f"[precache] Generados: {r['ok']} | "
          f"Omitidos (datos insuficientes): {len(r['skipped'])} | "
          f"Fallidos: {len(r['failed'])}")
    if r["skipped"]:
        print(f"[precache] Omitidos: {', '.join(r['skipped'])}")
    for nombre, err in r["failed"]:
        print(f"[precache] FALLO {nombre}: {err}")
