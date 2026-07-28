"""Genera el reel vertical del veredicto de un activo, dibujado de cero.

  python make-ig-reel.py            # AAPL
  python make-ig-reel.py GGAL
  python make-ig-reel.py BTC crypto

Deja dos archivos hermanos en ig/reels/:
  <simbolo>-<fecha>.mp4   1080x1920, H.264 + AAC, 20s
  <simbolo>-<fecha>.txt   el caption, derivado de los MISMOS datos

y el puntero ig/media/reel_video.txt con la ruta, que es lo que despues lee el
workflow para publicarlo.

NO muestra la app: todo esta dibujado a partir de la respuesta de
/verdict/<clase>/<simbolo>, el mismo endpoint que usa el producto. Dos intentos
con capturas de pantalla no funcionaron (un mockup de telefono recorta, y a
sangre sigue siendo una captura), asi que la escena es propia.

Tres pasos, cada uno en su archivo bajo ig/reel/:
  build_data.py  pide el veredicto, deja data.js y arma el caption
  render.js      posiciona scene.html en t = f/30 y captura cada frame nativo
  music.py       sintetiza la pista, con los golpes en las marcas de la escena

Hace falta, una sola vez:
  pip install imageio-ffmpeg      (trae un ffmpeg con H.264; el de Playwright no)
  npm install playwright && npx playwright install chromium
Las dos cosas hacen falta tambien en CI: la imagen de ubuntu-latest no trae
ffmpeg.
"""
import datetime
import importlib.util
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
REEL = os.path.join(RAIZ, "ig", "reel")
FRAMES = os.path.join(REEL, "frames")
SALIDA = os.path.join(RAIZ, "ig", "reels")
PUNTERO = os.path.join(RAIZ, "ig", "media", "reel_video.txt")
FPS = 30
KEEP = 3  # cuantos reels viejos se conservan: cada uno pesa ~3 MB

_spec = importlib.util.spec_from_file_location("build_data", os.path.join(REEL, "build_data.py"))
bd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bd)


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
    if subprocess.run(cmd, cwd=cwd or RAIZ).returncode:
        sys.exit(f"fallo: {titulo}")


def _prune():
    """Deja solo los ultimos KEEP reels, con su caption. Sin esto el repo suma
    3 MB por dia."""
    mp4s = sorted(f for f in os.listdir(SALIDA) if f.endswith(".mp4"))
    for viejo in mp4s[:-KEEP]:
        for f in (viejo, viejo[:-4] + ".txt"):
            try:
                os.remove(os.path.join(SALIDA, f))
                print("  borrado por antiguedad:", f)
            except OSError:
                pass


# Voz elegida el 2026-07-28 escuchando tres candidatas. El nombre del modelo
# dice "sharvard" y no indica el genero: es una voz MASCULINA, aunque el
# archivo de prueba se llamaba "mujer" por un error mio al rotularlo.
VOZ = "es_ES-sharvard-medium"


def narrar(d: dict, mp4: str) -> None:
    """Le agrega la voz en off al reel ya encodeado, pisando el archivo.

    Es BEST EFFORT a proposito: si falta piper, no esta el modelo o la sintesis
    falla, el reel queda con su musica y se publica igual. Perder la voz es un
    reel mas pobre; perder el reel es un dia sin posteo."""
    voces = os.path.join(REEL, "voces")
    try:
        _spec_n = importlib.util.spec_from_file_location(
            "narrar", os.path.join(REEL, "narrar.py"))
        nar = importlib.util.module_from_spec(_spec_n)
        _spec_n.loader.exec_module(nar)

        seg = nar.guion(d)
        pistas = nar.sintetizar(seg, VOZ, voces, os.path.join(REEL, "voz_tmp"))
        con_voz = mp4 + ".voz.mp4"
        nar.mezclar(mp4, pistas, con_voz)
        os.replace(con_voz, mp4)
        habla = sum(p[2] for p in pistas)
        print(f"== voz  {len(pistas)} lineas, {habla:.1f}s de habla")
    except Exception as e:
        print(f"::warning::sin voz en off ({type(e).__name__}: {e}). "
              f"El reel sale igual, con su musica.")
    finally:
        shutil.rmtree(os.path.join(REEL, "voz_tmp"), ignore_errors=True)


def main():
    sym = (sys.argv[1] if len(sys.argv) > 1 else "AAPL").upper()
    clase = sys.argv[2] if len(sys.argv) > 2 else "stock"

    print(f"== veredicto de {sym} ({clase})")
    d = bd.preparar(bd.pedir(sym, clase))
    bd.escribir_datajs(d)
    print(f"  {d['score']}/100 {d['verdict']} · razones {len(d['razones'])}/{d['total_razones']}")

    paso("musica", sys.executable, os.path.join(REEL, "music.py"), cwd=REEL)
    paso("frames", "node", os.path.join(REEL, "render.js"), cwd=REEL)

    os.makedirs(SALIDA, exist_ok=True)
    base = f"{sym.lower()}-{datetime.date.today():%Y-%m-%d}"
    mp4 = os.path.join(SALIDA, base + ".mp4")
    paso("encode", ffmpeg(), "-y", "-hide_banner", "-loglevel", "error",
         "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%04d.png"),
         "-i", os.path.join(REEL, "track.wav"),
         "-c:v", "libx264", "-preset", "slow", "-crf", "19",
         "-pix_fmt", "yuv420p",            # sin esto Instagram lo rechaza
         "-c:a", "aac", "-b:a", "160k", "-shortest",
         "-movflags", "+faststart", mp4)

    narrar(d, mp4)

    with open(os.path.join(SALIDA, base + ".txt"), "w", encoding="utf-8") as f:
        f.write(bd.caption(d))

    shutil.rmtree(FRAMES, ignore_errors=True)   # ~600 PNG de 1080x1920
    _prune()

    os.makedirs(os.path.dirname(PUNTERO), exist_ok=True)
    rel = os.path.relpath(mp4, RAIZ).replace("\\", "/")
    with open(PUNTERO, "w", encoding="utf-8") as f:
        f.write(rel)
    print(f"\nlisto: {rel}")


if __name__ == "__main__":
    main()
