"""Voz en off para el reel diario: escribe el guion, lo sintetiza y lo mezcla.

El guion NO es texto suelto: cada linea esta atada a un acto de scene.html
(las marcas A1..A6), asi la voz nombra lo que se esta viendo en ese momento y
no algo que ya paso o todavia no aparecio.

Se deriva de los MISMOS datos que la animacion y el caption, para que las tres
cosas no puedan contar versiones distintas.

  python narrar.py NVDA                      -> escribe el guion y lo lee
  python narrar.py NVDA --voz es_MX-claude-high --sobre ../reels/nvda-....mp4

Hace falta:  pip install piper-tts   +   los modelos de voz (se bajan con
python -m piper.download_voices --download-dir voces <nombre>)
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import wave

RAIZ = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "build_data", os.path.join(RAIZ, "build_data.py"))
bd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bd)

# Las mismas marcas que scene.html. Si alla cambian, cambian aca: la voz se
# desengancha de la imagen en silencio y no hay test que lo agarre.
A1, A2, A3, A4, A5, A6 = 0.00, 2.10, 5.60, 11.00, 13.70, 17.20
DURACION = 20.0

# Como se leen las cosas que estan escritas para el ojo, no para el oido.
VERDICTO_HABLADO = {
    "COMPRA": "compra", "ACUMULAR": "acumular", "NEUTRAL": "neutral",
    "CAUTELA": "cautela", "EVITAR": "evitar",
}


def ffmpeg() -> str:
    hallado = shutil.which("ffmpeg")
    if hallado:
        return hallado
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("Falta ffmpeg. Instalalo o corre: pip install imageio-ffmpeg")


def _plural(n, singular, plural):
    return f"{n} {singular}" if n == 1 else f"{n} {plural}"


def _sin_parentesis(txt: str) -> str:
    """Los detalles entre parentesis y los numeros sueltos ('RSI 43') se leen
    horrible. Para la voz se usa solo el titulo de la razon."""
    return txt.split("(")[0].strip().rstrip(".")


def guion(d: dict) -> list:
    """Devuelve [(segundo, texto)] listo para sintetizar.

    El reparto sigue los actos: se presenta el activo, se nombra el grafico
    mientras se dibuja, se cuentan las señales cuando entran las razones, se
    dice el veredicto cuando aparece el numero, y se cierra con la marca."""
    c = d["conteo"]
    nombre = d["name"] or d["symbol"]

    seg = [(A1 + 0.25, f"{nombre}, hoy.", True)]

    seg.append((A2 + 0.25, "Seis meses de precio y sus medias.", True))

    # El conteo, que es lo que explica el numero. Se dicen solo los grupos que
    # existen: "cero en contra" suena a relleno.
    partes = []
    if c["positivo"]:
        partes.append(_plural(c["positivo"], "señal a favor", "señales a favor"))
    if c["neutral"]:
        partes.append(_plural(c["neutral"], "neutra", "neutras"))
    if c["negativo"]:
        partes.append(_plural(c["negativo"], "en contra", "en contra"))
    if partes:
        seg.append((A3 + 0.30, ", ".join(partes[:-1]) +
                    (" y " if len(partes) > 1 else "") + partes[-1] + ".", True))

    # La razon de mas peso, dicha entera: es lo que le da sustancia al numero.
    principal = next((r for r in d["razones"] if r["tipo"] == "negativo"), None) \
        or next((r for r in d["razones"] if r["tipo"] == "positivo"), None)
    # Esta es OPCIONAL: los titulos de las razones varian mucho de largo y
    # algunos dias no entran. Antes que atropellar al veredicto, se cae.
    if principal:
        seg.append((A3 + 3.10, _sin_parentesis(principal["titulo"]) + ".", False))

    seg.append((A4 + 0.30,
                f"Veredicto: {VERDICTO_HABLADO.get(d['verdict'], d['verdict'].lower())}. "
                f"{d['score']} sobre 100.", True))

    # "verdikt.finance" leido como URL suena a robot deletreando. Se escribe
    # como se dice.
    seg.append((A6 + 0.20, "En verdikt punto finance.", True))

    return seg


def _dur_wav(path: str) -> float:
    with wave.open(path) as w:
        return w.getnframes() / float(w.getframerate())


def _decir_piper(texto: str, voz: str, data_dir: str, wav: str, velocidad: float) -> None:
    """TTS offline. Gratis y sin cuenta, pero SOLO habla español: las palabras
    en ingles las lee con fonetica española ("finance" -> fi-nan-se). Escribirlas
    como suenan tampoco sirve — se probo y el modelo termina nombrando los
    acentos. Sirve para probar el pipeline, no para publicar."""
    subprocess.run(
        [sys.executable, "-m", "piper", "-m", voz, "--data-dir", data_dir,
         "--length-scale", str(velocidad), "-f", wav],
        input=texto, text=True, check=True, encoding="utf-8",
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _decir_elevenlabs(texto: str, voz: str, wav: str, velocidad: float) -> None:
    """Modelo multilingue: reconoce solo que "finance" o "Goldman Sachs" son
    inglesas y las pronuncia como corresponde, sin marcarle nada. Por eso es el
    que mejor le cae a un guion en castellano lleno de nombres en ingles.

    Necesita ELEVENLABS_API_KEY en el entorno. `voz` es el id de la voz."""
    import json
    import urllib.request

    clave = os.environ.get("ELEVENLABS_API_KEY")
    if not clave:
        sys.exit("Falta ELEVENLABS_API_KEY en el entorno.")

    cuerpo = json.dumps({
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        # speed va de 0.7 a 1.2; nuestro `velocidad` es al reves (menor = mas
        # rapido, como el length-scale de piper), asi que se invierte.
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75,
                           "speed": round(2.0 - velocidad, 2)},
    }).encode()

    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=pcm_22050",
        data=cuerpo, method="POST",
        headers={"xi-api-key": clave, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        crudo = r.read()

    # Devuelve PCM pelado; se le pone cabecera wav para poder medirlo igual que
    # los de piper.
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(crudo)


def _decir_azure(texto: str, voz: str, wav: str, velocidad: float) -> None:
    """Voces neuronales de Azure. Gratis hasta 500 mil caracteres por mes.

    A diferencia de ElevenLabs no adivina el idioma, asi que las palabras en
    ingles se marcan una por una con <lang>. Es mas trabajo pero se controla
    exactamente como suena cada cosa."""
    import urllib.request

    clave = os.environ.get("AZURE_SPEECH_KEY")
    region = os.environ.get("AZURE_SPEECH_REGION", "brazilsouth")
    if not clave:
        sys.exit("Falta AZURE_SPEECH_KEY en el entorno.")

    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
            f'xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="es-MX">'
            f'<voice name="{voz}">'
            f'<prosody rate="{int((1 / velocidad - 1) * 100):+d}%">'
            f'{_marcar_ingles(texto)}'
            f'</prosody></voice></speak>')

    req = urllib.request.Request(
        f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml.encode("utf-8"), method="POST",
        headers={"Ocp-Apim-Subscription-Key": clave,
                 "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "riff-22050hz-16bit-mono-pcm",
                 "User-Agent": "verdikt"})
    with urllib.request.urlopen(req, timeout=120) as r:
        datos = r.read()
    with open(wav, "wb") as f:
        f.write(datos)


# Palabras del guion que son inglesas y hay que decir como tales. Solo la usa
# el motor de Azure; ElevenLabs las reconoce solo.
INGLESAS = ["finance", "Goldman Sachs", "UnitedHealth", "Salesforce",
            "JPMorgan", "Bank of America", "Home Depot", "Walmart",
            "Berkshire Hathaway", "Coinbase", "Airbnb", "PayPal"]


def _marcar_ingles(texto: str) -> str:
    for palabra in INGLESAS:
        if palabra in texto:
            texto = texto.replace(
                palabra, f'<lang xml:lang="en-US">{palabra}</lang>')
    return texto


def _decir(texto: str, voz: str, data_dir: str, wav: str, velocidad: float,
           motor: str = "piper") -> float:
    if motor == "elevenlabs":
        _decir_elevenlabs(texto, voz, wav, velocidad)
    elif motor == "azure":
        _decir_azure(texto, voz, wav, velocidad)
    else:
        _decir_piper(texto, voz, data_dir, wav, velocidad)
    return _dur_wav(wav)


# Cuanto se puede apurar una linea antes de que suene atropellada. Por debajo
# de 0.82 el sintetizador se come las silabas.
VELOCIDADES = [1.0, 0.92, 0.85, 0.82]


def sintetizar(seg: list, voz: str, data_dir: str, out_dir: str,
               velocidad: float = 1.0, motor: str = "piper") -> list:
    """Un wav por linea, ACOMODADO al hueco que le toca.

    Se sintetiza por separado y no todo junto a proposito: asi cada linea cae
    en su acto exacto. Y como el largo del habla depende de los datos del dia
    (hay titulos de razones de tres palabras y de doce), no alcanza con escribir
    un guion que entre "en general": cada linea se mide contra su hueco real y,
    si se pasa, primero se apura y despues —si es opcional— se cae.

    Sin esto la voz se pisa a si misma, que fue exactamente lo que paso en la
    primera prueba: 21,5 s de habla en un video de 20."""
    os.makedirs(out_dir, exist_ok=True)
    quedan = list(seg)

    while True:
        pistas = []
        recortar = None
        # Los avisos se juntan y se emiten SOLO si esta pasada es la definitiva:
        # una linea que no entra ahora puede entrar de sobra despues de que se
        # caiga la opcional que tenia adelante, y avisar de eso confunde.
        avisos = []

        for i, (t, texto, obligatoria) in enumerate(quedan):
            prox = quedan[i + 1][0] if i + 1 < len(quedan) else DURACION
            hueco = prox - t - 0.05

            wav = os.path.join(out_dir, f"voz{i:02d}.wav")
            for v in VELOCIDADES:
                if v > velocidad:
                    continue
                dur = _decir(texto, voz, data_dir, wav, v, motor)
                if dur <= hueco:
                    break
            else:
                dur = _dur_wav(wav)

            if dur > hueco:
                if not obligatoria:
                    recortar = i
                    print(f"  (se cae la linea opcional {i}: necesita "
                          f"{dur:.2f}s y el hueco es {hueco:.2f}s)")
                    break
                avisos.append(f"::warning::la linea {i} no entra ni apurada: "
                              f"{dur:.2f}s en un hueco de {hueco:.2f}s. "
                              f"Hay que acortar el texto del guion.")
            pistas.append((t, wav, dur, v))

        if recortar is None:
            for a in avisos:
                print(a)
            return pistas
        quedan.pop(recortar)


def mezclar(video: str, pistas: list, salida: str) -> str:
    """Mete la voz sobre el audio que el reel ya trae.

    La musica NO se baja a un volumen fijo: se usa sidechaincompress, o sea que
    se agacha sola cuando entra la voz y vuelve a subir cuando termina. Con un
    volumen fijo, los tramos sin voz quedan flojos."""
    entradas = ["-i", video]
    for _, wav, _, _ in pistas:
        entradas += ["-i", wav]

    # Cada linea se retrasa hasta su segundo y se suman en una sola pista.
    filtros = []
    etiquetas = []
    for i, (t, _, _, _) in enumerate(pistas):
        filtros.append(f"[{i + 1}:a]adelay={int(t * 1000)}|{int(t * 1000)},"
                       f"apad=whole_dur={DURACION}[v{i}]")
        etiquetas.append(f"[v{i}]")
    filtros.append("".join(etiquetas) + f"amix=inputs={len(pistas)}:normalize=0[voz]")
    filtros.append("[voz]asplit=2[voz1][llave]")
    filtros.append("[0:a][llave]sidechaincompress=threshold=0.03:ratio=12:"
                   "attack=15:release=350[musica]")
    filtros.append("[musica][voz1]amix=inputs=2:normalize=0:duration=first[out]")

    subprocess.run(
        [ffmpeg(), "-y", "-hide_banner", "-loglevel", "error", *entradas,
         "-filter_complex", ";".join(filtros),
         "-map", "0:v", "-map", "[out]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", salida],
        check=True)
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("simbolo")
    ap.add_argument("clase", nargs="?", default="stock")
    ap.add_argument("--motor", default="piper",
                    choices=["piper", "elevenlabs", "azure"],
                    help="piper: offline y gratis, pero no pronuncia ingles. "
                         "elevenlabs: multilingue, el que mejor le cae a esto. "
                         "azure: gratis hasta 500k caracteres, ingles marcado a mano")
    ap.add_argument("--voz", help="id o nombre de la voz segun el motor")
    ap.add_argument("--voces-dir", default=os.path.join(RAIZ, "voces"))
    ap.add_argument("--velocidad", type=float, default=1.0,
                    help="1.0 normal; menos de 1 habla mas rapido")
    ap.add_argument("--sobre", help="mp4 del reel sobre el que mezclar")
    ap.add_argument("--salida", default="reel-narrado.mp4")
    a = ap.parse_args()

    if not a.voz:
        a.voz = {"piper": "es_MX-claude-high",
                 "elevenlabs": "onwK4e9ZLuTAKqWW03F9",   # Daniel, multilingue
                 "azure": "es-MX-JorgeNeural"}[a.motor]

    d = bd.preparar(bd.pedir(a.simbolo.upper(), a.clase))
    seg = guion(d)

    print(f"\nGuion de {d['name']} ({d['verdict']} {d['score']}):\n")
    for t, texto, obligatoria in seg:
        print(f"  {t:5.2f}s  {texto}" + ("" if obligatoria else "   [opcional]"))

    if not a.sobre:
        print("\n(sin --sobre no se sintetiza nada: era solo el guion)")
        return

    tmp = os.path.join(RAIZ, "voz_tmp")
    pistas = sintetizar(seg, a.voz, a.voces_dir, tmp, a.velocidad, a.motor)
    print()
    for i, (t, _, dur, v) in enumerate(pistas):
        apuro = "" if v == 1.0 else f"  (apurada a {v})"
        print(f"  linea {i}: {t:5.2f}s + {dur:4.2f}s = termina {t + dur:5.2f}s{apuro}")
    habla = sum(p[2] for p in pistas)
    print(f"\n  habla {habla:.1f}s de {DURACION:.0f}s "
          f"({habla / DURACION * 100:.0f}% del reel)")

    mezclar(a.sobre, pistas, a.salida)
    print("\nlisto:", a.salida)


if __name__ == "__main__":
    main()
