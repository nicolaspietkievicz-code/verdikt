"""Que activo le toca al reel de hoy.

Misma idea que la rotacion de placas: una lista fija y un marcador con el ultimo
publicado, para que no se repita ni dependa de la fecha (si un dia falla, al otro
sigue donde iba en vez de saltearse uno).

Se alternan accion y cripto a proposito: el feed queda variado y no se hacen
tandas de una sola clase. Con 32 activos, un mes largo sin repetir.

Los 32 estan verificados contra /verdict/<clase>/<simbolo>: los que no responden
o vienen sin serie de precios no entran, porque romperian el posteo de ese dia.
"""

ACCIONES = [
    "AAPL", "NVDA", "YPF", "KO", "MELI", "JPM", "TSLA", "AMD",
    "GGAL", "MSFT", "VIST", "GOOGL", "PBR", "META", "BMA", "AMZN",
    "INTC", "DIS", "BABA", "NFLX",
]

CRIPTOS = [
    "BTC", "ETH", "XMR", "LINK", "SOL", "LTC", "ADA", "XRP",
    "AVAX", "DOGE", "BNB", "DOT",
]


def _armar():
    """Intercala acciones y criptos. Hay mas acciones que criptos, asi que al
    final del ciclo quedan acciones seguidas: preferible a repetir cripto."""
    orden, i, j = [], 0, 0
    while i < len(ACCIONES) or j < len(CRIPTOS):
        if i < len(ACCIONES):
            orden.append(("stock", ACCIONES[i])); i += 1
        if j < len(CRIPTOS):
            orden.append(("crypto", CRIPTOS[j])); j += 1
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


if __name__ == "__main__":
    print(f"{len(ORDEN)} activos en rotacion:")
    for k, (c, s) in enumerate(ORDEN, 1):
        print(f"  {k:2}. {c:6} {s}")
