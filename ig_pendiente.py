"""Reel diario con revision humana: GENERA y ENCOLA, no publica.

Reemplaza el viejo ig-reels.yml (3 reels/dia, automatico, mismo formato). Ahora
es 1 reel/dia que pasa por el ojo del usuario:

  generar   -> elige el activo (salteando los que no tienen datos), renderiza el
               reel, pide a la IA el copy y 3 caratulas, y deja todo en
               ig/pendientes/<fecha ART>/ para revisar desde el celular. NO
               publica. Si no hay OPENAI_API_KEY, encola igual con caption
               templado y una caratula de plantilla.

  aprobar   -> lee ig/pendientes/<fecha>/APROBAR.md (lo edita el usuario y lo
               commitea). Segun eso: publica el reel con la caratula elegida, o
               lo descarta. Recien ahi avanza la rotacion.

El MP4 no se commitea (va al release "media", como antes). Las caratulas PNG
si, que pesan poco y son lo que el usuario mira en GitHub.

Ver el plan en .claude/plans y [[verdikt-instagram]]."""
import argparse
import datetime
import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import ig_publish

RAIZ = os.path.dirname(os.path.abspath(__file__))
PEND_DIR = os.path.join(RAIZ, "ig", "pendientes")
MEDIA_DIR = os.path.join(RAIZ, "ig", "media")
REEL_LAST_FILE = os.path.join(MEDIA_DIR, "last_reel.txt")
REEL_VIDEO_FILE = os.path.join(MEDIA_DIR, "reel_video.txt")
PEND_PTR = os.path.join(MEDIA_DIR, "pendiente_dir.txt")  # gitignored
KEEP = 5  # carpetas pendientes a conservar


def _load(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

bd = _load("build_data", os.path.join(RAIZ, "ig", "reel", "build_data.py"))
rotacion = _load("rotacion", os.path.join(RAIZ, "ig", "reel", "rotacion.py"))


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _write(path, val):
    with open(path, "w", encoding="utf-8") as f:
        f.write(val)


def dia_art():
    return (datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(hours=3)).strftime("%Y-%m-%d")


# --------------------------------------------------------------- generar -------
def _elegir_activo():
    clase, sym, muertos = rotacion.siguiente_con_datos(_read(REEL_LAST_FILE))
    if muertos:
        _write(REEL_LAST_FILE, muertos[-1])
        print("puntero adelantado sobre:", ", ".join(muertos))
    return clase, sym


def _renderizar(sym, clase):
    """Corre make-ig-reel.py (Playwright + ffmpeg). Devuelve la ruta del mp4."""
    r = subprocess.run([sys.executable, os.path.join(RAIZ, "make-ig-reel.py"),
                        sym, clase], cwd=RAIZ)
    if r.returncode:
        sys.exit(f"fallo el render de {sym}")
    mp4 = _read(REEL_VIDEO_FILE)
    if not mp4 or not os.path.exists(os.path.join(RAIZ, mp4)):
        sys.exit("make-ig-reel.py no dejo el mp4")
    return mp4


def _copy_y_caratulas(d, out_dir):
    """Devuelve (caption, lista_de_caratulas, copy_dict|None). Best effort:
    si la IA falla, caption templado + caratula de plantilla."""
    from ig.ia import caratula, redaccion
    from ig.ia.cliente import IAError

    copy = None
    try:
        copy = redaccion.redactar(d)
        print("copy IA:", copy["gancho"], "|", copy["titular"])
    except IAError as e:
        print(f"::warning::sin copy de IA ({e}). Va el caption templado.")

    if copy:
        cierre = _cierre_caption(d)
        caption = copy["caption_cuerpo"].rstrip() + "\n\n" + cierre
    else:
        caption = bd.caption(d)

    titular = (copy or {}).get("titular", "")
    # La de plantilla se genera SIEMPRE: es la opcion "caratula: 0" y el
    # respaldo si no hay otra cosa.
    plantilla = caratula.plantilla(
        d, os.path.join(out_dir, "cover-plantilla.png"), titular=titular)
    caratulas = []
    # Las caratulas de IA (modelo pago, o Pollinations gratis pero mediocre)
    # son opt-in: por defecto solo va la plantilla y el usuario pega la suya.
    # Se prenden con la var de repo IA_CARATULAS=1 (poner cuando OpenAI tenga
    # billing andando, o para usar Pollinations).
    if copy and os.environ.get("IA_CARATULAS", "").strip():
        try:
            caratulas = caratula.generar(d, copy["brief_caratula"], out_dir,
                                         titular=titular)
            print(f"{len(caratulas)} caratulas de IA + plantilla")
        except IAError as e:
            print(f"::warning::sin caratulas de IA ({e}). Queda la de plantilla.")
    return caption, (caratulas or [plantilla]), copy


def _cierre_caption(d):
    """El pie fijo del caption, calcado del final de build_data.caption()."""
    return "\n".join([
        "El score va de 0 a 100 y resume el panorama tecnico del activo. "
        "Se recalcula todos los dias con el cierre.",
        "",
        "Analiza cualquier accion, CEDEAR o cripto en app.verdikt.finance",
        "",
        d.get("disclaimer") or ("Informacion educativa, no es asesoramiento "
                                "financiero. Invertis bajo tu propia responsabilidad."),
        "",
        bd.HASHTAGS,
    ])


def cmd_generar():
    clase, sym = _elegir_activo()
    print(f"Reel de hoy: {sym} ({clase})")
    d = bd.preparar(bd.pedir(sym, clase))
    print(f"  {d['score']}/100 {d['verdict']}")

    fecha = dia_art()
    out_dir = os.path.join(PEND_DIR, fecha)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    mp4 = _renderizar(sym, clase)

    caption, caratulas, copy = _copy_y_caratulas(d, out_dir)
    _write(os.path.join(out_dir, "caption.txt"), caption)
    _write(os.path.join(out_dir, "asset.txt"), rotacion.clave(clase, sym))
    _write(os.path.join(out_dir, "reel_local.txt"), mp4)
    if copy:
        _write(os.path.join(out_dir, "copy.json"),
               json.dumps(copy, ensure_ascii=False, indent=2))

    nombres = [os.path.basename(c) for c in caratulas]
    _write(os.path.join(out_dir, "APROBAR.md"), _aprobar_md(d, sym, clase, caption, nombres))

    os.makedirs(MEDIA_DIR, exist_ok=True)
    _write(PEND_PTR, fecha)
    _prune()
    print(f"\nencolado en ig/pendientes/{fecha}/  ({len(caratulas)} caratula(s))")
    print("falta: subir el mp4 al release y commitear la carpeta")


def _aprobar_md(d, sym, clase, caption, nombres):
    ia = [n for n in nombres if n.startswith("cover-") and n != "cover-plantilla.png"]
    ops = ("0 (plantilla) · " +
           " · ".join(n.split("-")[1].split(".")[0] for n in ia) if ia
           else "0 (plantilla)")
    preview = "\n".join("    " + l for l in caption.splitlines()[:6])
    return (
        "caratula: 0\n"
        "descartar: no\n"
        "\n"
        "<!--\n"
        f"  caratula:  {ops}\n"
        "             O pegá tu propia carátula en esta carpeta como\n"
        "             cover-mia.png y poné 'caratula: mia'.\n"
        "  descartar: 'si' = no publicar hoy, saltear este activo.\n"
        "  Guardá y commiteá: el reel se publica solo en ~2 min.\n"
        "-->\n"
        "\n"
        f"# {sym} · {d['verdict']} {d['score']}/100\n"
        f"\n{clase} — {d['name']}\n"
        f"\nArchivos de carátula: {', '.join(nombres)}\n"
        "\nCaption:\n\n"
        f"{preview}\n"
    )


def _prune():
    for p in sorted(glob.glob(os.path.join(PEND_DIR, "20*")))[:-KEEP]:
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)


# --------------------------------------------------------------- aprobar -------
def _carpeta_pendiente():
    """La carpeta ig/pendientes/<fecha> mas nueva que todavia no se resolvio."""
    for p in sorted(glob.glob(os.path.join(PEND_DIR, "20*")), reverse=True):
        if os.path.isdir(p) and not os.path.exists(os.path.join(p, ".publicado")):
            return p
    return None


def _parse_aprobar(ruta):
    """Lee solo el bloque de claves del encabezado (hasta la primera linea en
    blanco o el primer comentario): asi el texto de ayuda del <!-- --> no pisa
    lo que puso el usuario. Devuelve (caratula:str, descartar:bool)."""
    caratula, descartar = "0", False
    for linea in _read(ruta).splitlines():
        s = linea.strip()
        if not s or s.startswith("<!--"):
            break
        k, sep, v = s.partition(":")
        if not sep:
            continue
        k, v = k.strip().lower(), v.strip()
        if k == "caratula" and v:
            caratula = v
        elif k == "descartar":
            descartar = v.lower() in ("si", "sí", "true", "yes")
    return caratula, descartar


def _elegir_cover(carpeta, valor):
    """`valor` puede ser 0 (plantilla), 1/2/3 (cover-N.png) o un nombre libre
    para la caratula propia que el usuario dejo en la carpeta (acepta 'mia',
    'mia.png' o 'cover-mia.png'). Devuelve el nombre de archivo o None."""
    hay = {os.path.basename(p) for p in glob.glob(os.path.join(carpeta, "*.png"))}
    v = valor.strip().lower()
    if v in ("0", "", "plantilla"):
        return "cover-plantilla.png" if "cover-plantilla.png" in hay else None
    candidatos = [v, f"{v}.png", f"cover-{v}.png",
                  f"cover-{v}.png".replace(".png.png", ".png")]
    for c in candidatos:
        if c in hay:
            return c
    return "cover-plantilla.png" if "cover-plantilla.png" in hay else None


def cmd_aprobar(video_url, cover_base, dry_run):
    carpeta = _carpeta_pendiente()
    if not carpeta:
        print("No hay carpeta pendiente sin resolver.")
        return 0
    print("carpeta:", os.path.relpath(carpeta, RAIZ))

    valor, descartar = _parse_aprobar(os.path.join(carpeta, "APROBAR.md"))
    asset = _read(os.path.join(carpeta, "asset.txt"))

    if descartar:
        _write(os.path.join(carpeta, ".publicado"), "descartado " + dia_art())
        if asset and not dry_run:
            _write(REEL_LAST_FILE, asset)
            print("descartado; rotacion avanzada a", asset)
        return 0

    cover = _elegir_cover(carpeta, valor)
    print("caratula:", cover or "(ninguna, la elige Instagram)")

    if not video_url:
        video_url = _read(os.path.join(carpeta, "reel_url.txt"))
    if not video_url:
        print("Falta la URL del reel (reel_url.txt).")
        return 1
    caption = _read(os.path.join(carpeta, "caption.txt"))
    cover_url = None
    if cover and cover_base:
        cover_url = f"{cover_base.rstrip('/')}/{os.path.basename(carpeta)}/{cover}"

    mid = ig_publish.publish_reel(video_url, caption, cover_url=cover_url,
                                  dry_run=dry_run)
    print("reel publicado:", mid)
    if not dry_run:
        _write(os.path.join(carpeta, ".publicado"), f"{mid} {dia_art()}")
        if asset:
            _write(REEL_LAST_FILE, asset)
            print("rotacion avanzada a", asset)
    return 0


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generar")
    p = sub.add_parser("aprobar")
    p.add_argument("--video-url", default="")
    p.add_argument("--cover-base", default="",
                   help="prefijo raw hasta ig/pendientes, sin la fecha")
    p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.cmd == "generar":
        sys.exit(cmd_generar() or 0)
    if a.cmd == "aprobar":
        sys.exit(cmd_aprobar(a.video_url, a.cover_base, a.dry_run))


if __name__ == "__main__":
    main()
