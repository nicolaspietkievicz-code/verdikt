"""Datos para las placas de info -> data.js (+ caption).

  python ig/placa/build.py veredicto            # nro 1 del ranking del dia
  python ig/placa/build.py veredicto NVDA stock # forzar activo
  python ig/placa/build.py termometro
  python ig/placa/build.py cambios
  python ig/placa/build.py educativa            # la que toca en la rotacion

El caption se DERIVA de los mismos datos que la placa (no se escribe aparte):
asi no se pueden desincronizar.
"""
import datetime
import importlib.util
import json
import os
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
API = "https://app.verdikt.finance"

_spec = importlib.util.spec_from_file_location(
    "build_data", os.path.join(RAIZ, "ig", "reel", "build_data.py"))
bd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bd)

MERCADO = {"crypto": "Cripto", "stock": "Wall St", "cedear": "CEDEAR",
           "ar": "Argentina", "eu": "Europa", "asia": "Asia"}
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
HASHTAGS = ("#inversiones #cedears #cripto #trading #bolsa #acciones "
            "#finanzas #mercados #argentina #análisis")
CIERRE_CAPTION = [
    "",
    "El score va de 0 a 100 y resume el panorama tecnico. Se recalcula todos "
    "los dias con el cierre. No es una recomendacion de inversion.",
    "",
    "Analiza cualquier accion, CEDEAR o cripto en app.verdikt.finance",
    "",
    HASHTAGS,
]


def _fecha_larga(d: datetime.date) -> str:
    return f"{d.day} de {_MESES[d.month - 1]} de {d.year}"


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=30) as r:
        return json.loads(r.read())


def _fmt_num(v) -> str:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if abs(v) >= 1000:
        return f"{v:,.0f}".replace(",", ".")
    if abs(v) >= 1:
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{v:.4f}".rstrip("0").replace(".", ",")


def _dump(payload: dict, caption: str) -> None:
    payload.setdefault("fecha", _fecha_larga(datetime.date.today()))
    fondos_dir = os.path.join(AQUI, "fondos")
    payload["fondos"] = sorted(f for f in os.listdir(fondos_dir)
                               if f.endswith(".png")) if os.path.isdir(fondos_dir) else []
    with open(os.path.join(AQUI, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    with open(os.path.join(AQUI, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)


# --------------------------------------------------------------- veredicto ----
def _numero_uno() -> tuple:
    it = (_get("/market/ranking").get("items") or [None])[0]
    if not it:
        raise SystemExit("el ranking vino vacio")
    return it["symbol"], it["asset_class"]


def _titular(d: dict) -> str:
    try:
        if RAIZ not in sys.path:
            sys.path.insert(0, RAIZ)
        from ig.ia import redaccion
        return redaccion.redactar(d)["titular"]
    except Exception as e:
        print(f"  sin titular de IA ({type(e).__name__}: {str(e)[:80]}); templado")
        return f"El veredicto de {d['name']} hoy"


def build_veredicto(sym: str = "", clase: str = "") -> dict:
    if not sym:
        sym, clase = _numero_uno()
    clase = clase or "stock"
    print(f"placa veredicto de {sym} ({clase})")
    d = bd.preparar(bd.pedir(sym, clase))
    hoy = datetime.date.today()
    r = d["razones"]
    pos = [x["titulo"] for x in r if x["tipo"] == "positivo"]
    neg = [x["titulo"] for x in r if x["tipo"] == "negativo"]

    _dump({
        "tipo": "veredicto",
        "kicker": "VEREDICTO DEL DÍA",
        "name": d["name"], "symbol": d["symbol"],
        "mercado": MERCADO.get(clase, clase.upper()),
        "score": d["score"], "verdict": d["verdict"],
        "titular": _titular(d),
        "afavor": pos[:3], "encontra": neg[:3],
    }, "\n".join([
        f"Veredicto del dia — {_fecha_larga(hoy)}", "",
        f"{d['name']} ({d['symbol']}): {d['verdict']} · {d['score']}/100", "",
        ("A favor: " + "; ".join(t.lower() for t in pos) + ".") if pos else "",
        ("En contra: " + "; ".join(t.lower() for t in neg) + ".") if neg else "",
    ] + ([f"", f"Que vigilar: {d['risk'][0].lower() + d['risk'][1:]}."] if d.get("risk") else [])
      + CIERRE_CAPTION))
    print(f"  {d['symbol']} {d['score']}/100 {d['verdict']}")
    return {"symbol": d["symbol"], "clase": clase, "screen": f"?a={d['symbol']}&c={clase}"}


# -------------------------------------------------------------- termometro ----
_IND_PLACA = ["Merval", "S&P 500", "Bitcoin"]


def build_termometro() -> dict:
    print("placa termometro")
    m = _get("/market")
    mood = m.get("mood") or {}
    ind = {i["name"]: i for i in m.get("indices", [])}
    indices = []
    for n in _IND_PLACA:
        i = ind.get(n)
        if i:
            indices.append({"name": n, "value": _fmt_num(i["value"]),
                            "chg": round(i.get("day_change_pct") or 0, 2)})
    cambios = len((_get("/verdict-changes").get("items") or []))
    ccl = (m.get("dolares") or {}).get("ccl")
    bull, bear = round(mood.get("bull_pct") or 0), round(mood.get("bear_pct") or 0)
    nota = (f"{bull}% de los activos analizados están alcistas y {bear}% bajistas. "
            f"{cambios} cambiaron de veredicto en la última semana.")

    _dump({
        "tipo": "termometro",
        "kicker": "TERMÓMETRO DEL MERCADO",
        "mood_label": mood.get("label", "NEUTRAL"),
        "mood_score": mood.get("score", 50),
        "bull_pct": bull, "bear_pct": bear,
        "indices": indices, "ccl": _fmt_num(ccl) if ccl else "—",
        "nota": nota,
    }, "\n".join([
        f"Termometro del mercado — {_fecha_larga(datetime.date.today())}", "",
        f"Animo general: {mood.get('label', 'NEUTRAL')} ({mood.get('score', 50)}/100)",
        f"{bull}% alcistas · {bear}% bajistas",
        "",
    ] + [f"{i['name']}: {i['value']} ({'+' if i['chg'] >= 0 else ''}{i['chg']}%)" for i in indices]
      + ([f"Dolar CCL: {_fmt_num(ccl)}"] if ccl else [])
      + ["", f"{cambios} activos cambiaron de veredicto esta semana."]
      + CIERRE_CAPTION))
    return {"screen": "/"}  # captura de la home (ranking del día)


# ----------------------------------------------------------------- cambios ----
def build_cambios() -> dict:
    print("placa cambios de veredicto")
    ch = _get("/verdict-changes")
    items = ch.get("items") or []
    if not items:
        raise SystemExit("no hay cambios de veredicto hoy")
    # Los que mas se movieron primero (el backend ya los ordena, pero por si acaso).
    items = sorted(items, key=lambda it: abs((it.get("score") or 0) - (it.get("prev_score") or 0)),
                   reverse=True)[:6]
    filas = [{"symbol": it["symbol"], "prev": it["prev_verdict"], "now": it["verdict"],
              "prev_score": it["prev_score"], "score": it["score"]} for it in items]
    subieron = sum(1 for it in items if it["score"] > it["prev_score"])
    nota = (f"{subieron} mejoraron y {len(items) - subieron} empeoraron. "
            "El veredicto se recalcula todos los días con el cierre.")
    hero = items[0]

    def _dm(s):
        try:
            d = datetime.date.fromisoformat(s)
            return f"desde el {d.day} de {_MESES[d.month - 1]}"
        except ValueError:
            return ""

    _dump({
        "tipo": "cambios",
        "kicker": "CAMBIÓ DE OPINIÓN",
        "title": "El mercado cambió de opinión",
        "subtitle": _dm(ch.get("prev_date", "")),
        "items": filas, "nota": nota,
    }, "\n".join([
        f"Cambios de veredicto — {_fecha_larga(datetime.date.today())}", "",
    ] + [f"{it['symbol']}: {it['prev_verdict']} → {it['verdict']} "
         f"({it['prev_score']} → {it['score']})" for it in items]
      + ["", nota] + CIERRE_CAPTION))
    return {"screen": f"?a={hero['symbol']}&c={hero['asset_class']}"}


# --------------------------------------------------------------- educativa ----
# Biblioteca portada de make-ig-placas.py. `q` es la pregunta grande (con la
# palabra en verde marcada con **), y despues o `body` (parrafo) o `items`.
_EDU = [
    {"q": "¿Qué mide el **score** de 0 a 100?",
     "body": "Resume en un solo número la tendencia, el momentum, el volumen y "
             "el riesgo técnico de un activo. Es una foto del panorama, no una "
             "predicción: sirve para comparar activos entre sí el mismo día."},
    {"q": "¿Por qué hay **cinco veredictos** y no dos?",
     "items": ["El mercado no es binario: casi todo es matiz.",
               "Entre COMPRA y EVITAR hay tres estados intermedios.",
               "Forzar todo a sí o no esconde justo lo que importa."]},
    {"q": "¿Por qué el veredicto **cambia** todos los días?",
     "items": ["Se recalcula con los datos de cada cierre.",
               "Si el panorama cambia, el veredicto cambia con él.",
               "Un veredicto viejo no describe el mercado de hoy."]},
    {"q": "Qué es el **RSI** y qué no te dice",
     "items": ["Mide si un activo viene muy comprado o muy vendido.",
               "Un RSI bajo no es “barato”: puede seguir cayendo.",
               "Sirve de contexto, no de señal de entrada sola."]},
    {"q": "Qué es una **media móvil** y para qué sirve",
     "items": ["Es el precio promedio de los últimos N días.",
               "Suaviza el ruido diario y deja ver la dirección.",
               "No predice: describe lo que ya viene pasando."]},
    {"q": "**Soporte** y **resistencia**, sin misterio",
     "items": ["Soporte: zona donde suelen aparecer compradores.",
               "Resistencia: zona donde suelen aparecer vendedores.",
               "No son paredes: son zonas donde el precio suele frenar."]},
    {"q": "Qué es el **stop loss** y por qué se define antes",
     "items": ["Es el precio al que aceptás que te equivocaste.",
               "Se fija ANTES de entrar, con la cabeza fría.",
               "Definirlo después es negociar con vos mismo."]},
    {"q": "**Riesgo / beneficio**: la cuenta que casi nadie hace",
     "items": ["Cuánto arriesgo contra cuánto puedo ganar.",
               "Si arriesgás 10 para ganar 10, tenés que acertar siempre.",
               "Con 1 a 3, alcanza con acertar una de cada tres."]},
    {"q": "Por qué **“ya bajó mucho”** no es una razón",
     "items": ["Una acción que cayó 50% puede caer otro 50%.",
               "El precio pasado no pone un piso.",
               "Lo barato lo define el negocio, no el gráfico."]},
    {"q": "Qué es un **CEDEAR**, en criollo",
     "items": ["Un certificado que representa acciones del exterior.",
               "Se compra en pesos, en el mercado argentino.",
               "Te da exposición a la empresa sin sacar la plata del país."]},
    {"q": "Qué es el **dólar CCL** y por qué te afecta",
     "items": ["Es el tipo de cambio implícito en comprar y vender activos.",
               "Los CEDEARs se mueven con la acción Y con el CCL.",
               "Podés acertar la acción y perder por el dólar."]},
    {"q": "Por qué el **volumen** importa tanto como el precio",
     "items": ["El volumen es cuánta gente respaldó ese movimiento.",
               "Una suba sin volumen es una suba sin convicción.",
               "Los movimientos que duran suelen venir acompañados."]},
    {"q": "**Diversificar** no es comprar diez cosas parecidas",
     "items": ["Diez tecnológicas caen juntas: eso no es diversificar.",
               "Es tener activos que no se mueven igual.",
               "Si todo sube junto, también va a bajar junto."]},
    {"q": "**Volatilidad** y **riesgo** no son lo mismo",
     "items": ["Volatilidad es cuánto se mueve el precio.",
               "Riesgo es la chance de perder plata de forma permanente.",
               "Un activo tranquilo también puede arruinarte."]},
    {"q": "Qué es el **drawdown** y por qué duele",
     "items": ["Es cuánto cayó tu cartera desde su punto más alto.",
               "Una caída del 50% necesita un 100% para recuperarse.",
               "Por eso proteger el capital vale más que acertar."]},
    {"q": "**Esperar** también es una posición",
     "body": "No entrar es, muchas veces, la mejor operación del día. El "
             "mercado no exige que estés siempre adentro: exige que entres "
             "cuando las señales acompañan, y que sepas por qué."},
]
_EDU_ROT = os.path.join(RAIZ, "ig", "media", "last_educativa.txt")


def build_educativa() -> dict:
    try:
        with open(_EDU_ROT, encoding="utf-8") as f:
            i = (int(f.read().strip()) + 1) % len(_EDU)
    except (OSError, ValueError):
        i = 0
    e = _EDU[i]
    print(f"placa educativa #{i}")
    q_plano = e["q"].replace("**", "")
    q_html = e["q"].replace("**", "\x00")
    parts = q_html.split("\x00")
    q_render = "".join(p if k % 2 == 0 else f'<span class="g">{p}</span>'
                       for k, p in enumerate(parts))

    payload = {"tipo": "educativa", "kicker": "APRENDÉ A LEERLO", "q_html": q_render}
    if e.get("items"):
        payload["items"] = e["items"]
        cuerpo_cap = [""] + [f"· {x}" for x in e["items"]]
    else:
        payload["body"] = e["body"]
        cuerpo_cap = ["", e["body"]]

    os.makedirs(os.path.dirname(_EDU_ROT), exist_ok=True)
    with open(_EDU_ROT, "w", encoding="utf-8") as f:
        f.write(str(i))

    _dump(payload, "\n".join([q_plano] + cuerpo_cap + CIERRE_CAPTION))
    return {}  # sin captura de la app


# -------------------------------------------------------------------- main ----
_BUILDERS = {
    "veredicto": build_veredicto, "termometro": build_termometro,
    "cambios": build_cambios, "educativa": build_educativa,
}


def build(tipo: str, *args) -> dict:
    fn = _BUILDERS.get(tipo)
    if not fn:
        raise SystemExit(f"tipo desconocido: {tipo}")
    return fn(*args) if tipo == "veredicto" else fn()


if __name__ == "__main__":
    a = sys.argv[1:]
    build(a[0] if a else "veredicto", *a[1:])

