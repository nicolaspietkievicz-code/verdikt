# Imagen social (og:image) 1200x630 para verdikt.finance: la V verde de la
# marca (misma geometría que el ícono de la app) + wordmark + tagline, sobre
# el fondo oscuro de la landing. Se dibuja a 2x y se baja con LANCZOS.
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (5, 6, 8)            # #050608 (fondo de la landing)
TILE = (11, 14, 20)       # #0B0E14 (fondo del ícono)
BORDER = (35, 41, 57)     # #232939
GREEN = (47, 191, 113)    # #2FBF71
GREEN_DIM = (30, 96, 66)  # #1E6042 (rama que cae)
TEXT = (237, 239, 244)    # #EDEFF4
DIM = (138, 148, 166)     # #8A94A6

S = 2
W, H = 1200 * S, 630 * S
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def draw_v(dr, ox, oy, side, green=GREEN, dim=GREEN_DIM):
    """Marca V-recuperacion dentro del cuadrado [ox, oy, ox+side]."""
    def P(fx, fy):
        return (ox + side * fx, oy + side * fy)

    lt = P(0.16, 0.30)
    bot = P(0.46, 0.86)
    end = P(0.78, 0.30)
    w = side * 0.11

    def cap(p, col):
        dr.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2],
                   fill=col)

    dr.line([lt, bot], fill=dim, width=int(round(w)))
    cap(lt, dim)
    cap(bot, dim)

    ang = math.atan2(end[1] - bot[1], end[0] - bot[0])
    head_len = side * 0.22
    head_w = side * 0.15
    tip = (end[0] + head_len * 0.5 * math.cos(ang),
           end[1] + head_len * 0.5 * math.sin(ang))
    bc = (tip[0] - head_len * math.cos(ang), tip[1] - head_len * math.sin(ang))
    px, py = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
    b1 = (bc[0] + px * head_w, bc[1] + py * head_w)
    b2 = (bc[0] - px * head_w, bc[1] - py * head_w)
    dr.line([bot, bc], fill=green, width=int(round(w)))
    cap(bot, green)
    dr.polygon([tip, b1, b2], fill=green)


mono_b = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 74 * S)
mono_s = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 26 * S)
sans = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 40 * S)

# --- Tile con la V (misma receta que _draw_icon de pwa_setup.py) -------------
ts = 190 * S                       # lado del tile
tx, ty = (W - ts) // 2, 96 * S     # posición (centrado, arriba)
d.rounded_rectangle([tx, ty, tx + ts, ty + ts], radius=ts * 0.22, fill=TILE,
                    outline=BORDER, width=2 * S)
draw_v(d, tx + ts * 0.14, ty + ts * 0.14, ts * 0.72)

# --- Wordmark VERDIKT_ con letterspacing, cursor verde -----------------------
word = "VERDIKT"
ls = 14 * S  # espacio extra entre letras
widths = [d.textlength(c, font=mono_b) for c in word]
cursor_w = d.textlength("_", font=mono_b)
total = sum(widths) + ls * (len(word) - 1) + ls + cursor_w
x = (W - total) / 2
y = ty + ts + 44 * S
for c, cw_ in zip(word, widths):
    d.text((x, y), c, font=mono_b, fill=TEXT)
    x += cw_ + ls
d.text((x, y), "_", font=mono_b, fill=GREEN)

# --- Tagline y dominio --------------------------------------------------------
tag = "¿Comprar, acumular o evitar? Un veredicto claro, de 0 a 100."
tw = d.textlength(tag, font=sans)
d.text(((W - tw) / 2, y + 116 * S), tag, font=sans, fill=DIM)

dom = "verdikt.finance"
dw = d.textlength(dom, font=mono_s)
d.text(((W - dw) / 2, H - 64 * S), dom, font=mono_s, fill=GREEN)

img = img.resize((1200, 630), Image.LANCZOS)
img.save(Path(__file__).parent / "img" / "og.png", optimize=True)
print("og.png lista")
