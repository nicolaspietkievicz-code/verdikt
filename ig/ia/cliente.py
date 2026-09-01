"""Cliente minimo de la API de OpenAI: texto (chat) e imagen (gpt-image-1).

Sin SDK, solo urllib, igual que el resto del repo (ig_publish.py, build_data.py).
Se usa para el copy y las caratulas del reel diario (ver ig_pendiente.py).

Entorno:
  OPENAI_API_KEY      obligatorio para que haga algo
  OPENAI_TEXT_MODEL   opcional, por defecto gpt-4.1-mini
  OPENAI_IMAGE_MODEL  opcional, por defecto gpt-image-1

Si falta la key, cualquier llamada tira IAError; los llamadores lo toleran y
caen a plantilla (misma logica que cuando faltan los secrets de Instagram)."""
import base64
import json
import os
import urllib.error
import urllib.request

BASE = "https://api.openai.com/v1"
# `or` y no default de get(): el workflow puede exportar la var vacia.
TEXT_MODEL = os.environ.get("OPENAI_TEXT_MODEL") or "gpt-4.1-mini"
IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL") or "gpt-image-1"


class IAError(Exception):
    pass


def _key() -> str:
    k = os.environ.get("OPENAI_API_KEY", "").strip()
    if not k:
        raise IAError("Falta OPENAI_API_KEY en el entorno.")
    return k


def _post(path: str, payload: dict, *, timeout: int) -> dict:
    req = urllib.request.Request(
        f"{BASE}/{path}",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {_key()}",
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:800]
        raise IAError(f"HTTP {e.code} en {path}: {body}")
    except Exception as e:
        raise IAError(f"{type(e).__name__} en {path}: {e}")


def chat(system: str, user: str, *, json_out: bool = True, timeout: int = 60) -> str:
    """Una vuelta de chat. Devuelve el texto crudo de la respuesta (si
    json_out, el modelo entrega un objeto JSON como string)."""
    payload = {
        "model": TEXT_MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.7,
    }
    if json_out:
        payload["response_format"] = {"type": "json_object"}
    data = _post("chat/completions", payload, timeout=timeout)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise IAError(f"Respuesta de chat sin contenido: {str(data)[:400]}")


def imagenes(prompt: str, *, n: int = 3, size: str = "1024x1536",
             quality: str = "medium", timeout: int = 240) -> list:
    """Genera n imagenes. gpt-image-1 siempre devuelve base64 (no URL).
    Devuelve una lista de bytes PNG."""
    data = _post("images/generations", {
        "model": IMAGE_MODEL, "prompt": prompt, "n": n,
        "size": size, "quality": quality,
    }, timeout=timeout)
    out = []
    for item in data.get("data", []):
        b64 = item.get("b64_json")
        if b64:
            out.append(base64.b64decode(b64))
    if not out:
        raise IAError(f"Sin imagenes en la respuesta: {str(data)[:400]}")
    return out
