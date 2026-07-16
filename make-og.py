# Imagen social (og:image) 1200x630 para verdikt.finance: la V verde de la
# marca (misma geometría que el ícono de la app) + wordmark + tagline, sobre
# el fondo oscuro de la landing. Se dibuja a 2x y se baja con LANCZOS.
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (5, 6, 8)            # #050608 (fondo de la landing)
TILE = (11, 14, 20)       # #0B0E14 (fondo del ícono)
BORDER = (35, 41, 57)     # #232939
GREEN = (47, 191, 113)    # #2FBF71
TEXT = (237, 239, 244)    # #EDEFF4
DIM = (138, 148, 166)     # #8A94A6

S = 2
W, H = 1200 * S, 630 * S
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

mono_b = ImageFont.truetype(r"C:\Windows\Fonts\consolab.ttf", 74 * S)
mono_s = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 26 * S)
sans = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 40 * S)

# --- Tile con la V (misma receta que _draw_icon de pwa_setup.py) -------------
ts = 190 * S                       # lado del tile
tx, ty = (W - ts) // 2, 96 * S     # posición (centrado, arriba)
d.rounded_rectangle([tx, ty, tx + ts, ty + ts], radius=ts * 0.22, fill=TILE,
                    outline=BORDER, width=2 * S)
m = int(ts * 0.26)
cw = ch = ts - 2 * m
w = int(ts * 0.105)
top_l = (tx + m + cw * 0.06, ty + m + ch * 0.08)
top_r = (tx + ts - m - cw * 0.06, ty + m + ch * 0.08)
bottom = (tx + ts / 2, ty + ts - m - ch * 0.04)
d.line([top_l, bottom], fill=GREEN, width=w)
d.line([bottom, top_r], fill=GREEN, width=w)
for (x, y) in (top_l, top_r, bottom):
    d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=GREEN)

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
