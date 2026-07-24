# Foto de perfil para el Instagram de Verdikt (1080x1080).
#
# Por que no sirve img/logo.png: ese es un tile CUADRADO con esquinas
# redondeadas y borde. Instagram recorta la foto de perfil en CIRCULO, asi que
# esas esquinas -y el borde que las dibuja- se pierden enteras. Ademas la V
# queda 42px por debajo del centro (draw_v la apoya baja dentro de su caja),
# desfasaje que en un cuadrado no se nota pero en un circulo si.
#
# Entonces: fondo a sangre (el circulo se lo come todo igual), cuadricula de la
# marca, y la V centrada por BOUNDING BOX real -no por formula- y agrandada
# para que se lea en los 32px que usa Instagram en los comentarios.
import math
from pathlib import Path

from PIL import Image, ImageDraw

TILE = (11, 14, 20)       # #0B0E14 (fondo del icono, igual que el resto)
GRID = (24, 32, 46)       # lineas de la cuadricula
GREEN = (47, 191, 113)    # #2FBF71
GREEN_DIM = (30, 96, 66)  # #1E6042 (rama que cae)

S = 3                     # supersampling: se dibuja a 3x y se baja con LANCZOS
OUT = 1080
W = H = OUT * S

# Cuanto del diametro ocupa la marca. 0.66 la deja grande para que se lea
# chica, sin pegarse al borde del recorte circular.
MARK_FRAC = 0.66


def draw_v(dr, ox, oy, side, green=GREEN, dim=GREEN_DIM):
    """Marca V-recuperacion dentro del cuadrado [ox, oy, ox+side].
    Copiada tal cual de make-logo.py / make-og.py — misma marca, sin variantes."""
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


def build() -> Image.Image:
    img = Image.new("RGB", (W, H), TILE)
    d = ImageDraw.Draw(img)

    # Cuadricula a sangre. Con el recorte circular no hay tile que respetar,
    # asi que la grilla corre de borde a borde como en los posteos.
    step = W // 12
    for x in range(0, W + 1, step):
        d.line([(x, 0), (x, H)], fill=GRID, width=S)
    for y in range(0, H + 1, step):
        d.line([(0, y), (W, y)], fill=GRID, width=S)

    # La marca se dibuja aparte, en transparente, para poder medir su bounding
    # box REAL y centrarla. Centrar la caja de draw_v en vez de la marca es lo
    # que dejaba la V corrida hacia abajo en el logo actual.
    side = W * MARK_FRAC
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_v(ImageDraw.Draw(layer), (W - side) / 2, (H - side) / 2, side)

    box = layer.getbbox()
    dx = (W - (box[0] + box[2])) // 2
    dy = (H - (box[1] + box[3])) // 2
    img.paste(layer.crop(box), (box[0] + dx, box[1] + dy), layer.crop(box))

    return img.resize((OUT, OUT), Image.LANCZOS)


if __name__ == "__main__":
    im = build()
    out = Path(__file__).parent / "img" / "ig-pfp.png"
    im.save(out, optimize=True)
    print("listo:", out)
