"""Genera un reel vertical del veredicto de un activo, dibujado de cero.

  python make-ig-reel.py            # AAPL
  python make-ig-reel.py GGAL
  python make-ig-reel.py BTC crypto

Sale ig/reels/<simbolo>-<fecha>.mp4 (1080x1920, H.264 + AAC), listo para
publicarse con el workflow "Instagram diario de Verdikt" pasandole la ruta.

NO muestra la app: todo lo que se ve esta dibujado a partir de la respuesta de
/verdict/<clase>/<simbolo>, el mismo endpoint que usa el producto. Dos intentos
previos con capturas de pantalla no funcionaron (un mockup de telefono recorta y
a sangre sigue siendo una captura), asi que la escena es propia.

Tres pasos, cada uno en su archivo bajo ig/reel/:
  build_data.py  pide el veredicto y lo deja como data.js
  render.js      posiciona scene.html en t = f/30 y captura cada frame nativo
  music.py       sintetiza la pista, con los golpes en las marcas de la escena

Hace falta, una sola vez:
  pip install imageio-ffmpeg      (trae un ffmpeg con H.264; el de Playwright no)
  npm install playwright && npx playwright install chromium
En los runners de GitHub Actions ffmpeg ya viene, asi que alli alcanza Playwright.
"""
import datetime
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
REEL = os.path.join(RAIZ, "ig", "reel")
FRAMES = os.path.join(REEL, "frames")
FPS = 30


def ffmpeg() -> str:
    """El ffmpeg del sistema si esta; si no, el que empaqueta imageio-ffmpeg."""
    hallado = shutil.which("ffmpeg")
    if hallado:
        return hallado
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("Falta ffmpeg. Instalalo o corre: pip install imageio-ffmpeg")


def paso(titulo, *cmd, cwd=None):
    print(f"\n== {titulo}")
    r = subprocess.run(cmd, cwd=cwd or RAIZ)
    if r.returncode:
        sys.exit(f"fallo: {titulo}")


def main():
    sym = (sys.argv[1] if len(sys.argv) > 1 else "AAPL").upper()
    clase = sys.argv[2] if len(sys.argv) > 2 else "stock"

    paso("datos del veredicto", sys.executable,
         os.path.join(REEL, "build_data.py"), sym, clase)
    paso("musica", sys.executable, os.path.join(REEL, "music.py"), cwd=REEL)
    paso("frames", "node", os.path.join(REEL, "render.js"), cwd=REEL)

    salida = os.path.join(RAIZ, "ig", "reels",
                          f"{sym.lower()}-{datetime.date.today():%Y-%m-%d}.mp4")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    paso("encode", ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
         "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%04d.png"),
         "-i", os.path.join(REEL, "track.wav"),
         "-c:v", "libx264", "-preset", "slow", "-crf", "19",
         "-pix_fmt", "yuv420p",            # sin esto Instagram lo rechaza
         "-c:a", "aac", "-b:a", "160k", "-shortest",
         "-movflags", "+faststart", salida)

    # Los frames sueltos son ~600 PNG de 1080x1920: no van al repo.
    shutil.rmtree(FRAMES, ignore_errors=True)
    print(f"\nlisto: {os.path.relpath(salida, RAIZ)}")
    print("falta el caption: dejalo en el mismo nombre con extension .txt")


if __name__ == "__main__":
    main()
