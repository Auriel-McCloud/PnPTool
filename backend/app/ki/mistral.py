"""Mistral-AI-Client ("La Plateforme", api.mistral.ai).

Alternative zu Gemini — z.B. wenn das Gemini-Kontingent aufgebraucht ist.
Mistral ist OpenAI-kompatibel (`/v1/chat/completions`), deshalb ein eigener,
kleiner Client statt den Gemini-Client zu verbiegen.

Gleiche Signatur wie `gemini.generiere_json`, damit `routes.py` den Anbieter
austauschen kann, ohne die Aufrufstellen zu ändern (siehe `ki_client.py`).
"""

import json
import re

import httpx

from app.config import settings

_API_URL = "https://api.mistral.ai/v1/chat/completions"


class MistralFehler(Exception):
    """Lesbare Fehlermeldung für die Mistral-Anbindung."""


async def generiere_json(
    prompt: str,
    system: str = "",
    schema: dict | None = None,
) -> dict:
    """Ruft Mistral auf und erwartet eine JSON-Antwort, die als Dict zurückkommt.

    `schema` ist ein JSON-Schema (dasselbe Format wie bei Gemini) und wird als
    `response_format: json_schema` mitgeschickt — zwingt das Modell zu einer
    festen Form.
    """
    if not settings.mistral_api_key:
        raise MistralFehler("Kein Mistral-API-Key konfiguriert (backend/.env)")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body: dict = {
        "model": settings.mistral_model,
        "messages": messages,
    }
    if schema is not None:
        # Mistral verlangt "additionalProperties": false und ein "name" fürs Schema.
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "antwort",
                "schema": _ohne_gemini_typnamen(schema),
                "strict": True,
            },
        }
    else:
        body["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            _API_URL,
            headers={"Authorization": f"Bearer {settings.mistral_api_key}"},
            json=body,
        )

    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("message", "") or resp.json().get("error", {}).get("message", "")
        except Exception:
            pass
        raise MistralFehler(f"Mistral-Aufruf fehlgeschlagen (HTTP {resp.status_code})" + (f": {detail}" if detail else ""))

    try:
        text = resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise MistralFehler("Mistral lieferte eine unerwartete Antwort")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise MistralFehler("Mistral lieferte kein gültiges JSON")


def _ohne_gemini_typnamen(schema: dict) -> dict:
    """Wandelt Gemini-Schema-Typnamen (GROSS) in Standard-JSON-Schema (klein) um.

    Unsere Schemata in routes.py sind im Gemini-Stil geschrieben
    ("OBJECT", "STRING", "ARRAY", "INTEGER"). Mistral erwartet Standard-
    JSON-Schema ("object", "string", "array", "integer"). Rekursiv, weil
    Schemata verschachtelte "items"/"properties" enthalten.
    """
    if isinstance(schema, dict):
        neu = {}
        for k, v in schema.items():
            if k == "type" and isinstance(v, str):
                neu[k] = v.lower()
            else:
                neu[k] = _ohne_gemini_typnamen(v)
        # Mistrals strict mode verlangt additionalProperties: false auf jedem Objekt.
        if neu.get("type") == "object" and "additionalProperties" not in neu:
            neu["additionalProperties"] = False
        return neu
    if isinstance(schema, list):
        return [_ohne_gemini_typnamen(v) for v in schema]
    return schema
