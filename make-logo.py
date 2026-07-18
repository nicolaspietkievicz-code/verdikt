# Logo cuadrado (512x512) para datos estructurados (Organization.logo de
# schema.org) y para donde haga falta un ícono de marca real, no la og.png
# rectangular. La "V" de Verdikt es una recuperacion en V: cae en verde
# apagado y rebota en verde brillante con una flecha. Mismo tile oscuro con
# cuadricula que el resto de la marca. Se dibuja a 3x y se baja con LANCZOS.
import math
from pathlib import Path

from PIL import Image, ImageDraw

BG = (5, 6, 8)            # #050608 (fondo de la landing)
TILE = (11, 14, 20)       # #0B0E14 (fondo del icono)
BORDER = (35, 41, 57)     # #232939
GRID = (24, 32, 46)       # lineas de la cuadricula de fondo
GREEN = (47, 191, 113)    # #2FBF71
GREEN_DIM = (30, 96, 66)  # #1E6042 (rama que cae)

S = 3
W = H = 512 * S
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


# --- Tile con cuadricula tenue de fondo --------------------------------------
ts = int(462 * S)                      # lado del tile (deja margen al borde)
tx, ty = (W - ts) // 2, (H - ts) // 2  # centrado
radius = ts * 0.16

tile = Image.new("RGB", (ts, ts), TILE)
td = ImageDraw.Draw(tile)
step = int(ts / 12)
x = 0
while x <= ts:
    td.line([(x, 0), (x, ts)], fill=GRID, width=S)
    x += step
y = 0
while y <= ts:
    td.line([(0, y), (ts, y)], fill=GRID, width=S)
    y += step
mask = Image.new("L", (ts, ts), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, ts, ts], radius=radius, fill=255)
img.paste(tile, (tx, ty), mask)
d.rounded_rectangle([tx, ty, tx + ts, ty + ts], radius=radius,
                    outline=BORDER, width=3 * S)

# --- La V-recuperacion dentro del tile ---------------------------------------
draw_v(d, tx + ts * 0.14, ty + ts * 0.14, ts * 0.72)

img = img.resize((512, 512), Image.LANCZOS)
img.save(Path(__file__).parent / "img" / "logo.png", optimize=True)
print("logo.png lista")
