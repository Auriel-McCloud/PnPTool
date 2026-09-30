"""Google-Gemini-Client.

Nur der Transport: Prompt + optionaler Systemtext rein, strukturiertes JSON
raus. Die Prompts und ihre Bedeutung liegen in `routes.py`.

Absichtlich ein eigener, kleiner Fehlertyp: das Frontend soll eine verständ-
liche Meldung zeigen („Kein Key konfiguriert", „Gemini antwortete mit Quatsch"),
keine rohe HTTP-Exception.
"""

import json
import re

import httpx

from app.config import settings

_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiFehler(Exception):
    """Lesbare Fehlermeldung für die KI-Anbindung."""


def _url() -> str:
    return f"{_API_BASE}/{settings.gemini_model}:generateContent"


async def generiere_json(
    prompt: str,
    system: str = "",
    schema: dict | None = None,
) -> dict:
    """Ruft Gemini auf und erwartet eine JSON-Antwort, die als Dict zurückkommt.

    `schema` ist ein Gemini-responseSchema (JSON-Schema) und zwingt das Modell
    zu einer festen Form — für Charaktere und Story-Parts die sauberste Art,
    kein freies Raten über die Ausgabe zu brauchen.
    """
    if not settings.gemini_api_key:
        raise GeminiFehler("Kein Gemini-API-Key konfiguriert (backend/.env)")

    body: dict = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    if schema is not None:
        body["generationConfig"]["responseSchema"] = schema

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            _url(),
            params={"key": settings.gemini_api_key},
            json=body,
        )

    if resp.status_code != 200:
        # Gemini liefert Fehler als JSON mit .error.message — die mitgeben,
        # sonst steht im Frontend nur „HTTP 400" ohne Grund.
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            pass
        raise GeminiFehler(f"Gemini-Aufruf fehlgeschlagen (HTTP {resp.status_code})" + (f": {detail}" if detail else ""))

    try:
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        raise GeminiFehler("Gemini lieferte eine unerwartete Antwort")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Manche Modelle liefern trotz JSON-MimeType Markdown-Fences um das
        # JSON herum — dann das erste {...} herausziehen.
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise GeminiFehler("Gemini lieferte kein gültiges JSON")


async def generiere_text(nachrichten: list[dict], system: str = "") -> str:
    """Freier Fließtext über mehrere Turns — kein JSON-Schema.

    `nachrichten` sind Dicts mit `rolle` (user/assistant) und `text`.
    Gemini heißt die Modell-Seite ``model``, nicht assistant.
    """
    if not settings.gemini_api_key:
        raise GeminiFehler("Kein Gemini-API-Key konfiguriert (backend/.env)")
    if not nachrichten:
        raise GeminiFehler("Keine Nachricht an Gemini")

    contents = []
    for eintrag in nachrichten:
        rolle = "user" if eintrag.get("rolle") == "user" else "model"
        contents.append({"role": rolle, "parts": [{"text": eintrag["text"]}]})

    body: dict = {
        "contents": contents,
        "generationConfig": {"temperature": 0.8},
    }
    if system:
        body["systemInstruction"] = {"parts": [{"text": system}]}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            _url(),
            params={"key": settings.gemini_api_key},
            json=body,
        )

    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            pass
        raise GeminiFehler(
            f"Gemini-Aufruf fehlgeschlagen (HTTP {resp.status_code})"
            + (f": {detail}" if detail else "")
        )

    try:
        teile = resp.json()["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in teile).strip()
    except (KeyError, IndexError, TypeError):
        raise GeminiFehler("Gemini lieferte eine unerwartete Antwort")
    if not text:
        raise GeminiFehler("Gemini lieferte keinen Text")
    return text
