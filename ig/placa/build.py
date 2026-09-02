"""Datos para la placa 'Veredicto del dia' -> data.js (+ caption).

  python ig/placa/build.py            # nro 1 del ranking del dia
  python ig/placa/build.py NVDA stock # forzar un activo

El nro 1 sale de /market/ranking (el mismo que abre la home de la app). El
detalle (score, razones, riesgo, grafico) sale de /verdict/<clase>/<sym>, via
ig/reel/build_data.py que ya tiene reintentos y normaliza el grafico.
"""
import datetime
import importlib.util
import json
import os
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
RANKING = "https://app.verdikt.finance/market/ranking"

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


def _fecha_larga(d: datetime.date) -> str:
    return f"{d.day} de {_MESES[d.month - 1]} de {d.year}"


def _numero_uno() -> tuple:
    with urllib.request.urlopen(RANKING, timeout=30) as r:
        data = json.loads(r.read())
    it = (data.get("items") or [None])[0]
    if not it:
        raise SystemExit("el ranking vino vacio")
    return it["symbol"], it["asset_class"]


def _titular(d: dict) -> str:
    """Una linea para el hero. Best effort con la IA; si no, templado."""
    try:
        if RAIZ not in sys.path:
            sys.path.insert(0, RAIZ)
        from ig.ia import redaccion
        return redaccion.redactar(d)["titular"]
    except Exception as e:
        print(f"  sin titular de IA ({type(e).__name__}: {e}); va el templado")
        return f"El veredicto de {d['name']} hoy"


def caption(d: dict, fecha: datetime.date) -> str:
    pos = [r for r in d["razones"] if r["tipo"] == "positivo"]
    neg = [r for r in d["razones"] if r["tipo"] == "negativo"]
    lineas = [
        f"Veredicto del dia — {_fecha_larga(fecha)}",
        "",
        f"{d['name']} ({d['symbol']}): {d['verdict']} · {d['score']}/100",
        "",
    ]
    if pos:
        lineas.append("A favor: " + "; ".join(r["titulo"].lower() for r in pos) + ".")
    if neg:
        lineas.append("En contra: " + "; ".join(r["titulo"].lower() for r in neg) + ".")
    if d.get("risk"):
        lineas += ["", f"Que vigilar: {d['risk'][0].lower() + d['risk'][1:]}."]
    lineas += [
        "",
        "El score va de 0 a 100 y resume el panorama tecnico. Se recalcula "
        "todos los dias con el cierre. No es una recomendacion de inversion.",
        "",
        "Analiza cualquier accion, CEDEAR o cripto en app.verdikt.finance",
        "",
        HASHTAGS,
    ]
    return "\n".join(lineas)


def build_veredicto(sym: str = "", clase: str = "") -> dict:
    if not sym:
        sym, clase = _numero_uno()
    clase = clase or "stock"
    print(f"placa de {sym} ({clase})")
    d = bd.preparar(bd.pedir(sym, clase))

    hoy = datetime.date.today()
    razones = d["razones"]
    fondos_dir = os.path.join(AQUI, "fondos")
    fondos = sorted(f for f in os.listdir(fondos_dir)
                    if f.endswith(".png")) if os.path.isdir(fondos_dir) else []
    payload = {
        "tipo": "veredicto",
        "fecha": _fecha_larga(hoy),
        "fondos": fondos,
        "kicker": "VEREDICTO DEL DÍA",
        "name": d["name"],
        "symbol": d["symbol"],
        "mercado": MERCADO.get(clase, clase.upper()),
        "score": d["score"],
        "verdict": d["verdict"],
        "titular": _titular(d),
        "price": d["price"],
        "currency": d["currency"],
        "change_1m": d["change_1m"],
        "per": d.get("per"),
        "risk": (d.get("risk") or "").rstrip("."),
        "afavor": [r["titulo"] for r in razones if r["tipo"] == "positivo"][:3],
        "encontra": [r["titulo"] for r in razones if r["tipo"] == "negativo"][:3],
        "conteo": d["conteo"],
        "chart": d["chart"],
        "desde": d["desde"],
        "hasta": d["hasta"],
    }

    with open(os.path.join(AQUI, "data.js"), "w", encoding="utf-8") as f:
        f.write("window.DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    with open(os.path.join(AQUI, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption(d, hoy))
    print(f"  data.js listo: {d['symbol']} {d['score']}/100 {d['verdict']}")
    return {"symbol": d["symbol"], "clase": clase}


if __name__ == "__main__":
    a = sys.argv[1:]
    build_veredicto(a[0] if a else "", a[1] if len(a) > 1 else "")
