"""Genera una placa de info del Instagram de Verdikt (HTML + Playwright).

  python make-ig-placa.py veredicto            # nro 1 del ranking del dia
  python make-ig-placa.py veredicto NVDA stock # forzar un activo

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
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
PLACA = os.path.join(RAIZ, "ig", "placa")
SALIDA = os.path.join(PLACA, "out")
PUNTERO = os.path.join(RAIZ, "ig", "media", "placa_render.txt")

_spec = importlib.util.spec_from_file_location(
    "placa_build", os.path.join(PLACA, "build.py"))
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)


def _run(titulo, *cmd, cwd=None, fatal=True):
    print(f"\n== {titulo}")
    r = subprocess.run(cmd, cwd=cwd or RAIZ)
    if r.returncode and fatal:
        sys.exit(f"fallo: {titulo}")
    return r.returncode == 0


def main():
    tipo = sys.argv[1] if len(sys.argv) > 1 else "veredicto"
    if tipo != "veredicto":
        sys.exit(f"tipo '{tipo}' todavia no implementado (fase 2)")
    sym = sys.argv[2] if len(sys.argv) > 2 else ""
    clase = sys.argv[3] if len(sys.argv) > 3 else ""

    info = build.build_veredicto(sym, clase)

    # Captura de la app: si falla, la plantilla usa el placeholder.
    ok = _run("captura de la app", "node", os.path.join(PLACA, "capturar.js"),
              info["symbol"], info["clase"], fatal=False)
    if not ok:
        screen = os.path.join(PLACA, "screen.png")
        if os.path.exists(screen):
            os.remove(screen)
        print("::warning::sin captura de la app; la placa sale con placeholder")

    os.makedirs(SALIDA, exist_ok=True)
    base = f"{tipo}-{datetime.date.today():%Y-%m-%d}"
    png = os.path.join(SALIDA, base + ".png")
    _run("render", "node", os.path.join(PLACA, "render.js"), png)

    with open(os.path.join(PLACA, "caption.txt"), encoding="utf-8") as f:
        cap = f.read()
    with open(os.path.join(SALIDA, base + ".txt"), "w", encoding="utf-8") as f:
        f.write(cap)

    os.makedirs(os.path.dirname(PUNTERO), exist_ok=True)
    rel = os.path.relpath(png, RAIZ).replace("\\", "/")
    with open(PUNTERO, "w", encoding="utf-8") as f:
        f.write(rel)
    print(f"\nlisto: {rel}")


if __name__ == "__main__":
    main()
