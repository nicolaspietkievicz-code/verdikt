"""Prepara los datos del veredicto para la animacion: endpoint -> data.js

Uso:
  python ig/reel/build_data.py            # AAPL, accion
  python ig/reel/build_data.py GGAL       # otra accion / CEDEAR
  python ig/reel/build_data.py BTC crypto # cripto

Deja data.js al lado de scene.html. Si ya hay un verdict.json local lo usa en
vez de pedirlo, para poder rehacer un video con los datos de ese dia.

La escena no inventa nada. Todo lo que se ve sale del endpoint del producto
(/verdict/stock/AAPL): el score, las razones con su signo, el riesgo, el PER y
la serie de cierres. La unica edicion es de forma: se parte el texto de cada
razon en titulo + detalle usando el parentesis que ya trae, y se eligen 6 de las
9 para que se lean en un celular. El conteo completo (6 a favor / 2 neutras /
1 en contra) se muestra igual, asi que no se esconde ninguna.
"""
import json
import os
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
API = "https://app.verdikt.finance/verdict/{clase}/{sym}"

MAX_FILAS = 6  # cuantas razones entran en pantalla; el conteo muestra todas

SIGNO = {"positivo": "+", "negativo": "-", "neutral": "="}

sym = (sys.argv[1] if len(sys.argv) > 1 else "AAPL").upper()
clase = sys.argv[2] if len(sys.argv) > 2 else "stock"

local = os.path.join(AQUI, "verdict.json")
if os.path.exists(local):
    print("usando verdict.json local")
    with open(local, encoding="utf-8") as f:
        j = json.load(f)
else:
    url = API.format(clase=clase, sym=sym)
    print("pidiendo", url)
    with urllib.request.urlopen(url, timeout=30) as r:
        j = json.loads(r.read())


def partir(texto):
    """'Tendencia alcista (medias 20>50>200)' -> ('Tendencia alcista', 'medias 20>50>200')"""
    if "(" in texto and texto.rstrip().endswith(")"):
        i = texto.index("(")
        return texto[:i].strip(), texto[i + 1:].rstrip().rstrip(")").strip()
    if ": " in texto:
        a, b = texto.split(": ", 1)
        return a.strip(), b.strip()
    return texto.strip(), ""


# Se reserva lugar para una neutra y una en contra: un video que muestre solo lo
# bueno no es un veredicto, es publicidad. El resto se llena con las positivas.
pos = [r for r in j["reasons"] if r["impact"] == "positivo"]
neu = [r for r in j["reasons"] if r["impact"] == "neutral"]
neg = [r for r in j["reasons"] if r["impact"] == "negativo"]
hueco = max(1, MAX_FILAS - len(neu[:1]) - len(neg[:1]))
elegidas = (pos[:hueco] + neu[:1] + neg[:1])[:MAX_FILAS]

razones = []
for r in elegidas:
    tit, det = partir(r["text"])
    razones.append({"signo": SIGNO.get(r["impact"], "="), "titulo": tit, "detalle": det})

conteo = {"positivo": 0, "negativo": 0, "neutral": 0}
for r in j["reasons"]:
    conteo[r["impact"]] = conteo.get(r["impact"], 0) + 1

# Los frenos, para el tramo de "por que no 100": lo que juega en contra y lo que
# no aporta. Salen del mismo campo impact, no de una lectura mia.
contras = []
for r in j["reasons"]:
    if r["impact"] in ("negativo", "neutral"):
        tit, det = partir(r["text"])
        contras.append({"signo": SIGNO[r["impact"]], "titulo": tit, "detalle": det,
                        "tipo": r["impact"]})
# Lo que juega EN CONTRA va primero: es la respuesta directa a "por que no 100".
# Las neutras despues, que restan por no aportar, no por estar mal.
contras.sort(key=lambda r: 0 if r["tipo"] == "negativo" else 1)

# ── Geometria del grafico ────────────────────────────────────────────────────
# Se normaliza contra el minimo y maximo de TODAS las series juntas para que el
# precio y la media de 200 queden a la misma escala (si no, la media parece
# pegada al precio y se pierde justamente lo que la razon #2 esta diciendo).
ch = j["chart"]
W, H, PAD = 1000.0, 400.0, 14.0
series = {k: ch[k] for k in ("closes", "ema200", "ema20")}
todos = [v for s in series.values() for v in s if v is not None]
lo, hi = min(todos), max(todos)
span = (hi - lo) or 1.0


def puntos(vals):
    n = len(vals)
    out = []
    for i, v in enumerate(vals):
        if v is None:
            continue
        x = i / (n - 1) * W
        y = H - PAD - (v - lo) / span * (H - PAD * 2)
        out.append(f"{x:.1f},{y:.1f}")
    return " ".join(out)


data = {
    "symbol": j["symbol"],
    "name": j["name"],
    "price": j["price"],
    "currency": j["currency"],
    "score": j["score"],
    "verdict": j["verdict"],
    "change_1m": j["change_1m"],
    "per": j["per"],
    "risk": j["risk"].rstrip("."),
    "razones": razones,
    "contras": contras,
    "conteo": conteo,
    "total_razones": len(j["reasons"]),
    "ema200_last": round(ch["ema200"][-1], 2),
    "desde": ch["dates"][0],
    "hasta": ch["dates"][-1],
    "chart": {"w": W, "h": H,
              "closes": puntos(ch["closes"]),
              "ema200": puntos(ch["ema200"]),
              "ema20": puntos(ch["ema20"])},
    "escala": ["EVITAR", "CAUTELA", "NEUTRAL", "ACUMULAR", "COMPRA"],
    "cedear": j["cedear"],
}

with open(os.path.join(AQUI, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")

print(f"data.js listo: {j['symbol']} {j['score']}/100 {j['verdict']}")
print(f"  razones en pantalla: {len(razones)} de {len(j['reasons'])}")
print(f"  conteo real: {conteo}")
print(f"  rango grafico: {lo:.2f} - {hi:.2f}")
