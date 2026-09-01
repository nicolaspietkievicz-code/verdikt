"""Copy del reel diario escrito por IA a partir de los datos del veredicto.

La IA mejora el GANCHO (las primeras lineas del caption, el titular, un brief
para la caratula). El cierre fijo del caption -- linea educativa, CTA a
app.verdikt.finance, disclaimer, hashtags -- lo sigue poniendo build_data.py:
la IA no toca el boilerplate.

Si algo falla (sin key, timeout, JSON roto), redactar() tira IAError y el
orquestador cae al caption templado de siempre."""
import json

from ig.ia.cliente import IAError, chat

__all__ = ["redactar", "SYSTEM"]

SYSTEM = """\
Sos el redactor de la cuenta de Instagram de Verdikt, una app que le pone un
veredicto (COMPRA / ACUMULAR / NEUTRAL / CAUTELA / EVITAR) y un puntaje de 0 a
100 a acciones, CEDEARs y cripto, recalculado cada dia con el cierre.

Voz:
- Castellano rioplatense, vos (no tu). Tono de terminal financiera: sobrio,
  preciso, sin humo. Cero emojis, cero signos de exclamacion, cero mayusculas
  sostenidas para enfatizar.
- Primero el para que: que aprende quien lee, no "mira esto".
- Nada de promesas de rentabilidad ni de "esta accion va a subir". Se describe
  lo que dice el analisis y por que, no se recomienda comprar.
- Nunca inventes un dato que no este en la entrada.

Te paso los datos de un activo y devolves SOLO un objeto JSON con estas claves:
- "gancho": 2 a 4 palabras, el titulo que iria arriba de todo. Sin punto final.
- "titular": una sola linea (max 90 caracteres), el angulo de hoy para ese
  activo: la tension entre lo que juega a favor y en contra, o el dato que
  manda. Sin signos de exclamacion.
- "caption_cuerpo": 2 a 4 lineas (separadas por \\n) que abren el caption de
  Instagram. La primera linea tiene que hacer frenar el scroll. Podes citar el
  score, el veredicto, alguna razon concreta. No cierres con CTA ni hashtags:
  eso se agrega despues.
- "brief_caratula": un PROMPT completo en espanol, listo para pegar en ChatGPT
  y que genere la portada del reel (formato vertical 9:16, para Instagram).
  Tiene que ser CREATIVO y DISTINTO cada vez: parti de una metafora visual
  concreta que nazca del angulo de hoy (un rebote que choca un techo, una
  grieta en una estructura, una linea que se aleja de su promedio, dos fuerzas
  que se empujan...). No repitas siempre "grafico de velas". El prompt debe
  cubrir, en frases claras:
  * el concepto / la metafora visual central
  * la composicion (donde va cada cosa, que queda vacio para el texto abajo)
  * la paleta: fondo casi negro (#07090C), un solo acento verde apagado
    (#2FBF71), grises frios; nada estridente
  * elementos concretos a dibujar
  * estilo: editorial financiero, plano, preciso, con aire; NADA de personas,
    caras, manos, fotos, logos de empresas reales, estetica de stock, 3D
    brillante, ni emojis
  * dejar el tercio inferior despejado para sobreimprimir el ticker y el score
  Escribilo como instruccion directa a un generador de imagenes, 4 a 8 frases."""


def _entrada(d: dict) -> str:
    razones = "\n".join(
        f"  [{r['tipo']}] {r['titulo']}" + (f" ({r['detalle']})" if r['detalle'] else "")
        for r in d.get("razones", [])
    )
    c = d.get("conteo", {})
    return (
        f"Activo: {d['name']} ({d['symbol']}) - {d.get('currency', '')}\n"
        f"Veredicto: {d['verdict']}  Score: {d['score']}/100\n"
        f"Precio: {d['price']}  Cambio 1 mes: {d.get('change_1m', 'n/d')}\n"
        f"PER: {d.get('per', 'n/d')}\n"
        f"Titular del motor: {d.get('headline', '')}\n"
        f"Que vigilar: {d.get('risk', '')}\n"
        f"Conteo de razones: {c.get('positivo', 0)} a favor, "
        f"{c.get('neutral', 0)} neutras, {c.get('negativo', 0)} en contra\n"
        f"Razones en pantalla:\n{razones}\n"
    )


_CLAVES = ("gancho", "titular", "caption_cuerpo", "brief_caratula")


def redactar(d: dict) -> dict:
    """Devuelve {gancho, titular, caption_cuerpo, brief_caratula}. Tira IAError
    si no hay key o la respuesta no sirve."""
    crudo = chat(SYSTEM, _entrada(d), json_out=True)
    try:
        obj = json.loads(crudo)
    except json.JSONDecodeError:
        raise IAError(f"El modelo no devolvio JSON: {crudo[:300]}")
    faltan = [k for k in _CLAVES if not str(obj.get(k, "")).strip()]
    if faltan:
        raise IAError(f"Faltan claves en el copy: {faltan}")
    return {k: str(obj[k]).strip() for k in _CLAVES}
