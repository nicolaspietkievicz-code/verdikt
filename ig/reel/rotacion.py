"""Que activo le toca al proximo reel.

Una lista fija y un marcador con el ultimo publicado, para que no se repita ni
dependa de la fecha: si un dia falla, al siguiente sigue donde iba en vez de
saltearse uno.

AMPLIADA EL 2026-07-28. Eran 32 activos elegidos a mano, que a un reel por dia
alcanzaban de sobra. Al pasar a TRES por dia el mismo activo volvia cada 11
dias, asi que ahora entra el catalogo entero: 91 acciones y 44 criptos =
135 activos, o sea 45 dias sin repetir.

Los 135 estan VERIFICADOS uno por uno contra el camino real del reel
(build_data.pedir + preparar, no solo "responde el endpoint"): la escena
necesita razones y la serie de precios con sus dos medias, y si algo de eso
falta el render explota y ese dia no hay posteo. Al 28/07 pasaron los 135.

Si se suma un activo al catalogo, conviene correr esa verificacion antes de
meterlo aca.

BAJAS 2026-09-01: EOS e ICX salieron. Los proveedores de datos les cortaron el
feed (EOS se renombro a Vaulta), asi que /verdict/crypto/EOS devuelve 404. Como
el reel NO avanza la rotacion si el render falla, EOS quedo de tapon y frozo
los tres reels diarios desde el 28/08. Ademas de sacarlos de aca,
`siguiente_con_datos()` sondea el endpoint antes de elegir y saltea cualquier
activo que de 404.
"""
import urllib.error
import urllib.request

API_VERDICT = "https://app.verdikt.finance/verdict/{clase}/{sym}"

ACCIONES = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "MELI",
    "KO", "DIS", "JPM", "NFLX", "V", "MCD", "PYPL", "AVGO",
    "AMD", "INTC", "MU", "QCOM", "TXN", "CSCO", "ORCL", "IBM",
    "ADBE", "CRM", "PLTR", "COIN", "UBER", "ABNB", "SHOP", "WMT",
    "COST", "HD", "NKE", "SBUX", "PEP", "PG", "JNJ", "PFE",
    "MRK", "ABBV", "LLY", "UNH", "BAC", "WFC", "C", "GS",
    "MS", "XOM", "CVX", "CAT", "BA", "GM", "F", "T",
    "VZ", "GGAL", "YPF", "PAM", "BMA", "TEO", "CEPU", "CRESY",
    "GLOB", "VIST", "ASML", "SAP", "NVO", "NVS", "AZN", "SHEL",
    "TTE", "UL", "HSBC", "SNY", "BUD", "DEO", "BTI", "TSM",
    "BABA", "TM", "SONY", "BIDU", "JD", "PDD", "NIO", "INFY",
    "HDB", "SE", "LI",
]

CRIPTOS = [
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX",
    "MATIC", "LINK", "DOT", "LTC", "TRX", "UNI", "ATOM", "BCH",
    "XLM", "ETC", "FIL", "AAVE", "ALGO", "XMR", "XTZ",
    "MKR", "NEO", "DASH", "ZEC", "COMP", "SNX", "CRV", "YFI",
    "BAT", "MANA", "SAND", "GRT", "ENJ", "CHZ", "ZRX", "KSM",
    "QTUM", "OMG", "SUSHI",
]


def _armar():
    """Reparte las criptos PAREJAS entre las acciones.

    La version vieja iba una y una, y como hay mas del doble de acciones, al
    agotarse las criptos quedaba una cola larguisima de acciones seguidas. Con
    91 y 44 esa cola serian 47 acciones al hilo. Aca se calcula el
    paso y se intercalan a lo largo de toda la vuelta."""
    acciones = [("stock", s) for s in ACCIONES]
    criptos = [("crypto", s) for s in CRIPTOS]
    if not criptos:
        return acciones

    orden = list(acciones)
    paso = (len(acciones) + len(criptos)) / len(criptos)
    for i, par in enumerate(criptos):
        orden.insert(min(int(i * paso), len(orden)), par)
    return orden


ORDEN = _armar()


def siguiente(ultimo: str = ""):
    """Devuelve (clase, simbolo) del proximo activo. `ultimo` es 'clase:simbolo'
    tal como lo guarda el marcador."""
    claves = [f"{c}:{s}" for c, s in ORDEN]
    if ultimo in claves:
        return ORDEN[(claves.index(ultimo) + 1) % len(ORDEN)]
    return ORDEN[0]


def clave(clase: str, sym: str) -> str:
    return f"{clase}:{sym}"


def verdict_status(clase: str, sym: str):
    """Codigo HTTP de /verdict para ese activo. 404 = el proveedor le corto los
    datos (ticker muerto o renombrado, paso con EOS). None = timeout / 5xx /
    red: no concluyente, no es motivo para sacarlo de la rotacion."""
    url = API_VERDICT.format(clase=clase, sym=sym.upper())
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        print(f"  sonda {sym}: {e}")
        return None


def siguiente_con_datos(ultimo: str = "", *, saltos=12):
    """Como siguiente(), pero sondea /verdict y saltea los activos que dan 404.

    Devuelve (clase, simbolo, muertos) donde `muertos` es la lista de claves
    'clase:simbolo' que se saltearon: el llamador conviene que adelante su
    marcador sobre la ultima, para no volver a probarlas. Un solo ticker muerto
    justo despues del marcador congelaba los tres reels del dia, porque la
    rotacion no avanza cuando el render falla (paso EOS, 28/08)."""
    last = ultimo
    muertos = []
    for _ in range(saltos):
        c, s = siguiente(last)
        if verdict_status(c, s) == 404:
            print(f"{s} ({c}): sin datos (404), se saltea de la rotacion")
            muertos.append(clave(c, s))
            last = clave(c, s)
            continue
        return c, s, muertos
    raise RuntimeError(f"{saltos} activos seguidos sin datos: revisar el backend")


if __name__ == "__main__":
    print(f"{len(ORDEN)} activos en rotacion:")
    for k, (c, s) in enumerate(ORDEN, 1):
        print(f"  {k:2}. {c:6} {s}")
