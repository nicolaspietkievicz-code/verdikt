"""Orquestador del posteo diario de Instagram de Verdikt.

Dos subcomandos (el workflow los llama en orden, con el commit/push en el medio
para que la imagen tenga URL publica antes de publicar):

  generate  -> pide los cambios de veredicto del dia; si NO hay, no deja nada
               (el workflow lo detecta y no publica). Si hay, dibuja la imagen
               fechada en ig/media/, escribe el caption y deja punteros en
               ig/media/latest_image.txt y ig/media/latest_caption.txt.

  publish   -> toma --image-url (la URL publica del PNG ya pusheado) y publica
               con el caption guardado, via ig_publish.publish().

Asi el generar y el publicar quedan separados por el push (Instagram baja la
imagen por URL, tiene que estar viva antes)."""
import argparse
import glob
import importlib.util
import os
import sys

import ig_publish

# El generador vive en make-ig-cambios.py (con guiones, no importable directo).
_gen_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "make-ig-cambios.py")
_spec = importlib.util.spec_from_file_location("make_ig_cambios", _gen_path)
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)

MEDIA_DIR = "ig/media"
KEEP = 14  # cuantas imagenes viejas conservar (para no inflar el repo)

VERDICT_ES = {
    "COMPRA": "COMPRA", "ACUMULAR": "ACUMULAR", "NEUTRAL": "NEUTRAL",
    "CAUTELA": "CAUTELA", "EVITAR": "EVITAR",
}
HASHTAGS = ("#inversiones #cedears #cripto #trading #bolsa #acciones "
            "#finanzas #mercados #argentina #análisis")


def _fecha_larga(dd: str) -> str:
    mes = {"01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
           "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
           "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"}
    if len(dd) == 10:
        return f"{int(dd[8:10])} de {mes.get(dd[5:7], '')} de {dd[:4]}"
    return dd


def build_caption(data: dict) -> str:
    items = data.get("items", [])
    dd = data.get("date", "")
    lines = [f"Hoy cambiaron de veredicto — {_fecha_larga(dd)}", ""]
    for it in items[:6]:
        prev = VERDICT_ES.get(it["prev_verdict"], it["prev_verdict"])
        new = VERDICT_ES.get(it["verdict"], it["verdict"])
        lines.append(f"{it['symbol']}: {prev} → {new} ({it['score']}/100)")
    lines += [
        "",
        "El score va de 0 a 100 y resume el panorama técnico de cada activo. "
        "No es una recomendación de inversión.",
        "",
        "Analizá cualquier acción, CEDEAR o cripto en app.verdikt.finance",
        "",
        HASHTAGS,
    ]
    return "\n".join(lines)


def _prune():
    old = sorted(glob.glob(os.path.join(MEDIA_DIR, "cambios-*.png")))
    for p in old[:-KEEP]:
        try:
            os.remove(p)
        except OSError:
            pass


def cmd_generate():
    data = gen._fetch_changes()
    items = data.get("items", [])
    if not items:
        print("Sin cambios de veredicto hoy: no se genera ni se publica.")
        # Aseguramos que no queden punteros viejos de una corrida anterior.
        for f in ("latest_image.txt", "latest_caption.txt"):
            p = os.path.join(MEDIA_DIR, f)
            if os.path.exists(p):
                os.remove(p)
        return 0

    os.makedirs(MEDIA_DIR, exist_ok=True)
    dd = data.get("date") or ""
    stamp = dd if len(dd) == 10 else "hoy"
    img_path = os.path.join(MEDIA_DIR, f"cambios-{stamp}.png")
    gen.generate(out_path=img_path, data=data)

    cap = build_caption(data)
    with open(os.path.join(MEDIA_DIR, "latest_image.txt"), "w", encoding="utf-8") as f:
        f.write(img_path.replace("\\", "/"))
    with open(os.path.join(MEDIA_DIR, "latest_caption.txt"), "w", encoding="utf-8") as f:
        f.write(cap)
    _prune()
    print("Imagen:", img_path)
    print("Caption:\n" + cap)
    return 0


def cmd_publish(image_url: str, dry_run: bool):
    cap_file = os.path.join(MEDIA_DIR, "latest_caption.txt")
    if not os.path.exists(cap_file):
        print("No hay caption (nada que publicar).")
        return 0
    with open(cap_file, encoding="utf-8") as f:
        caption = f.read()
    mid = ig_publish.publish(image_url, caption, dry_run=dry_run)
    print("publicado:", mid)
    return 0


def main():
    # La consola de Windows es cp1252 y revienta con → y acentos; en CI ya es
    # utf-8. Forzamos utf-8 tolerante para poder loguear el caption sin romper.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generate")
    p = sub.add_parser("publish")
    p.add_argument("--image-url", required=True)
    p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.cmd == "generate":
        sys.exit(cmd_generate())
    if a.cmd == "publish":
        sys.exit(cmd_publish(a.image_url, a.dry_run))


if __name__ == "__main__":
    main()
