"""Diagnostico del acceso a la Graph API de Instagram.

Para que es: cuando el posteo diario falla, decir DONDE se corto sin tener que
adivinar. Consulta, en orden, tres cosas y muestra el resultado crudo de Meta:

  1) debug_token   -> el token sigue vivo? de que app es? cuando vence? que
                      permisos (scopes) tiene?
  2) GET <user_id> -> la cuenta de Instagram responde con un token que solo lee?
  3) POST /media   -> se puede CREAR un contenedor (el paso que hoy falla)? Se
                      crea y NO se publica: queda un borrador que Meta descarta.

Si (1) y (2) andan y (3) no, el problema es de permisos/estado de la app, no del
token. Si falla todo, la app esta bloqueada del lado de Meta.

No imprime el token nunca: solo su largo y los ultimos 4 caracteres.

Uso: IG_USER_ID=... IG_ACCESS_TOKEN=... python ig_diag.py
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

GRAPH = "https://graph.facebook.com/v21.0"

# Imagen publica de este mismo repo: sirve de conejillo de indias para el POST.
SONDA_IMG = "https://raw.githubusercontent.com/nicolaspietkievicz-code/verdikt/main/img/og.png"


def _call(path: str, params: dict, method: str = "GET"):
    """Devuelve (ok, payload). Nunca lanza: el error de Meta ES el dato."""
    if method == "POST":
        req = urllib.request.Request(
            f"{GRAPH}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST"
        )
    else:
        req = urllib.request.Request(f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return True, json.loads(r.read())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode(errors="replace")
        try:
            return False, json.loads(cuerpo)
        except json.JSONDecodeError:
            return False, {"http": e.code, "body": cuerpo}
    except Exception as e:  # red, DNS, timeout
        return False, {"excepcion": repr(e)}


def _mostrar(titulo: str, ok: bool, payload) -> None:
    print(f"\n=== {titulo} ===")
    print("OK" if ok else "FALLO")
    print(json.dumps(payload, indent=2, ensure_ascii=False)[:2000])


def main() -> int:
    user_id = os.environ.get("IG_USER_ID", "")
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    if not user_id or not token:
        print("Faltan IG_USER_ID / IG_ACCESS_TOKEN en el entorno.")
        return 2

    print(f"IG_USER_ID: {len(user_id)} digitos, termina en {user_id[-4:]}")
    print(f"IG_ACCESS_TOKEN: {len(token)} caracteres, termina en {token[-4:]}")

    ok1, p1 = _call("debug_token", {"input_token": token, "access_token": token})
    _mostrar("1) debug_token (estado del token y de la app)", ok1, p1)

    ok2, p2 = _call(user_id, {"fields": "id,username,name", "access_token": token})
    _mostrar("2) GET del usuario de Instagram (lectura)", ok2, p2)

    ok3, p3 = _call(
        f"{user_id}/media",
        {"image_url": SONDA_IMG, "caption": "sonda de diagnostico", "access_token": token},
        method="POST",
    )
    _mostrar("3) POST /media (crear contenedor de FEED, SIN publicar)", ok3, p3)

    # Las historias usan el MISMO endpoint y el MISMO permiso que el feed
    # (instagram_content_publish); lo unico que cambia es media_type=STORIES.
    # Si esto crea contenedor, se pueden publicar historias sin tocar el token.
    ok4, p4 = _call(
        f"{user_id}/media",
        {"media_type": "STORIES", "image_url": SONDA_IMG, "access_token": token},
        method="POST",
    )
    _mostrar("4) POST /media con media_type=STORIES (SIN publicar)", ok4, p4)

    print("\n=== LECTURA ===")
    if ok3:
        print("Se puede publicar en el feed: el bloqueo se levanto.")
    elif ok1 and ok2:
        print("Token vivo y lectura OK, pero no deja crear media:")
        print("permisos o estado de la app del lado de Meta.")
    else:
        print("Ni la lectura basica anda: la app o el token estan bloqueados.")

    if ok4:
        print("HISTORIAS: habilitadas con el token actual, no hace falta permiso nuevo.")
    elif ok3:
        print("HISTORIAS: el feed anda pero STORIES no. Mirar el error de arriba:")
        print("si habla de permisos, hace falta pedir uno nuevo; si habla del")
        print("tipo de cuenta, la cuenta tiene que ser Empresa/Creador.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
