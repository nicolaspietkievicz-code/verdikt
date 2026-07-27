# Placa de Instagram de la VERSION DE ESCRITORIO: una frase grande + una
# captura real de la app abierta en una pantalla grande.
#
# Hermana de make-ig-terminal.py y con la misma regla: la captura es de la app
# de verdad, NO un mockup dibujado. La diferencia es la forma — el teléfono es
# vertical y entra en cuadro por abajo; el escritorio es apaisado (16:10) y hay
# que montarlo como una ventana, con su barra y su marco, o se lee como una
# imagen recortada.
#
# Uso:
#   python make-ig-desktop.py captura.png ig/media/desktop-terminal.png
import os
import sys

from PIL import Image, ImageDraw

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "make_ig_cambios",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "make-ig-cambios.py"))
_c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_c)

BG, CARD, BORDER = _c.BG, _c.CARD, _c.BORDER
TEXT, DIM, GREEN = _c.TEXT, _c.DIM, _c.GREEN
MONO, MONO_B, SANS, SANS_B = _c.MONO, _c.MONO_B, _c.SANS, _c.SANS_B
draw_v = _c.draw_v

S = 2
W, H = 1080 * S, 1350 * S
PAD = 64 * S

TITULO = "Ahora también en la compu"
ACCENT = "en la compu"
BAJADA = ("La misma app, con el ancho de una pantalla grande: el ranking del "
          "día, los mercados y el wire en vivo, todo a la vez.")
# Tres cosas que se ven en la captura, en versalita mono: el pie de una
# terminal, no una lista de beneficios.
PATAS = ["135 ACTIVOS PUNTUADOS", "MERCADOS EN VIVO", "SIN INSTALAR NADA"]
PIE = "app.verdikt.finance"


def wrap(dr, text, font, max_w):
    """Corta el texto en líneas que entren en `max_w`."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        probe = f"{cur} {w}".strip()
        if dr.textlength(probe, font=font) <= max_w:
            cur = probe
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_titulo(dr, y, max_w):
    """Titular con la parte del acento en verde, palabra por palabra, para que
    el verde caiga donde tiene que caer aunque cambie el corte de línea."""
    font = SANS_B(58)
    accent_words = set(ACCENT.split())
    for line in wrap(dr, TITULO, font, max_w):
        x = PAD
        for word in line.split():
            color = GREEN if word.strip(".,") in accent_words else TEXT
            dr.text((x, y), word, font=font, fill=color)
            x += dr.textlength(word + " ", font=font)
        y += int(font.size * 1.22)
    return y


def draw_ventana(img, dr, captura: str, y: int) -> int:
    """Monta la captura como una ventana de navegador A SANGRE: barra con tres
    puntos y la dirección, y abajo la pantalla de punta a punta del cuadro.

    A sangre y no dentro del margen porque la captura es apaisada y densa: cada
    píxel de ancho que se le saca es texto que deja de distinguirse. Sin la
    barra de arriba, un rectángulo apaisado sobre negro se lee como la foto de
    una foto, no como una pantalla."""
    shot = Image.open(captura).convert("RGB")
    shot = shot.resize((W, int(shot.height * (W / shot.width))), Image.LANCZOS)

    barra_h = 34 * S
    dr.rectangle([0, y, W, y + barra_h], fill=CARD)
    r = 5 * S
    cx = PAD
    for _ in range(3):
        dr.ellipse([cx - r, y + barra_h // 2 - r, cx + r, y + barra_h // 2 + r], fill=BORDER)
        cx += 18 * S
    fu = MONO(12)
    dr.text((cx + 12 * S, y + barra_h // 2 - int(fu.size * 0.62)),
            "app.verdikt.finance", font=fu, fill=DIM)

    # El recorte de abajo cae en mitad de una fila del ranking. Desvanecer al
    # negro lo convierte en "la pantalla sigue" en vez de "la captura se cortó".
    fade_h = 70 * S
    for i in range(fade_h):
        row_y = shot.height - fade_h + i
        if row_y < 0:
            continue
        row = shot.crop((0, row_y, shot.width, row_y + 1))
        dark = Image.new("RGB", row.size, BG)
        shot.paste(Image.blend(row, dark, i / fade_h), (0, row_y))

    img.paste(shot, (0, y + barra_h))
    # Reglas arriba y abajo: a sangre no hay marco lateral que encuadre, y sin
    # ellas la ventana se funde con el fondo.
    dr.line([0, y, W, y], fill=BORDER, width=2)
    dr.line([0, y + barra_h + shot.height, W, y + barra_h + shot.height],
            fill=BORDER, width=2)
    return y + barra_h + shot.height


def montar(captura: str, salida: str) -> str:
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)

    # ── Marca ────────────────────────────────────────────────────────────────
    draw_v(dr, PAD, PAD, 34 * S)
    dr.text((PAD + 46 * S, PAD + 3 * S), "VERDIKT", font=MONO_B(19), fill=TEXT)
    dr.text((PAD + 46 * S, PAD + 26 * S), "ESCRITORIO", font=MONO(13), fill=GREEN)

    # ── Titular y bajada ─────────────────────────────────────────────────────
    y = PAD + 105 * S
    y = draw_titulo(dr, y, W - PAD * 2)
    y += 14 * S
    fb = SANS(23)
    for line in wrap(dr, BAJADA, fb, W - PAD * 2):
        dr.text((PAD, y), line, font=fb, fill=DIM)
        y += int(fb.size * 1.42)

    # ── La ventana ───────────────────────────────────────────────────────────
    # La captura es apaisada: aun a sangre sobra alto. El sobrante se reparte
    # arriba y abajo en vez de acumularse todo al pie.
    shot = Image.open(captura)
    alto = 34 * S + int(shot.height * (W / shot.width)) + 46 * S  # + las patas
    desde, hasta = y + 42 * S, H - 62 * S
    fin = draw_ventana(img, dr, captura, desde + max(0, (hasta - desde - alto) // 2))

    # ── Patas ────────────────────────────────────────────────────────────────
    fp = MONO(13)
    sep = "   ·   "
    linea = sep.join(PATAS)
    tw = dr.textlength(linea, font=fp)
    dr.text(((W - tw) / 2, fin + 28 * S), linea, font=fp, fill=DIM)

    # ── Pie ──────────────────────────────────────────────────────────────────
    fpie = MONO(15)
    tw = dr.textlength(PIE, font=fpie)
    dr.text(((W - tw) / 2, H - 34 * S), PIE, font=fpie, fill=DIM)

    os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
    img.resize((1080, 1350), Image.LANCZOS).save(salida, quality=95)
    return salida


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "desktop.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "ig/media/desktop.png"
    print(montar(src, out))
