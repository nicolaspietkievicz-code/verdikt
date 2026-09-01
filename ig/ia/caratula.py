"""Caratulas del reel: 3 propuestas de IA + una de plantilla como respaldo.

La IA (gpt-image-1) dibuja la portada a partir de un brief; despues Pillow la
encaja a 1080x1920 y le monta ENCIMA la marca (wordmark + dominio + ticker +
veredicto), asi la pieza se lee como Verdikt aunque el modelo se vaya de tema.

plantilla() no usa IA: arma una portada sobria con la identidad del kit (grilla,
la V, el ticker grande, la barra de 0 a 100). Es lo que se publica si el usuario
rechaza las tres de IA (caratula: 0) o si no hay OPENAI_API_KEY.

Regla de fondo: nada de IA se publica sin que el usuario lo apruebe. Ver
[[diseno-no-ia]] y ig_pendiente.py."""
import importlib.util
import io
import os

from PIL import Image, ImageDraw, ImageFilter

from ig.ia.cliente import IAError, imagenes

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_mc_spec = importlib.util.spec_from_file_location(
    "make_ig_cambios", os.path.join(_RAIZ, "make-ig-cambios.py"))
mc = importlib.util.module_from_spec(_mc_spec)
_mc_spec.loader.exec_module(mc)

S = 2
W, H = 1080 * S, 1920 * S

_PREAMBULO = (
    "Vertical 2:3 social cover for a financial-analysis app called Verdikt. "
    "Sober editorial finance aesthetic, NOT playful. Very dark near-black "
    "background (#07090C) with a faint technical grid and thin data lines. "
    "Restrained palette: deep charcoal, muted green (#2FBF71) as the only "
    "accent, cool grey. Abstract shapes, candlestick-like bars, a subtle "
    "upward recovery curve. No people, no faces, no hands, no photorealism, "
    "no logos of real companies, no stock-photo look, no lens flare, no 3D "
    "render, no emoji, no gradients of many colors. Flat, precise, a lot of "
    "negative space in the lower third for text to be added later. "
)


def _encajar(png_bytes: bytes) -> Image.Image:
    """Escala a cubrir 1080x1920 y recorta al centro."""
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    escala = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * escala), round(im.height * escala)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = (im.height - H) // 2
    return im.crop((x, y, x + W, y + H))


def _marca(im: Image.Image, d: dict) -> Image.Image:
    """Monta la marca sobre la imagen (venga de IA o de plantilla)."""
    d_ = ImageDraw.Draw(im, "RGBA")
    vcol = mc.VCOL.get(d["verdict"], mc.GREEN)

    # Scrim de abajo para que el pie se lea sobre cualquier imagen.
    scrim = Image.new("RGBA", (W, int(H * 0.30)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    for i in range(scrim.height):
        sd.line([(0, i), (W, i)], fill=(7, 9, 12, int(235 * i / scrim.height)))
    im.paste(scrim, (0, H - scrim.height), scrim)

    pad = 60 * S
    # Cabecera: la V + VERDIKT
    ts = 74 * S
    d_.rounded_rectangle([pad, pad, pad + ts, pad + ts], radius=ts * 0.22,
                         fill=mc.CARD, outline=mc.BORDER, width=2)
    mc.draw_v(d_, pad + ts * 0.14, pad + ts * 0.14, ts * 0.72)
    wf = mc._font(["CascadiaCode-Bold.ttf", "consolab.ttf", "DejaVuSansMono-Bold.ttf"], 34 * S)
    d_.text((pad + ts + 22 * S, pad + ts / 2), "VERDIKT", font=wf, fill=mc.TEXT, anchor="lm")

    # Ticker grande + pill del veredicto, abajo a la izquierda.
    tf = mc._font(["CascadiaCode-Bold.ttf", "consolab.ttf", "DejaVuSansMono-Bold.ttf"], 132 * S)
    baseY = H - pad - 150 * S
    d_.text((pad, baseY), d["symbol"], font=tf, fill=mc.TEXT, anchor="ls")
    pf = mc._font(["Inter-Bold.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"], 30 * S)
    label = f"{d['verdict']}  {d['score']}/100"
    tw = d_.textlength(label, font=pf)
    py = baseY + 26 * S
    d_.rounded_rectangle([pad, py, pad + tw + 44 * S, py + 58 * S], radius=10 * S,
                         fill=(*vcol, 38), outline=(*vcol, 255), width=2)
    d_.text((pad + 22 * S, py + 29 * S), label, font=pf, fill=vcol, anchor="lm")

    # Dominio, abajo a la derecha.
    df = mc._font(["CascadiaCode-Regular.ttf", "consola.ttf", "DejaVuSansMono.ttf"], 26 * S)
    d_.text((W - pad, H - pad), "app.verdikt.finance", font=df, fill=mc.GREEN, anchor="rs")
    return im


def _fondo_plantilla(d: dict) -> Image.Image:
    """Fondo de la caratula de respaldo: grilla + halo, sin IA."""
    im = Image.new("RGB", (W, H), mc.BG)
    dr = ImageDraw.Draw(im)
    cell = 42 * S
    for x in range(0, W, cell):
        dr.line([(x, 0), (x, H)], fill=(24, 28, 36), width=1)
    for y in range(0, H, cell):
        dr.line([(0, y), (W, y)], fill=(24, 28, 36), width=1)
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([W * 0.02, -H * 0.28, W * 0.98, H * 0.30], fill=(47, 191, 113, 60))
    halo = halo.filter(ImageFilter.GaussianBlur(160))
    im.paste(halo, (0, 0), halo)

    # Titular (el angulo de hoy), en el cuerpo de la placa.
    tf = mc._font(["Inter-Regular.ttf", "segoeui.ttf", "DejaVuSans.ttf"], 46 * S)
    titular = (d.get("_titular") or d.get("headline") or "").strip()
    if titular:
        _texto_envuelto(dr, titular, tf, 60 * S, H * 0.42, W - 120 * S, mc.TEXT, 62 * S)
    return im


def _texto_envuelto(dr, texto, font, x, y, max_w, fill, lh):
    palabras = texto.split()
    linea = ""
    for p in palabras:
        prueba = (linea + " " + p).strip()
        if dr.textlength(prueba, font=font) > max_w and linea:
            dr.text((x, y), linea, font=font, fill=fill)
            y += lh
            linea = p
        else:
            linea = prueba
    if linea:
        dr.text((x, y), linea, font=font, fill=fill)


def _guardar(im: Image.Image, ruta: str) -> str:
    im.resize((1080, 1920), Image.LANCZOS).save(ruta, optimize=True)
    return ruta


def plantilla(d: dict, ruta: str, *, titular: str = "") -> str:
    """Caratula de respaldo, sin IA. Devuelve la ruta."""
    dd = dict(d, _titular=titular)
    im = _fondo_plantilla(dd)
    im = _marca(im, d)
    return _guardar(im, ruta)


def generar(d: dict, brief: str, out_dir: str, *, n: int = 3,
            titular: str = "") -> list:
    """3 caratulas de IA, ya con la marca montada. Tira IAError si la IA falla:
    el orquestador cae a plantilla()."""
    prompt = _PREAMBULO
    if titular:
        prompt += f'Theme of the piece: "{titular}". '
    prompt += f"Art direction: {brief}"

    pngs = imagenes(prompt, n=n)
    rutas = []
    for i, raw in enumerate(pngs, 1):
        im = _marca(_encajar(raw), d)
        rutas.append(_guardar(im, os.path.join(out_dir, f"cover-{i}.png")))
    return rutas
