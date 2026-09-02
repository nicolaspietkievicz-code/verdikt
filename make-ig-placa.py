"""Genera una placa de info del Instagram de Verdikt (HTML + Playwright).

  python make-ig-placa.py hoy                  # la que toca hoy (calendario)
  python make-ig-placa.py veredicto            # nro 1 del ranking del dia
  python make-ig-placa.py veredicto NVDA stock # forzar un activo
  python make-ig-placa.py termometro
  python make-ig-placa.py cambios
  python make-ig-placa.py educativa

'hoy' elige por calendario (hora argentina):
  viernes -> termometro   domingo -> educativa
  entre semana -> 'cambios' si hoy hubo cambios de veredicto, si no 'veredicto'.

Deja en ig/placa/out/:
  <tipo>-<fecha>.png    1080x1350
  <tipo>-<fecha>.txt    el caption

Tres pasos, cada uno en su archivo bajo ig/placa/:
  build.py      pide los datos, deja data.js y el caption
  capturar.js   screenshot real de la app para el mockup (best effort)
  render.js     carga plantilla.html y saca el PNG final

Hace falta (igual que el reel): npm install playwright + chromium.
"""
import datetime
import importlib.util
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
PLACA = os.path.join(RAIZ, "ig", "placa")
SALIDA = os.path.join(PLACA, "out")
MEDIA = os.path.join(RAIZ, "ig", "media")
# El PNG y el caption del dia, con nombre fijo, SI se commitean: son lo que el
# workflow sube y lo que Instagram baja por raw URL. Se pisan cada dia.
PLACA_HOY_PNG = os.path.join(MEDIA, "placa_hoy.png")
PLACA_HOY_CAP = os.path.join(MEDIA, "placa_hoy.txt")
PUNTERO = os.path.join(MEDIA, "placa_render.txt")

_spec = importlib.util.spec_from_file_location(
    "placa_build", os.path.join(PLACA, "build.py"))
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

TIPOS = ("veredicto", "termometro", "cambios", "educativa")


def _tipo_de_hoy() -> str:
    import datetime
    import json
    import urllib.request
    art = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3)
    dow = art.weekday()  # lun=0 ... dom=6
    if dow == 4:
        return "termometro"
    if dow == 6:
        return "educativa"
    try:
        with urllib.request.urlopen(
                "https://app.verdikt.finance/verdict-changes", timeout=30) as r:
            if json.loads(r.read()).get("items"):
                return "cambios"
    except Exception as e:
        print(f"  no se pudo mirar los cambios ({e}); va veredicto")
    return "veredicto"


def _run(titulo, *cmd, fatal=True):
    print(f"\n== {titulo}")
    r = subprocess.run(cmd, cwd=RAIZ)
    if r.returncode and fatal:
        sys.exit(f"fallo: {titulo}")
    return r.returncode == 0


def main():
    tipo = sys.argv[1] if len(sys.argv) > 1 else "hoy"
    extra = sys.argv[2:]
    if tipo == "hoy":
        tipo = _tipo_de_hoy()
        print(f"== hoy toca: {tipo}")
    if tipo not in TIPOS:
        sys.exit(f"tipo desconocido: {tipo} (usar: hoy, {', '.join(TIPOS)})")

    info = build.build(tipo, *extra)

    screen = (info or {}).get("screen")
    if screen:
        ok = _run("captura de la app", "node", os.path.join(PLACA, "capturar.js"),
                  screen, fatal=False)
        if not ok:
            p = os.path.join(PLACA, "screen.png")
            if os.path.exists(p):
                os.remove(p)
            print("::warning::sin captura de la app; la placa sale con placeholder")
    else:
        p = os.path.join(PLACA, "screen.png")
        if os.path.exists(p):
            os.remove(p)

    os.makedirs(SALIDA, exist_ok=True)
    base = f"{tipo}-{datetime.date.today():%Y-%m-%d}"
    png = os.path.join(SALIDA, base + ".png")
    _run("render", "node", os.path.join(PLACA, "render.js"), png)

    # El render sale a 2160x2700 (deviceScaleFactor 2). Instagram muestra a
    # 1080: se baja y se optimiza para que pese ~1/4.
    try:
        from PIL import Image
        im = Image.open(png)
        if im.width > 1080:
            im.resize((1080, 1350), Image.LANCZOS).save(png, optimize=True)
    except Exception as e:
        print(f"::warning::no se pudo bajar de escala ({e}); sale a tamaño completo")

    with open(os.path.join(PLACA, "caption.txt"), encoding="utf-8") as f:
        cap = f.read()
    with open(os.path.join(SALIDA, base + ".txt"), "w", encoding="utf-8") as f:
        f.write(cap)

    # Copia con nombre fijo, que es lo que se commitea y publica.
    os.makedirs(MEDIA, exist_ok=True)
    shutil.copyfile(png, PLACA_HOY_PNG)
    with open(PLACA_HOY_CAP, "w", encoding="utf-8") as f:
        f.write(cap)
    with open(PUNTERO, "w", encoding="utf-8") as f:
        f.write(tipo)
    print(f"\nlisto: {os.path.relpath(PLACA_HOY_PNG, RAIZ)} ({tipo})")


if __name__ == "__main__":
    main()
