# Placa de Instagram de la TERMINAL: una frase grande + una captura real de la
# pestaña en vivo.
#
# A diferencia de las placas evergreen (make-ig-placas.py, puro texto) y del
# carrusel de cambios (make-ig-cambios.py, datos del día), esta muestra el
# producto: la captura es de la app de verdad, no un mockup. Por eso el script
# NO dibuja una pantalla falsa — recibe el PNG capturado y lo monta.
#
# Uso:
#   python make-ig-terminal.py captura.png ig/media/terminal-mundo.png
import os
import sys

from PIL import Image, ImageDraw

# Mismas convenciones que el resto del kit (colores del theme, fuentes
# empacadas, la V): una sola fuente de verdad para la identidad.
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

TITULO = "Enterate de lo que pasa en el mundo"
ACCENT = "en el mundo"          # la parte que va en verde
BAJADA = ("Los titulares que mueven al mercado, traducidos al castellano y "
          "en vivo. Los de alto impacto salen marcados como FLASH.")
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
    """Titular con la parte del acento en verde. Se compone palabra por palabra
    para que el verde caiga donde tiene que caer aunque el corte de línea
    cambie."""
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


def montar(captura: str, salida: str) -> str:
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)

    # ── Marca ────────────────────────────────────────────────────────────────
    draw_v(dr, PAD, PAD, 34 * S)
    dr.text((PAD + 46 * S, PAD + 3 * S), "VERDIKT", font=MONO_B(19), fill=TEXT)
    dr.text((PAD + 46 * S, PAD + 26 * S), "TERMINAL", font=MONO(13), fill=GREEN)

    # ── Titular y bajada ─────────────────────────────────────────────────────
    y = PAD + 105 * S
    y = draw_titulo(dr, y, W - PAD * 2)
    y += 14 * S
    fb = SANS(23)
    for line in wrap(dr, BAJADA, fb, W - PAD * 2):
        dr.text((PAD, y), line, font=fb, fill=DIM)
        y += int(fb.size * 1.42)

    # ── La captura, montada como pantalla ────────────────────────────────────
    # Se recorta la franja útil (cabecera + primeros titulares) y se apoya
    # contra el borde inferior: la placa se lee como "mirá esto", con el
    # teléfono entrando en cuadro.
    shot = Image.open(captura).convert("RGB")
    top = int(shot.height * 0.055)     # saca el aire negro de arriba
    bottom = int(shot.height * 0.80)   # saca la barra de navegación
    shot = shot.crop((0, top, shot.width, bottom))

    frame_w = W - PAD * 2
    scale = frame_w / shot.width
    shot = shot.resize((frame_w, int(shot.height * scale)), Image.LANCZOS)

    y_shot = y + 34 * S
    visible = H - y_shot - 46 * S           # lo que queda hasta el pie
    if shot.height > visible:
        shot = shot.crop((0, 0, shot.width, visible))

    # Desvanecido al negro en el último tramo: el recorte cae en mitad de un
    # titular y sin esto se lee como una captura cortada, no como una pantalla
    # que sigue más abajo.
    fade_h = 150 * S // 2
    for i in range(fade_h):
        alpha = i / fade_h
        row_y = shot.height - fade_h + i
        if row_y < 0:
            continue
        row = shot.crop((0, row_y, shot.width, row_y + 1))
        dark = Image.new("RGB", row.size, BG)
        shot.paste(Image.blend(row, dark, alpha), (0, row_y))

    img.paste(shot, (PAD, y_shot))
    # Un marco de 1px: sin él, el negro de la captura y el negro del fondo se
    # funden y la pantalla no se lee como una pantalla.
    dr.rectangle([PAD - 2, y_shot - 2, PAD + shot.width + 1, y_shot + shot.height + 1],
                 outline=BORDER, width=2)

    # ── Pie ──────────────────────────────────────────────────────────────────
    fp = MONO(15)
    tw = dr.textlength(PIE, font=fp)
    dr.text(((W - tw) / 2, H - 34 * S), PIE, font=fp, fill=DIM)

    os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
    img.resize((1080, 1350), Image.LANCZOS).save(salida, quality=95)
    return salida


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "terminal.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "ig/media/terminal-mundo.png"
    print(montar(src, out))
