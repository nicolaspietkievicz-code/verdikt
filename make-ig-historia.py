# Historia de Instagram 1080x1920 con los datos del dia: animo del mercado,
# los indices, el top puntuado y cuantos activos cambiaron de veredicto.
#
# Por que es distinta de las otras placas: una historia se mira tres segundos y
# se va. Por eso el animo va GRANDE y solo, y lo demas queda en tres bloques
# cortos debajo. Nada de parrafos.
#
# ZONAS MUERTAS (lo que mas condiciona el diseno): Instagram le monta su propia
# interfaz encima a la historia — arriba la fila del perfil, abajo la barra de
# responder. Todo lo que importe tiene que vivir en la banda del medio, entre
# SAFE_TOP y SAFE_BOT. El fondo si ocupa los 1920 px.
#
# Como las historias por API NO admiten stickers ni link tocable (ver
# ig_publish.publish_story), el dominio va DIBUJADO en la placa.
#
# Uso:
#   python make-ig-historia.py                 -> ig/media/historia.png
#   python make-ig-historia.py salida.png
import json
import os
import sys
import urllib.request

from PIL import Image, ImageDraw

# Misma fuente de verdad para la identidad que el resto del kit.
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "make_ig_cambios",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "make-ig-cambios.py"))
_c = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_c)

BG, CARD, BORDER = _c.BG, _c.CARD, _c.BORDER
TEXT, DIM, GREEN = _c.TEXT, _c.DIM, _c.GREEN
VCOL = _c.VCOL
MONO, MONO_B, SANS, SANS_B = _c.MONO, _c.MONO_B, _c.SANS, _c.SANS_B
draw_v = _c.draw_v

ROJO = (217, 106, 123)

S = 2
W, H = 1080 * S, 1920 * S
PAD = 72 * S

# La banda util. Fuera de esto Instagram pone lo suyo encima.
SAFE_TOP = 300 * S
SAFE_BOT = 1660 * S

BASE = "https://app.verdikt.finance"

# Los mismos cortes que usa el motor para pasar de puntaje a palabra.
UMBRALES = [25, 44, 58, 72]
ESCALA = ["EVITAR", "CAUTELA", "NEUTRAL", "ACUMULAR", "COMPRA"]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


# --- Datos --------------------------------------------------------------------
def _get(path, timeout=60):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=timeout) as r:
        return json.load(r)


def fetch():
    """Trae todo de una. Si algun bloque falla, la historia se arma igual sin
    el: perder los indices no justifica no publicar nada."""
    datos = {"market": None, "verdicts": None, "changes": None}
    for clave, path in (("market", "/market"),
                        ("verdicts", "/verdicts-latest"),
                        ("changes", "/verdict-changes")):
        try:
            datos[clave] = _get(path)
        except Exception as e:
            print(f"::warning::no se pudo traer {path}: {e}")
    return datos


# --- Formato ------------------------------------------------------------------
def _miles(v):
    """Formato argentino: punto para los miles, coma para los decimales."""
    if v is None:
        return "-"
    if abs(v) >= 1000:
        return f"{v:,.0f}".replace(",", ".")
    return f"{v:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _pct(v):
    if v is None:
        return "-", DIM
    signo = "+" if v > 0 else ""
    txt = f"{signo}{v:.2f}".replace(".", ",") + "%"
    return txt, (GREEN if v > 0 else ROJO if v < 0 else DIM)


def _fecha_larga(dd):
    if not dd or len(dd) != 10:
        return ""
    return f"{int(dd[8:10])} de {MESES[int(dd[5:7]) - 1]}"


# --- Piezas -------------------------------------------------------------------
def _lienzo():
    """Cuadricula + marca, igual que el resto del kit, pero el header arranca
    dentro de la zona segura en vez de pegado al borde."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    cell = 42 * S
    grid = (24, 28, 36)
    for x in range(0, W, cell):
        d.line([(x, 0), (x, H)], fill=grid, width=1)
    for y in range(0, H, cell):
        d.line([(0, y), (W, y)], fill=grid, width=1)

    ts = 84 * S
    tx, ty = PAD, SAFE_TOP
    d.rounded_rectangle([tx, ty, tx + ts, ty + ts], radius=ts * 0.22,
                        fill=CARD, outline=BORDER, width=2)
    draw_v(d, tx + ts * 0.14, ty + ts * 0.14, ts * 0.72)

    mono_b = MONO_B(44)
    wx, wy = tx + ts + 28 * S, ty + ts / 2 - 30 * S
    for ch in "VERDIKT":
        d.text((wx, wy), ch, font=mono_b, fill=TEXT)
        wx += d.textlength(ch, font=mono_b) + 6 * S
    d.text((wx, wy), "_", font=mono_b, fill=GREEN)
    return img, d


def _rotulo(d, y, texto):
    """Etiqueta de seccion: mono, espaciada, verde. El separador va debajo."""
    f = MONO(26)
    x = PAD
    for ch in texto:
        d.text((x, y), ch, font=f, fill=GREEN)
        x += d.textlength(ch, font=f) + 3 * S
    d.line([(PAD, y + 44 * S), (W - PAD, y + 44 * S)], fill=BORDER, width=2)
    return y + 68 * S


def _barra_animo(d, y, score):
    """La escala de 0 a 100 en cinco tramos, con los cortes reales del motor.
    El tramo donde cae hoy va encendido y el resto apagado, igual que en la
    placa de la app."""
    x0, x1 = PAD, W - PAD
    alto = 18 * S
    cortes = [0] + UMBRALES + [100]
    activo = sum(1 for u in UMBRALES if score >= u)

    for i in range(5):
        a = x0 + (x1 - x0) * cortes[i] / 100
        b = x0 + (x1 - x0) * cortes[i + 1] / 100
        col = VCOL[ESCALA[i]]
        if i != activo:
            col = tuple(int(c * 0.22 + BG[j] * 0.78) for j, c in enumerate(col))
        d.rounded_rectangle([a + 3 * S, y, b - 3 * S, y + alto],
                            radius=alto / 2, fill=col)

    mx = x0 + (x1 - x0) * max(0, min(100, score)) / 100
    d.rounded_rectangle([mx - 3 * S, y - 9 * S, mx + 3 * S, y + alto + 9 * S],
                        radius=4 * S, fill=TEXT)
    return y + alto + 34 * S


def _bloque_animo(d, y, mood):
    """El heroe de la placa: la palabra grande y el puntaje al lado."""
    label = mood.get("label", "-")
    score = int(mood.get("score", 0))
    col = VCOL.get(label, TEXT)

    f = MONO_B(96)
    d.text((PAD, y), label, font=f, fill=col)
    wlab = d.textlength(label, font=f)

    fs = MONO_B(58)
    d.text((PAD + wlab + 26 * S, y + 44 * S), str(score), font=fs, fill=TEXT)
    wsc = d.textlength(str(score), font=fs)
    d.text((PAD + wlab + 26 * S + wsc, y + 56 * S), "/100", font=MONO(34), fill=DIM)

    y = _barra_animo(d, y + 132 * S, score)

    bull = mood.get("bull_pct")
    bear = mood.get("bear_pct")
    total = mood.get("total")
    if bull is not None and bear is not None:
        txt = (f"{bull:.0f}% en COMPRA o ACUMULAR contra "
               f"{bear:.0f}% en CAUTELA o EVITAR")
        d.text((PAD, y), txt, font=SANS(30), fill=DIM)
        y += 52 * S
    return y


def _bloque_mercados(d, y, market):
    """Cuatro renglones de contexto. Los numeros van en mono y alineados a la
    derecha para que las comas caigan en la misma columna."""
    filas = []
    for ix in (market.get("indices") or []):
        if ix.get("name") in ("Merval", "S&P 500"):
            filas.append((ix["name"], _miles(ix.get("value")),
                          _pct(ix.get("day_change_pct"))))
    ccl = (market.get("dolares") or {}).get("ccl")
    if ccl:
        filas.append(("Dólar CCL", "$" + _miles(ccl), ("", DIM)))

    fn, fv = SANS(34), MONO(34)
    for nombre, valor, (pct, pcol) in filas[:3]:
        d.text((PAD, y), nombre, font=fn, fill=TEXT)
        if pct:
            wp = d.textlength(pct, font=fv)
            d.text((W - PAD - wp, y), pct, font=fv, fill=pcol)
            wv = d.textlength(valor, font=fv)
            d.text((W - PAD - wp - 40 * S - wv, y), valor, font=fv, fill=DIM)
        else:
            wv = d.textlength(valor, font=fv)
            d.text((W - PAD - wv, y), valor, font=fv, fill=TEXT)
        y += 62 * S
    return y


def _bloque_top(d, y, verdicts, n=3):
    """Los mejor puntuados del dia. Tres alcanzan: en una historia, una lista
    de diez no la lee nadie."""
    items = sorted(verdicts.get("items") or [], key=lambda x: -x.get("score", 0))[:n]
    fs, fv, fn = MONO_B(46), MONO(30), MONO_B(46)
    for i, it in enumerate(items, 1):
        d.text((PAD, y + 6 * S), f"{i}", font=MONO(30), fill=DIM)
        d.text((PAD + 44 * S, y), it["symbol"], font=fs, fill=TEXT)

        score = str(it.get("score", ""))
        ws = d.textlength(score, font=fn)
        d.text((W - PAD - ws, y), score, font=fn, fill=TEXT)

        ver = it.get("verdict", "")
        wv = d.textlength(ver, font=fv)
        d.text((W - PAD - ws - 30 * S - wv, y + 12 * S), ver, font=fv,
               fill=VCOL.get(ver, DIM))
        y += 76 * S
    return y


def _alto_pie(changes):
    """Cuanto mide el cierre. Se calcula ANTES de dibujar el resto para poder
    reservarle el lugar: si no, el ultimo renglon del top le queda debajo."""
    n = len(((changes or {}).get("items")) or [])
    return 130 * S + (100 * S if n else 0)


def _pie(d, changes):
    """Cierre: cuantos cambiaron hoy (si hubo) y el dominio, dibujado — por API
    no hay sticker de link que valga."""
    y = SAFE_BOT - _alto_pie(changes)
    n = len(((changes or {}).get("items")) or [])
    if n:
        d.rounded_rectangle([PAD, y, W - PAD, y + 74 * S], radius=10 * S,
                            fill=CARD, outline=BORDER, width=2)
        txt = (f"{n} activos cambiaron de veredicto hoy" if n > 1
               else "1 activo cambió de veredicto hoy")
        d.text((PAD + 28 * S, y + 20 * S), txt, font=SANS(30), fill=TEXT)
        y += 100 * S

    d.text((PAD, y), "verdikt.finance", font=MONO_B(38), fill=GREEN)
    d.text((PAD, y + 52 * S), "El veredicto de los 135 activos, gratis.",
           font=SANS(28), fill=DIM)


# --- Armado -------------------------------------------------------------------
def generate(out_path="ig/media/historia.png", datos=None):
    datos = datos or fetch()
    market = datos.get("market") or {}
    mood = market.get("mood") or {}
    if not mood:
        raise RuntimeError("Sin animo del mercado no hay historia que valga.")

    img, d = _lienzo()

    fecha = _fecha_larga(mood.get("date") or "")
    d.text((PAD, SAFE_TOP + 110 * S), fecha.upper(), font=MONO(28), fill=DIM)

    y = SAFE_TOP + 178 * S
    y = _rotulo(d, y, "ÁNIMO DEL MERCADO")
    y = _bloque_animo(d, y, mood)

    y = _rotulo(d, y + 30 * S, "MERCADOS")
    y = _bloque_mercados(d, y, market)

    # El top se adapta a lo que sobra: con el pie ya reservado, entran tres
    # renglones, dos o ninguno. Antes se dibujaban tres siempre y el tercero
    # terminaba debajo de la tarjeta de cambios.
    tope = SAFE_BOT - _alto_pie(datos.get("changes")) - 30 * S
    if datos.get("verdicts"):
        caben = int((tope - (y + 24 * S + 68 * S)) // (76 * S))
        caben = max(0, min(3, caben))
        if caben:
            y = _rotulo(d, y + 24 * S, "MEJOR PUNTUADOS HOY")
            y = _bloque_top(d, y, datos["verdicts"], caben)
        else:
            print("::warning::no entra el top del dia: se publica sin el.")

    if y > tope:
        print(f"::warning::el contenido llega a {y // S}px y el pie arranca en "
              f"{tope // S}px: hay superposicion.")

    _pie(d, datos.get("changes"))

    img = img.resize((1080, 1920), Image.LANCZOS)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, optimize=True)
    return out_path


def main():
    salida = sys.argv[1] if len(sys.argv) > 1 else "ig/media/historia.png"
    p = generate(salida)
    print("historia:", p, f"({os.path.getsize(p) // 1024} KB)")


if __name__ == "__main__":
    main()
