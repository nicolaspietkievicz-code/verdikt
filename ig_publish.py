"""Publica un posteo en el FEED de Instagram por la Graph API oficial de Meta.

Es el camino soportado por Instagram para publicar solo (nada de automatizar el
login humano). Flujo en dos pasos:
  1) crear un "contenedor" de media con la URL PUBLICA de la imagen + el caption;
  2) esperar a que el contenedor quede FINISHED y publicarlo.

Necesita, en el entorno:
  IG_USER_ID       -> id del usuario de Instagram (cuenta Empresa/Creador)
  IG_ACCESS_TOKEN  -> token de larga duracion con permisos de publicacion

Cómo conseguir esos dos valores está en SETUP-IG.md. La imagen DEBE estar en una
URL publica https (la Graph API la baja por URL; no se suben bytes directo).

Publica una imagen sola, un carrusel de hasta 10 (un contenedor hijo por imagen
mas uno padre que los lista) o un reel.

Uso:
  python ig_publish.py --image-url https://.../portada.png --caption-file cap.txt
  python ig_publish.py --image-urls https://.../1.png,https://.../2.png --caption-file cap.txt
  python ig_publish.py --image-url https://.../x.png --caption "hola" --dry-run
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"


class PublishError(Exception):
    pass


def _post(path: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{GRAPH}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise PublishError(f"HTTP {e.code} en {path}: {body}")


def _get(path: str, params: dict) -> dict:
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{GRAPH}/{path}?{q}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise PublishError(f"HTTP {e.code} en {path}: {body}")


def _creds(user_id, token):
    user_id = user_id or os.environ.get("IG_USER_ID")
    token = token or os.environ.get("IG_ACCESS_TOKEN")
    if not user_id or not token:
        raise PublishError("Falta IG_USER_ID o IG_ACCESS_TOKEN en el entorno.")
    return user_id, token


def _aviso_dry(kind: str, url: str, caption: str, user_id, token) -> str:
    head = caption.strip().splitlines()[0] if caption.strip() else ""
    print("[dry-run] NO se publica. Se enviaria:")
    print(f"  {kind:10}:", url)
    print("  caption   :", head, f"({len(caption)} chars)")
    print("  IG_USER_ID:", "seteado" if (user_id or os.environ.get("IG_USER_ID")) else "FALTA")
    print("  token     :", "seteado" if (token or os.environ.get("IG_ACCESS_TOKEN")) else "FALTA")
    return "dry-run"


def _esperar(cid: str, token: str, intentos: int, espera: float) -> None:
    """Espera a que el contenedor quede FINISHED. El video tarda mucho mas que
    la imagen: Instagram lo baja, lo transcodifica y recien ahi habilita el
    publish, asi que se le da bastante mas margen."""
    for i in range(intentos):
        st = _get(cid, {"fields": "status_code,status", "access_token": token})
        code = st.get("status_code")
        if code == "FINISHED":
            return
        if code == "ERROR":
            raise PublishError(f"El contenedor quedo en ERROR: {st}")
        if i and i % 5 == 0:
            print(f"  ...procesando ({code}), {int(i * espera)}s")
        time.sleep(espera)
    raise PublishError("El contenedor nunca llego a FINISHED (timeout).")


def _publicar(user_id: str, token: str, cid: str) -> str:
    pub = _post(f"{user_id}/media_publish", {"creation_id": cid, "access_token": token})
    mid = pub.get("id")
    if not mid:
        raise PublishError(f"No se publico: {pub}")
    return mid


def publish(image_url: str, caption: str, *, user_id=None, token=None, dry_run=False) -> str:
    """Publica una imagen en el feed. Devuelve el id del posteo (o 'dry-run')."""
    if dry_run:
        return _aviso_dry("image_url", image_url, caption, user_id, token)
    user_id, token = _creds(user_id, token)

    cont = _post(f"{user_id}/media", {
        "image_url": image_url, "caption": caption, "access_token": token,
    })
    cid = cont.get("id")
    if not cid:
        raise PublishError(f"No se creo el contenedor: {cont}")

    _esperar(cid, token, intentos=25, espera=3)
    return _publicar(user_id, token, cid)


def publish_carousel(image_urls: list, caption: str, *, user_id=None, token=None,
                     dry_run=False) -> str:
    """Publica varias imagenes como UN carrusel. Son tres pasos en vez de dos:
    un contenedor "hijo" por imagen (is_carousel_item), un contenedor padre que
    los lista, y recien ahi el publish. El caption va en el padre.

    Instagram admite hasta 10 imagenes; si llegan mas, se corta y se avisa."""
    if len(image_urls) == 1:
        return publish(image_urls[0], caption, user_id=user_id, token=token, dry_run=dry_run)
    if len(image_urls) > 10:
        print(f"::warning::{len(image_urls)} imagenes: se publican las primeras 10.")
        image_urls = image_urls[:10]

    if dry_run:
        print(f"[dry-run] NO se publica. Carrusel de {len(image_urls)} imagenes:")
        for i, u in enumerate(image_urls, 1):
            print(f"  {i:02d}. {u}")
        return _aviso_dry("carrusel", f"{len(image_urls)} imagenes", caption, user_id, token)
    user_id, token = _creds(user_id, token)

    hijos = []
    for i, url in enumerate(image_urls, 1):
        cont = _post(f"{user_id}/media", {
            "image_url": url, "is_carousel_item": "true", "access_token": token,
        })
        cid = cont.get("id")
        if not cid:
            raise PublishError(f"No se creo el contenedor de la imagen {i}: {cont}")
        print(f"  hijo {i:02d}/{len(image_urls)}: {cid}")
        hijos.append(cid)

    padre = _post(f"{user_id}/media", {
        "media_type": "CAROUSEL",
        "children": ",".join(hijos),
        "caption": caption,
        "access_token": token,
    })
    cid = padre.get("id")
    if not cid:
        raise PublishError(f"No se creo el contenedor del carrusel: {padre}")
    print("carrusel:", cid)

    _esperar(cid, token, intentos=40, espera=3)
    return _publicar(user_id, token, cid)


def publish_reel(video_url: str, caption: str, *, user_id=None, token=None,
                 dry_run=False, share_to_feed=True) -> str:
    """Publica un REEL (video vertical). Mismo flujo de dos pasos que la imagen,
    con dos diferencias: el contenedor se crea con media_type=REELS + video_url,
    y hay que esperarle mucho mas al transcode.

    share_to_feed=True hace que ademas aparezca en la grilla del perfil, no solo
    en la pestaña de reels: si no, el perfil se ve vacio para quien lo visita."""
    if dry_run:
        return _aviso_dry("video_url", video_url, caption, user_id, token)
    user_id, token = _creds(user_id, token)

    cont = _post(f"{user_id}/media", {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true" if share_to_feed else "false",
        "access_token": token,
    })
    cid = cont.get("id")
    if not cid:
        raise PublishError(f"No se creo el contenedor del reel: {cont}")
    print("contenedor:", cid)

    # 5 min de margen: un MP4 de pocos MB suele estar listo en menos de uno,
    # pero si Instagram se demora no queremos perder el posteo por impaciencia.
    _esperar(cid, token, intentos=60, espera=5)
    return _publicar(user_id, token, cid)


def main():
    ap = argparse.ArgumentParser()
    m = ap.add_mutually_exclusive_group(required=True)
    m.add_argument("--image-url")
    m.add_argument("--image-urls", help="varias URLs separadas por coma: publica un carrusel")
    m.add_argument("--video-url", help="publica como REEL")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--caption")
    g.add_argument("--caption-file")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    caption = a.caption
    if a.caption_file:
        with open(a.caption_file, encoding="utf-8") as f:
            caption = f.read()

    if a.video_url:
        mid = publish_reel(a.video_url, caption, dry_run=a.dry_run)
    elif a.image_urls:
        urls = [u.strip() for u in a.image_urls.split(",") if u.strip()]
        mid = publish_carousel(urls, caption, dry_run=a.dry_run)
    else:
        mid = publish(a.image_url, caption, dry_run=a.dry_run)
    print("publicado:", mid)


if __name__ == "__main__":
    main()
