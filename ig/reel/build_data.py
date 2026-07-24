"""Datos del veredicto para la animacion: endpoint -> data.js (+ caption).

  python ig/reel/build_data.py            # AAPL, accion
  python ig/reel/build_data.py GGAL
  python ig/reel/build_data.py BTC crypto

Se usa como modulo desde make-ig-reel.py. La escena no inventa nada: todo lo que
se ve sale de /verdict/<clase>/<simbolo>, el mismo endpoint que usa el producto.
La unica edicion es de forma (partir el texto de cada razon en titulo + detalle
usando el parentesis que ya trae, y elegir cuantas entran en pantalla).

Si hay un verdict.json al lado, se usa ese en vez de pedirlo: sirve para rehacer
un video con los datos de aquel dia.
"""
import json
import os
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
API = "https://app.verdikt.finance/verdict/{clase}/{sym}"

MAX_FILAS = 6  # razones en pantalla; el conteo muestra el total real igual
SIGNO = {"positivo": "+", "negativo": "-", "neutral": "="}

HASHTAGS = ("#inversiones #cedears #cripto #trading #bolsa #acciones "
            "#finanzas #mercados #argentina #análisis")


def pedir(sym: str, clase: str = "stock") -> dict:
    local = os.path.join(AQUI, "verdict.json")
    if os.path.exists(local):
        print("usando verdict.json local")
        with open(local, encoding="utf-8") as f:
            return json.load(f)
    url = API.format(clase=clase, sym=sym.upper())
    print("pidiendo", url)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def partir(texto: str):
    """'Tendencia alcista (medias 20>50>200)' -> ('Tendencia alcista', 'medias 20>50>200')"""
    if "(" in texto and texto.rstrip().endswith(")"):
        i = texto.index("(")
        return texto[:i].strip(), texto[i + 1:].rstrip().rstrip(")").strip()
    if ": " in texto:
        a, b = texto.split(": ", 1)
        return a.strip(), b.strip()
    return texto.strip(), ""


def _fila(r):
    tit, det = partir(r["text"])
    return {"signo": SIGNO.get(r["impact"], "="), "titulo": tit, "detalle": det,
            "tipo": r["impact"]}


def preparar(j: dict) -> dict:
    pos = [r for r in j["reasons"] if r["impact"] == "positivo"]
    neu = [r for r in j["reasons"] if r["impact"] == "neutral"]
    neg = [r for r in j["reasons"] if r["impact"] == "negativo"]

    # Se reserva lugar para una neutra y una en contra antes de llenar con las
    # positivas: un video que muestre solo lo bueno no es un veredicto, es
    # publicidad. Si el activo no tiene de esas, el hueco lo ocupan positivas.
    hueco = max(1, MAX_FILAS - len(neu[:1]) - len(neg[:1]))
    elegidas = (pos[:hueco] + neu[:1] + neg[:1])[:MAX_FILAS]
    # Si sobra lugar (un activo con pocas positivas, tipico de los bajistas) se
    # llena con el resto en vez de dejar filas vacias: BTC entraba con 3 de 5.
    for r in j["reasons"]:
        if len(elegidas) >= MAX_FILAS:
            break
        if r not in elegidas:
            elegidas.append(r)
    ORDEN_TIPO = {"positivo": 0, "neutral": 1, "negativo": 2}
    elegidas.sort(key=lambda r: ORDEN_TIPO[r["impact"]])
    razones = [_fila(r) for r in elegidas]

    # Los frenos, para el acto de "por que no 100". Lo que juega EN CONTRA va
    # primero: es la respuesta directa. Las neutras despues, que restan por no
    # aportar, no por estar mal.
    contras = [_fila(r) for r in (neg + neu)][:4]

    conteo = {"positivo": len(pos), "negativo": len(neg), "neutral": len(neu)}

    # Geometria del grafico. Se normaliza contra el minimo y maximo de TODAS las
    # series juntas para que el precio y las medias queden a la misma escala.
    ch = j["chart"]
    W, H, PAD = 1000.0, 400.0, 14.0
    todos = [v for k in ("closes", "ema200", "ema20") for v in ch[k] if v is not None]
    lo, hi = min(todos), max(todos)
    span = (hi - lo) or 1.0

    def puntos(vals):
        n = len(vals)
        out = []
        for i, v in enumerate(vals):
            if v is None:
                continue
            out.append(f"{i / (n - 1) * W:.1f},{H - PAD - (v - lo) / span * (H - PAD * 2):.1f}")
        return " ".join(out)

    return {
        "symbol": j["symbol"], "name": j["name"],
        "price": j["price"], "currency": j["currency"],
        "score": j["score"], "verdict": j["verdict"],
        "headline": j.get("headline", ""),
        "change_1m": j["change_1m"], "per": j.get("per"),
        "risk": (j.get("risk") or "").rstrip("."),
        "razones": razones, "contras": contras, "conteo": conteo,
        "total_razones": len(j["reasons"]),
        "ema200_last": round(ch["ema200"][-1], 2),
        "desde": ch["dates"][0], "hasta": ch["dates"][-1],
        "chart": {"w": W, "h": H, "closes": puntos(ch["closes"]),
                  "ema200": puntos(ch["ema200"]), "ema20": puntos(ch["ema20"])},
        "escala": ["EVITAR", "CAUTELA", "NEUTRAL", "ACUMULAR", "COMPRA"],
        "cedear": j.get("cedear"),
        "disclaimer": j.get("disclaimer", ""),
    }


def caption(d: dict) -> str:
    """Se DERIVA de los mismos datos que la animacion, para que el texto y el
    video no puedan contar cosas distintas."""
    c, n = d["conteo"], d["symbol"]
    partes = [f"¿Por qué {n} saca {d['score']} y no 100?", ""]

    favor = [r for r in d["razones"] if r["tipo"] == "positivo"]
    if favor:
        # "Entre ellas" solo si quedaron afuera: si se listan todas, sobra.
        prefijo = "Entre ellas: " if len(favor) < c["positivo"] else ""
        partes.append(f"{c['positivo']} señales a favor. {prefijo}".rstrip() + " " +
                      "; ".join(r["titulo"].lower() +
                                (f" ({r['detalle']})" if r["detalle"] else "")
                                for r in favor) + ".")
        partes.append("")
    neutras = [r for r in d["contras"] if r["tipo"] == "neutral"]
    if neutras:
        partes.append(f"{c['neutral']} neutras, que no aportan ni restan: " +
                      "; ".join(r["titulo"].lower() +
                                (f" ({r['detalle']})" if r["detalle"] else "")
                                for r in neutras) + ".")
        partes.append("")
    contra = [r for r in d["contras"] if r["tipo"] == "negativo"]
    if contra:
        partes.append(f"{c['negativo']} en contra: " +
                      "; ".join(r["titulo"].lower() +
                                (f" ({r['detalle']})" if r["detalle"] else "")
                                for r in contra) + ".")
        partes.append("")
    if d["risk"]:
        partes += [f"Qué vigilar: {d['risk'][0].lower() + d['risk'][1:]}.", ""]

    partes += [
        "Eso es un veredicto: un número y las razones detrás. "
        "Se recalcula todos los días con el cierre, porque el panorama cambia.",
        "",
        "Analizá cualquier acción, CEDEAR o cripto en app.verdikt.finance",
        "",
        d["disclaimer"] or ("Información educativa, no es asesoramiento financiero. "
                           "Invertís bajo tu propia responsabilidad."),
        "",
        HASHTAGS,
    ]
    return "\n".join(partes)


def escribir_datajs(d: dict) -> str:
    ruta = os.path.join(AQUI, "data.js")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("window.DATA = " + json.dumps(d, ensure_ascii=False) + ";\n")
    return ruta


def main():
    sym = (sys.argv[1] if len(sys.argv) > 1 else "AAPL").upper()
    clase = sys.argv[2] if len(sys.argv) > 2 else "stock"
    d = preparar(pedir(sym, clase))
    escribir_datajs(d)
    print(f"data.js listo: {d['symbol']} {d['score']}/100 {d['verdict']}")
    print(f"  razones en pantalla: {len(d['razones'])} de {d['total_razones']}")
    print(f"  conteo real: {d['conteo']}")


if __name__ == "__main__":
    main()
