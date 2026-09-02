"""Genera la biblioteca de fondos de las placas — UNA sola vez.

  OPENAI_API_KEY=... python ig/placa/fondos/generar.py [cantidad]

Fondos oscuros, cinematograficos, SIN texto. Se revisan a mano y quedan
commiteados; las placas los rotan por fecha. Volver a correr esto solo si se
quiere renovar la tanda (pisa fondo-N.png)."""
import io
import os
import sys

from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, RAIZ)
from ig.ia.cliente import imagenes  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350

_ESCENAS = [
    "a moody out-of-focus night city skyline of glass towers seen at dusk, "
    "deep teal-blue, warm window lights glowing as soft bokeh, atmospheric haze",
    "a modern glass office tower facade at blue hour, shot from below, "
    "reflections of clouds in the windows, cool blue-grey with soft highlights",
    "a wide dark marble and steel lobby with dramatic side lighting, deep "
    "shadows but clear architectural forms, cinematic, cool tones",
    "abstract flowing dark topographic contour lines in slate blue and charcoal "
    "with a soft emerald glow along one edge, depth and dimension",
    "a blurred financial trading floor at night from a distance, rows of "
    "monitors as soft cyan-green rectangular glows, atmospheric depth, cinematic",
    "dark calm water at night reflecting distant city lights, deep blue-black "
    "with warm and green reflections rippling, vast and moody",
    "an abstract 3d grid of thin luminous lines receding toward a vanishing "
    "point over a dark plane, faint green horizon glow, sense of scale",
]

_COMUN = (
    " Vertical 9:16 photograph. Dark and moody but with CLEAR VISIBLE DETAIL and "
    "depth — not pure black, mid-dark with readable midtones and soft "
    "highlights. Cinematic color grade, slight film grain. Empty darker areas "
    "top and bottom for text. ABSOLUTELY NO text, letters, numbers, logos, "
    "people, faces, charts, or UI."
)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else len(_ESCENAS)
    for i, escena in enumerate(_ESCENAS[:n], 1):
        print(f"[{i}/{n}] {escena[:60]}...")
        try:
            raw = imagenes(escena + _COMUN, n=1, size="1024x1536")[0]
        except Exception as e:
            print(f"  fallo: {e}")
            continue
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        escala = max(W / im.width, H / im.height)
        im = im.resize((round(im.width * escala), round(im.height * escala)),
                       Image.LANCZOS)
        x = (im.width - W) // 2
        y = (im.height - H) // 2
        im = im.crop((x, y, x + W, y + H))
        ruta = os.path.join(AQUI, f"fondo-{i}.png")
        im.save(ruta, optimize=True)
        print(f"  -> {ruta}")


if __name__ == "__main__":
    main()
