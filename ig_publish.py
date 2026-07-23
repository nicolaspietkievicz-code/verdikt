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

Uso:
  python ig_publish.py --image-url https://.../cambios.png --caption-file cap.txt
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


def publish(image_url: str, caption: str, *, user_id=None, token=None, dry_run=False) -> str:
    """Publica una imagen en el feed. Devuelve el id del posteo (o 'dry-run')."""
    user_id = user_id or os.environ.get("IG_USER_ID")
    token = token or os.environ.get("IG_ACCESS_TOKEN")

    if dry_run:
        head = caption.strip().splitlines()[0] if caption.strip() else ""
        print("[dry-run] NO se publica. Se enviaria:")
        print("  image_url :", image_url)
        print("  caption   :", head, f"({len(caption)} chars)")
        print("  IG_USER_ID:", "seteado" if user_id else "FALTA")
        print("  token     :", "seteado" if token else "FALTA")
        return "dry-run"

    if not user_id or not token:
        raise PublishError("Falta IG_USER_ID o IG_ACCESS_TOKEN en el entorno.")

    # 1) contenedor
    cont = _post(f"{user_id}/media", {
        "image_url": image_url, "caption": caption, "access_token": token,
    })
    cid = cont.get("id")
    if not cid:
        raise PublishError(f"No se creo el contenedor: {cont}")

    # 2) esperar a que Instagram baje y valide la imagen (FINISHED)
    for _ in range(25):
        st = _get(cid, {"fields": "status_code", "access_token": token})
        code = st.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise PublishError(f"El contenedor quedo en ERROR: {st}")
        time.sleep(3)
    else:
        raise PublishError("El contenedor nunca llego a FINISHED (timeout).")

    # 3) publicar
    pub = _post(f"{user_id}/media_publish", {
        "creation_id": cid, "access_token": token,
    })
    mid = pub.get("id")
    if not mid:
        raise PublishError(f"No se publico: {pub}")
    return mid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-url", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--caption")
    g.add_argument("--caption-file")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    caption = a.caption
    if a.caption_file:
        with open(a.caption_file, encoding="utf-8") as f:
            caption = f.read()

    mid = publish(a.image_url, caption, dry_run=a.dry_run)
    print("publicado:", mid)


if __name__ == "__main__":
    main()
