"""Cliente minimo de IA para el copy y las caratulas del reel: Gemini u OpenAI.

Sin SDK, solo urllib, igual que el resto del repo (ig_publish.py, build_data.py).

Elige proveedor por la key que este seteada en el entorno:
  GEMINI_API_KEY   -> Google Gemini (preferido; free tier, sin tarjeta)
  OPENAI_API_KEY   -> OpenAI (fallback si no hay Gemini)
Ninguna -> IAError, y el llamador cae a plantilla (misma logica que los
secrets de Instagram).

Variables opcionales de modelo:
  GEMINI_TEXT_MODEL   (def. gemini-2.5-flash)
  GEMINI_IMAGE_MODEL  (def. gemini-2.5-flash-image)
  OPENAI_TEXT_MODEL   (def. gpt-4.1-mini)
  OPENAI_IMAGE_MODEL  (def. gpt-image-1)"""
import base64
import json
import os
import urllib.error
import urllib.request

_OPENAI = "https://api.openai.com/v1"
_GEMINI = "https://generativelanguage.googleapis.com/v1beta"


class IAError(Exception):
    pass


def _env(nombre):
    return (os.environ.get(nombre) or "").strip()


def _provider():
    if _env("GEMINI_API_KEY"):
        return "gemini"
    if _env("OPENAI_API_KEY"):
        return "openai"
    raise IAError("Falta GEMINI_API_KEY u OPENAI_API_KEY en el entorno.")


def _req(url, payload, headers, timeout):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={**headers, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise IAError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:800]}")
    except Exception as e:
        raise IAError(f"{type(e).__name__}: {e}")


# ------------------------------------------------------------------ texto ------
def chat(system: str, user: str, *, json_out: bool = True, timeout: int = 60) -> str:
    """Una vuelta de chat. Devuelve el texto crudo (si json_out, un objeto JSON
    como string)."""
    if _provider() == "gemini":
        model = _env("GEMINI_TEXT_MODEL") or "gemini-2.5-flash"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.7},
        }
        if json_out:
            body["generationConfig"]["responseMimeType"] = "application/json"
        data = _req(f"{_GEMINI}/models/{model}:generateContent", body,
                    {"x-goog-api-key": _env("GEMINI_API_KEY")}, timeout)
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError):
            raise IAError(f"Gemini sin texto: {str(data)[:400]}")

    model = _env("OPENAI_TEXT_MODEL") or "gpt-4.1-mini"
    body = {"model": model, "temperature": 0.7,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}]}
    if json_out:
        body["response_format"] = {"type": "json_object"}
    data = _req(f"{_OPENAI}/chat/completions", body,
                {"Authorization": f"Bearer {_env('OPENAI_API_KEY')}"}, timeout)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise IAError(f"OpenAI sin texto: {str(data)[:400]}")


# --------------------------------------------------------------- imagenes ------
def imagenes(prompt: str, *, n: int = 3, size: str = "1024x1536",
             timeout: int = 240) -> list:
    """Genera n imagenes. Devuelve una lista de bytes PNG.

    Gemini genera de a una, asi que se llama n veces; OpenAI las pide en una
    sola. El encuadre final (1080x1920) lo hace caratula.py, asi que el aspect
    ratio exacto de la fuente no importa demasiado."""
    if _provider() == "gemini":
        model = _env("GEMINI_IMAGE_MODEL") or "gemini-2.5-flash-image"
        out = []
        for _ in range(n):
            data = _req(
                f"{_GEMINI}/models/{model}:generateContent",
                {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                 "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}},
                {"x-goog-api-key": _env("GEMINI_API_KEY")}, timeout)
            try:
                parts = data["candidates"][0]["content"]["parts"]
            except (KeyError, IndexError):
                continue
            for p in parts:
                inline = p.get("inlineData") or p.get("inline_data")
                if inline and inline.get("data"):
                    out.append(base64.b64decode(inline["data"]))
                    break
        if not out:
            raise IAError(f"Gemini no devolvio imagenes: {str(data)[:400]}")
        return out

    model = _env("OPENAI_IMAGE_MODEL") or "gpt-image-1"
    data = _req(f"{_OPENAI}/images/generations",
                {"model": model, "prompt": prompt, "n": n, "size": size,
                 "quality": "medium"},
                {"Authorization": f"Bearer {_env('OPENAI_API_KEY')}"}, timeout)
    out = [base64.b64decode(i["b64_json"]) for i in data.get("data", [])
           if i.get("b64_json")]
    if not out:
        raise IAError(f"OpenAI sin imagenes: {str(data)[:400]}")
    return out
