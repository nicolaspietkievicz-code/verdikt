# Logo cuadrado (512x512) para datos estructurados (Organization.logo de
# schema.org) y para donde haga falta un ícono de marca real, no la og.png
# rectangular. Misma V verde y mismo tile que el ícono de la app. Se dibuja
# a 2x y se baja con LANCZOS.
from pathlib import Path

from PIL import Image, ImageDraw

BG = (5, 6, 8)            # #050608 (fondo de la landing)
TILE = (11, 14, 20)       # #0B0E14 (fondo del icono)
BORDER = (35, 41, 57)     # #232939
GREEN = (47, 191, 113)    # #2FBF71

S = 2
W = H = 512 * S
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# --- Tile con la V (misma receta que _draw_icon de pwa_setup.py) -------------
ts = 380 * S                          # lado del tile
tx, ty = (W - ts) // 2, (H - ts) // 2  # centrado
d.rounded_rectangle([tx, ty, tx + ts, ty + ts], radius=ts * 0.22, fill=TILE,
                    outline=BORDER, width=3 * S)
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

img = img.resize((512, 512), Image.LANCZOS)
img.save(Path(__file__).parent / "img" / "logo.png", optimize=True)
print("logo.png lista")
