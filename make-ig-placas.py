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
def _st(texto, accent, pie=""):
    return {"tipo": "statement", "texto": texto, "accent": accent,
            "pie": pie or "app.verdikt.finance"}


def _li(kicker, titulo, *items):
    return {"tipo": "lista", "kicker": kicker, "titulo": titulo, "items": list(items)}


PLACAS = {
    # ── Declaraciones de marca ────────────────────────────────────────────────
    "manifiesto": _st("No te decimos qué comprar. Te damos un veredicto.", "veredicto."),
    "esperar": _st("Esperar también es una posición.", "posición.",
                   "No entrar es, muchas veces, la mejor operación del día."),
    "probabilidades": _st("El mercado no te da certezas. Te da probabilidades.",
                          "probabilidades."),
    "criterio": _st("Un número no reemplaza tu criterio. Lo ordena.", "criterio."),
    "porque": _st("La peor operación es la que no sabías por qué hacías.", "por qué"),
    "momentos": _st("No hay activos buenos ni malos. Hay momentos.", "momentos."),
    "salida": _st("Si no sabés dónde salís, todavía no sabés si entrás.", "salís,"),
    "perder-poco": _st("Perder poco a tiempo también es ganar.", "ganar."),
    "precio-valor": _st("El precio te dice cuánto pagás. No cuánto vale.", "vale."),
    "barato": _st("Comprar barato no es lo mismo que comprar bien.", "barato"),
    "medir": _st("Lo que no medís, lo estás adivinando.", "medís,"),
    "disciplina": _st("El mercado premia la disciplina, no la intuición.", "disciplina,"),

    # ── Educativas ────────────────────────────────────────────────────────────
    "senales": _li("aprender", "3 señales que confunden a los principiantes",
                   "RSI bajo no es “barato”. Puede seguir cayendo.",
                   "Volumen sin dirección no confirma nada.",
                   "Una vela verde no es una tendencia."),
    "per": _li("aprender", "Qué es el PER y qué no te dice",
               "Compara el precio con las ganancias de la empresa.",
               "Un PER bajo puede ser una oportunidad o una empresa en problemas.",
               "Solo sirve comparando empresas del mismo sector."),
    "precio-cara": _li("aprender", "Por qué el precio no dice si una acción está cara",
                       "Una acción de $5 puede estar más cara que una de $500.",
                       "Lo que importa es cuánto valen las ganancias detrás.",
                       "El precio solo dice cuánto sale una unidad."),
    "media-movil": _li("aprender", "Qué es una media móvil y para qué sirve",
                       "Es el precio promedio de los últimos N días.",
                       "Suaviza el ruido diario y deja ver la dirección.",
                       "No predice: describe lo que ya viene pasando."),
    "soporte-resistencia": _li("aprender", "Soporte y resistencia, sin misterio",
                               "Soporte: zona donde históricamente aparecen compradores.",
                               "Resistencia: zona donde aparecen vendedores.",
                               "No son paredes. Son zonas donde el precio suele frenar."),
    "stop-loss": _li("aprender", "Qué es el stop loss y por qué se define antes",
                     "Es el precio al que aceptás que te equivocaste.",
                     "Se fija ANTES de entrar, con la cabeza fría.",
                     "Definirlo después es negociar con vos mismo."),
    "riesgo-beneficio": _li("aprender", "Riesgo/beneficio: la cuenta que casi nadie hace",
                            "Cuánto arriesgo contra cuánto puedo ganar.",
                            "Si arriesgás 10 para ganar 10, necesitás acertar siempre.",
                            "Con 1 a 3, alcanza con acertar una de cada tres."),
    "drawdown": _li("aprender", "Qué es el drawdown y por qué duele",
                    "Es cuánto cayó tu cartera desde su punto más alto.",
                    "Una caída del 50% necesita un 100% para recuperarse.",
                    "Por eso proteger el capital vale más que acertar."),
    "ya-bajo": _li("aprender", "Por qué “ya bajó mucho” no es una razón",
                   "Una acción que cayó 50% puede caer otro 50%.",
                   "El precio pasado no pone un piso.",
                   "Lo barato se define por el negocio, no por el gráfico."),
    "promediar": _li("aprender", "Promediar a la baja: plan o terquedad",
                     "Es plan si estaba escrito antes de comprar.",
                     "Es terquedad si nace de no querer aceptar la pérdida.",
                     "La diferencia no está en el precio: está en la decisión."),
    "cedear-que-es": _li("aprender", "Qué es un CEDEAR, en criollo",
                         "Un certificado que representa acciones del exterior.",
                         "Se compra en pesos, en el mercado argentino.",
                         "Te da exposición a la empresa sin sacar la plata del país."),
    "cedear-ratio": _li("aprender", "Por qué un CEDEAR no vale lo mismo que la acción",
                        "Cada CEDEAR equivale a una fracción de la acción real.",
                        "Esa proporción se llama ratio y cambia según la empresa.",
                        "Sin mirar el ratio, cualquier comparación de precios engaña."),
    "ccl": _li("aprender", "Qué es el dólar CCL y por qué te afecta",
               "Es el tipo de cambio implícito en comprar y vender activos.",
               "Los CEDEARs se mueven con la acción Y con el CCL.",
               "Podés acertar la acción y perder por el dólar."),
    "diversificar": _li("aprender", "Diversificar no es comprar diez cosas parecidas",
                        "Diez tecnológicas caen juntas: eso no es diversificar.",
                        "Diversificar es tener activos que no se mueven igual.",
                        "Si todo sube junto, también va a bajar junto."),
    "volatilidad": _li("aprender", "Volatilidad y riesgo no son lo mismo",
                       "Volatilidad es cuánto se mueve el precio.",
                       "Riesgo es la chance de perder plata de forma permanente.",
                       "Un activo tranquilo también puede arruinarte."),
    "dividendos": _li("aprender", "Qué son los dividendos y de dónde salen",
                      "Es parte de la ganancia que la empresa reparte.",
                      "El día que los paga, la acción vale menos por ese monto.",
                      "No es plata gratis: es plata que sale de la empresa."),
    "spread": _li("aprender", "El spread: el costo que no ves",
                  "Es la diferencia entre el precio de compra y el de venta.",
                  "Lo pagás al entrar y al salir, aunque no figure como comisión.",
                  "En activos poco operados puede costarte más que la comisión."),
    "volumen": _li("aprender", "Por qué el volumen importa tanto como el precio",
                   "El volumen es cuánta gente respaldó ese movimiento.",
                   "Una suba sin volumen es una suba sin convicción.",
                   "Los movimientos que duran suelen venir acompañados."),
    "costo-oportunidad": _li("aprender", "Qué es el costo de oportunidad",
                             "Es lo que dejás de ganar por elegir una cosa y no otra.",
                             "Sostener una posición muerta cuesta, aunque no pierda.",
                             "El capital quieto también tiene precio."),
    "tres-errores": _li("aprender", "Tres errores que cometen casi todos al empezar",
                        "Entrar sin saber a qué precio saldrían.",
                        "Poner en una sola apuesta lo que no pueden perder.",
                        "Cambiar de estrategia cada vez que una falla."),

    # ── Cómo decide el sistema ────────────────────────────────────────────────
    "filtros": _li("cómo decide", "Un veredicto pasa por 4 filtros",
                   "Tendencia diaria a favor.",
                   "Confirmación en el gráfico de 1 hora.",
                   "Riesgo mínimo exigido para entrar.",
                   "Momentum que todavía no se agotó."),
    "confirmacion": _li("cómo decide", "Por qué exigimos confirmación en 1 hora",
                        "El gráfico diario marca la dirección de fondo.",
                        "El de 1 hora evita entrar contra un rebote falso.",
                        "Sin las dos alineadas, no hay veredicto de compra."),
    "score-mide": _li("cómo decide", "Qué mide el score de 0 a 100",
                      "Resume tendencia, momentum, volumen y riesgo en un número.",
                      "Es una foto del panorama técnico, no una predicción.",
                      "Sirve para comparar activos entre sí el mismo día."),
    "cinco-veredictos": _li("cómo decide", "Por qué hay cinco veredictos y no dos",
                            "El mercado no es binario: casi todo es matiz.",
                            "Entre comprar y evitar hay tres estados intermedios.",
                            "Forzar todo a sí o no esconde justamente lo que importa."),
    "cambia-diario": _li("cómo decide", "Por qué el veredicto cambia todos los días",
                         "Se recalcula con los datos de cada cierre.",
                         "Si el panorama cambia, el veredicto cambia con él.",
                         "Un veredicto viejo no describe el mercado de hoy."),
    "no-mira": _li("cómo decide", "Qué NO mira Verdikt",
                   "No adivina hacia dónde va el precio.",
                   "No sabe cuánta plata tenés ni cuánto podés arriesgar.",
                   "No reemplaza tu decisión: la informa."),
    "score-alto": _li("cómo decide", "Un score alto no es una orden de compra",
                      "Dice que el panorama técnico acompaña, nada más.",
                      "El tamaño de la posición sigue siendo tuyo.",
                      "Sin plan de salida, ningún número te salva."),
    "cedear-veredicto": _li("cómo decide", "Cómo se arma el veredicto de un CEDEAR",
                            "Se analiza la acción real, en su mercado de origen.",
                            "Ahí está el volumen que de verdad mueve el precio.",
                            "El CEDEAR sigue a esa acción, más el efecto del dólar."),
}

# Orden de publicacion. Arranca con declaraciones y educativas: explicar el
# metodo antes de que a nadie le importe rinde poco, asi que las de "como
# decide" quedan para mas adelante, cuando ya haya audiencia.
ORDEN = [
    "manifiesto", "senales", "probabilidades", "stop-loss", "esperar",
    "cedear-que-es", "criterio", "riesgo-beneficio", "precio-valor", "ya-bajo",
    "momentos", "media-movil", "salida", "diversificar", "porque",
    "volumen", "barato", "precio-cara", "perder-poco", "ccl",
    "medir", "soporte-resistencia", "disciplina", "per", "drawdown",
    "filtros", "promediar", "score-mide", "volatilidad", "confirmacion",
    "spread", "cinco-veredictos", "dividendos", "cambia-diario",
    "costo-oportunidad", "score-alto", "cedear-ratio", "no-mira",
    "tres-errores", "cedear-veredicto",
]


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

    # El acento puede ser una frase ("por qué"), no solo una palabra: se busca
    # la secuencia consecutiva y se pinta entera. Marcando palabra por palabra,
    # "por" salia en verde y "qué" en blanco.
    palabras = cfg["texto"].split()
    acc = (cfg.get("accent") or "").split()
    marca = [False] * len(palabras)
    for i in range(len(palabras) - len(acc) + 1) if acc else []:
        if palabras[i:i + len(acc)] == acc:
            for j in range(i, i + len(acc)):
                marca[j] = True
            break
    words = [(w, GREEN if marca[i] else TEXT) for i, w in enumerate(palabras)]
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


HASHTAGS = ("#inversiones #cedears #cripto #trading #bolsa #acciones "
            "#finanzas #mercados #argentina #análisis")


def caption(nombre: str) -> str:
    """El caption se DERIVA de la placa en vez de escribirse aparte: asi no se
    pueden desincronizar, que es lo que ya paso una vez con los cambios."""
    cfg = PLACAS[nombre]
    if cfg["tipo"] == "statement":
        cuerpo = [cfg["texto"]]
        pie = cfg.get("pie", "")
        if pie and not pie.startswith("app."):
            cuerpo.append(pie)
    else:
        cuerpo = [cfg["titulo"], ""]
        cuerpo += [f"· {it}" for it in cfg["items"]]
    return "\n".join(cuerpo + [
        "",
        "Analizá cualquier acción, CEDEAR o cripto en app.verdikt.finance",
        "",
        HASHTAGS,
    ])


def siguiente(ultima: str = "") -> str:
    """Proxima placa de la rotacion. Con 40 placas a una por dia, el ciclo
    tarda mas de un mes en repetirse."""
    if ultima in ORDEN:
        return ORDEN[(ORDEN.index(ultima) + 1) % len(ORDEN)]
    return ORDEN[0]


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
