# Placas "evergreen" del Instagram de Verdikt: las que NO dependen de datos del
# dia (manifiesto, educativas, como decide el sistema, cierre). Existen para
# que la cuenta tenga contenido los dias sin cambios de veredicto y para que el
# feed no sea siempre la misma placa con otros numeros.
#
# Vienen del "Kit de Instagram" (borrador del 18/07), reconstruidas con la
# identidad ACTUAL: la V de draw_v, las fuentes empacadas de ig/fonts y los
# colores del theme — el kit todavia usaba el logo viejo de barras.
#
# Dos plantillas cubren casi todo:
#   statement -> una frase grande con una palabra en verde (manifiesto, cierre)
#   lista     -> titulo + items numerados (educativas, sistema)
#
# El texto vive en PLACAS, separado del dibujo: sumar una placa nueva es
# agregar un dict, no tocar el layout. Ahi es donde crece la biblioteca.
import os

from PIL import Image, ImageDraw

# Se reusan las convenciones del generador de cambios (colores del theme,
# fuentes portables, la V) en vez de duplicarlas: una sola fuente de verdad.
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "make_ig_cambios",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "make-ig-cambios.py"))
_c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_c)

BG, CARD, BORDER = _c.BG, _c.CARD, _c.BORDER
TEXT, DIM, GREEN = _c.TEXT, _c.DIM, _c.GREEN
_font, draw_v = _c._font, _c.draw_v

S = 2
W, H = 1080 * S, 1350 * S
PAD = 64 * S


# ── Biblioteca de placas ──────────────────────────────────────────────────────
# `accent`: la palabra que va en verde dentro de la frase (statement).
PLACAS = {
    "manifiesto": {
        "tipo": "statement",
        "texto": "No te decimos qué comprar. Te damos un veredicto.",
        "accent": "veredicto.",
        "pie": "app.verdikt.finance",
    },
    "esperar": {
        "tipo": "statement",
        "texto": "Esperar también es una posición.",
        "accent": "posición.",
        "pie": "No entrar es, muchas veces, la mejor operación del día.",
    },
    "senales": {
        "tipo": "lista",
        "kicker": "aprender",
        "titulo": "3 señales que confunden a los principiantes",
        "items": [
            "RSI bajo no es “barato”. Puede seguir cayendo.",
            "Volumen sin dirección no confirma nada.",
            "Una vela verde no es una tendencia.",
        ],
    },
    "filtros": {
        "tipo": "lista",
        "kicker": "cómo decide",
        "titulo": "Un veredicto pasa por 4 filtros",
        "items": [
            "Tendencia diaria a favor.",
            "Confirmación en el gráfico de 1 hora.",
            "Riesgo mínimo exigido para entrar.",
            "Momentum que todavía no se agotó.",
        ],
    },
    "confirmacion": {
        "tipo": "lista",
        "kicker": "cómo decide",
        "titulo": "Por qué exigimos confirmación en 1 hora",
        "items": [
            "El gráfico diario marca la dirección de fondo.",
            "El de 1 hora evita entrar contra un rebote falso.",
            "Sin las dos alineadas, no hay veredicto de compra.",
        ],
    },
}


def _chrome(d):
    """Fondo comun a todas las placas: cuadricula + header de marca."""
    cell = 42 * S
    grid = (24, 28, 36)
    for x in range(0, W, cell):
        d.line([(x, 0), (x, H)], fill=grid, width=1)
    for y in range(0, H, cell):
        d.line([(0, y), (W, y)], fill=grid, width=1)

    mono_b = _font(["CascadiaCode-Bold.ttf", "consolab.ttf", "DejaVuSansMono-Bold.ttf"], 44 * S)
    ts = 84 * S
    tx = ty = PAD
    d.rounded_rectangle([tx, ty, tx + ts, ty + ts], radius=ts * 0.22,
                        fill=CARD, outline=BORDER, width=2)
    draw_v(d, tx + ts * 0.14, ty + ts * 0.14, ts * 0.72)
    wx, wy = tx + ts + 28 * S, ty + ts / 2 - 30 * S
    for ch in "VERDIKT":
        d.text((wx, wy), ch, font=mono_b, fill=TEXT)
        wx += d.textlength(ch, font=mono_b) + 6 * S
    d.text((wx, wy), "_", font=mono_b, fill=GREEN)
    return tx + ts + 28 * S


def _wrap(d, words, font, max_w):
    """Corta en lineas una lista de (palabra, color) midiendo de verdad."""
    lines, cur, cur_w = [], [], 0
    space = d.textlength(" ", font=font)
    for w, col in words:
        ww = d.textlength(w, font=font)
        if cur and cur_w + space + ww > max_w:
            lines.append(cur)
            cur, cur_w = [], 0
        cur.append((w, col, ww))
        cur_w += ww + (space if len(cur) > 1 else 0)
    if cur:
        lines.append(cur)
    return lines, space


def _statement(d, cfg):
    """Frase grande, centrada verticalmente, con una palabra en verde."""
    f = _font(["Inter-Bold.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"], 92 * S)
    sans = _font(["Inter-Regular.ttf", "segoeui.ttf", "DejaVuSans.ttf"], 30 * S)
    mono = _font(["CascadiaCode-Regular.ttf", "consola.ttf", "DejaVuSansMono.ttf"], 30 * S)

    accent = cfg.get("accent")
    words = [(w, GREEN if w == accent else TEXT) for w in cfg["texto"].split()]
    lines, space = _wrap(d, words, f, W - PAD * 2)

    # Centrado en el espacio REAL (entre el header y el pie), no en el lienzo:
    # centrar contra la altura total deja el bloque alto y un hueco muerto abajo.
    lh = 112 * S
    top, bot = 210 * S, H - 190 * S
    y = top + (bot - top - len(lines) * lh) / 2
    for ln in lines:
        x = PAD
        for w, col, ww in ln:
            d.text((x, y), w, font=f, fill=col)
            x += ww + space
        y += lh

    pie = cfg.get("pie", "")
    if pie.startswith("app."):
        d.text((PAD, H - 96 * S), pie, font=mono, fill=GREEN)
    else:
        d.text((PAD, H - 150 * S), pie, font=sans, fill=DIM)
        d.text((PAD, H - 96 * S), "app.verdikt.finance", font=mono, fill=GREEN)


def _lista(d, cfg):
    """Titulo + items numerados en una tarjeta."""
    title_f = _font(["Inter-Bold.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"], 64 * S)
    sans = _font(["Inter-Regular.ttf", "segoeui.ttf", "DejaVuSans.ttf"], 34 * S)
    sans_sm = _font(["Inter-Regular.ttf", "segoeui.ttf", "DejaVuSans.ttf"], 28 * S)
    mono = _font(["CascadiaCode-Regular.ttf", "consola.ttf", "DejaVuSansMono.ttf"], 30 * S)
    mono_sm = _font(["CascadiaCode-Regular.ttf", "consola.ttf", "DejaVuSansMono.ttf"], 26 * S)

    d.text((PAD, 210 * S), cfg["kicker"].upper(), font=mono_sm, fill=GREEN)

    tl, sp = _wrap(d, [(w, TEXT) for w in cfg["titulo"].split()], title_f, W - PAD * 2)
    y = 268 * S
    for ln in tl:
        x = PAD
        for w, col, ww in ln:
            d.text((x, y), w, font=title_f, fill=col)
            x += ww + sp
        y += 80 * S

    rows = []
    for it in cfg["items"]:
        wl, s2 = _wrap(d, [(w, TEXT) for w in it.split()], sans, W - PAD * 2 - 150 * S)
        rows.append((wl, s2))
    card_h = sum(len(r[0]) * 52 * S + 56 * S for r in rows) + 40 * S
    # La tarjeta se centra entre el titulo y el pie: con altura fija quedaba
    # pegada al titulo y dejaba un hueco muerto abajo (listas de 3 items).
    cy0 = y + 50 * S + max(0, (H - 190 * S - (y + 50 * S) - card_h) / 2)
    d.rounded_rectangle([PAD, cy0, W - PAD, cy0 + card_h], radius=16 * S,
                        fill=CARD, outline=BORDER, width=2)

    y = cy0 + 44 * S
    for i, (wl, s2) in enumerate(rows, 1):
        n = str(i)
        nw = d.textlength(n, font=mono)
        d.rounded_rectangle([PAD + 36 * S, y - 6 * S, PAD + 36 * S + nw + 28 * S, y + 46 * S],
                            radius=6 * S, outline=BORDER, width=2)
        d.text((PAD + 50 * S, y + 4 * S), n, font=mono, fill=GREEN)
        tx = PAD + 36 * S + nw + 56 * S
        for ln in wl:
            x = tx
            for w, col, ww in ln:
                d.text((x, y), w, font=sans, fill=col)
                x += ww + s2
            y += 52 * S
        y += 56 * S

    d.text((PAD, H - 150 * S), "Un veredicto claro, de 0 a 100. Actualizado todos los días.",
           font=sans_sm, fill=DIM)
    d.text((PAD, H - 96 * S), "app.verdikt.finance", font=mono, fill=GREEN)


def generate(nombre: str, out_path: str = None) -> str:
    cfg = PLACAS[nombre]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    _chrome(d)
    (_statement if cfg["tipo"] == "statement" else _lista)(d, cfg)

    out_path = out_path or f"ig/placas/{nombre}.png"
    img = img.resize((1080, 1350), Image.LANCZOS)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, optimize=True)
    return out_path


if __name__ == "__main__":
    for n in PLACAS:
        print("ok:", generate(n))
