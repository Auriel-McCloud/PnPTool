"""KI-Bildgenerierung: Provider-Abstraktion (lokal Fooocus + Cloud Gemini).

Analog zu `client.py`'s Text-Provider-Wahl, aber als eigenes Modul, weil
Bildgenerierung eine andere Anfrage-Form braucht (Bild-Bytes statt JSON) und
weil der Nutzer den Provider PRO AUFRUF wählt (Commlink-Popup-Dropdown),
nicht global per `.env` wie bei Text (`KI_PROVIDER`).

Zwei Wege:

- **lokal** — spricht gegen `pnptool_server.py` in C:\\DEV\\Fooocus (eigener
  Prozess, eigenes venv, läuft NICHT im PnPTool-Backend). Fooocus 2.5.5 (Gradio
  3.41.2) hat keine eigene REST-API; der Wrapper importiert
  `modules.async_worker` direkt und ahmt `webui.py::generate_clicked` nach
  (siehe Kommentare dort). Muss separat gestartet sein — dieses Modul prüft
  das per Verbindungsfehler und liefert eine klare Fehlermeldung statt eines
  rohen Timeouts.
- **cloud** — Gemini `generateContent` mit `responseModalities: ["IMAGE"]`,
  Modell aus `settings.gemini_image_model` (Default `gemini-3.1-flash-image`,
  Nachfolger von `gemini-2.5-flash-image`). Derselbe REST-Stil wie `gemini.py`
  (kein separates SDK). Bild kommt als Base64 in einem `inlineData`-Part.

Beide liefern am Ende dieselbe Form: rohe Bild-Bytes + Content-Type, die der
Aufrufer (`routes.py`) über den bestehenden Upload-Mechanismus speichert
(gleiche Ordnerstruktur wie `entities/routes.py::_entitaets_bild_hochladen`,
NICHT neu erfunden).
"""

import base64

import httpx

from app.config import settings


class BildgenerierungFehler(Exception):
    """Lesbare Fehlermeldung, unabhängig vom Provider dahinter."""


async def generiere_bild(provider: str, prompt: str) -> tuple[bytes, str]:
    """Generiert ein Bild aus einem Prompt. Gibt (bytes, content_type) zurück.

    provider: "lokal" (Fooocus) oder "cloud" (Gemini).
    """
    if provider == "lokal":
        return await _generiere_fooocus(prompt)
    if provider == "cloud":
        return await _generiere_gemini(prompt)
    raise BildgenerierungFehler(f"Unbekannter Bild-Provider '{provider}' (erwartet: lokal, cloud)")


async def _generiere_fooocus(prompt: str) -> tuple[bytes, str]:
    """Spricht den Fooocus-Wrapper (`pnptool_server.py`) an — muss als eigener
    Prozess laufen (siehe Modul-Docstring). Liefert einen Dateipfad zurück,
    den wir hier einlesen (der Wrapper läuft auf demselben Rechner wie das
    Backend, kein Netzwerktransport nötig).
    """
    url = f"{settings.fooocus_url}/generieren"
    try:
        async with httpx.AsyncClient(timeout=settings.fooocus_timeout_sekunden) as client:
            resp = await client.post(
                url,
                json={
                    "prompt": prompt,
                    "breite": settings.fooocus_breite,
                    "hoehe": settings.fooocus_hoehe,
                    "performance": settings.fooocus_performance,
                },
            )
    except httpx.ConnectError as e:
        raise BildgenerierungFehler(
            "Fooocus ist nicht erreichbar — läuft der lokale Generator "
            f"({url})? Siehe docs/api/ki.md, Abschnitt Bildgenerierung."
        ) from e
    except httpx.TimeoutException as e:
        raise BildgenerierungFehler(
            "Fooocus hat nicht rechtzeitig geantwortet (GTX 1070 kann bei SDXL "
            "mehrere Minuten brauchen) — ggf. Timeout erhöhen oder Auflösung/"
            "Performance-Preset senken."
        ) from e

    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("detail", "")
        except Exception:
            pass
        raise BildgenerierungFehler(f"Fooocus-Aufruf fehlgeschlagen (HTTP {resp.status_code})" + (f": {detail}" if detail else ""))

    pfad = resp.json().get("pfad")
    if not pfad:
        raise BildgenerierungFehler("Fooocus lieferte keinen Bildpfad")

    try:
        with open(pfad, "rb") as f:
            daten = f.read()
    except OSError as e:
        raise BildgenerierungFehler(f"Von Fooocus gemeldete Datei nicht lesbar: {pfad}") from e

    content_type = "image/webp" if pfad.lower().endswith(".webp") else "image/png"
    return daten, content_type


async def _generiere_gemini(prompt: str) -> tuple[bytes, str]:
    """Google Gemini Bildgenerierung — derselbe REST-Stil wie gemini.py,
    aber mit `responseModalities: ["IMAGE"]` statt JSON-Schema-Output.
    """
    if not settings.gemini_api_key:
        raise BildgenerierungFehler("Kein Gemini-API-Key konfiguriert (backend/.env)")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_image_model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, params={"key": settings.gemini_api_key}, json=body)

    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("error", {}).get("message", "")
        except Exception:
            pass
        raise BildgenerierungFehler(f"Gemini-Bildaufruf fehlgeschlagen (HTTP {resp.status_code})" + (f": {detail}" if detail else ""))

    try:
        payload = resp.json()
    except Exception:
        raise BildgenerierungFehler("Gemini lieferte eine unerwartete Antwort")
    return bild_aus_gemini_antwort(payload)


def bild_aus_gemini_antwort(payload: dict) -> tuple[bytes, str]:
    """Zieht Bild-Bytes aus einer Gemini-generateContent-JSON-Antwort.

    Gemini 3.x legt das Bild oft hinter einem Text-/Thought-Part; Safety-Blöcke
    kommen ohne `content.parts`. Beides darf nicht mehr als generisches
    „unerwartete Antwort“ enden.
    """
    if not isinstance(payload, dict):
        raise BildgenerierungFehler("Gemini lieferte eine unerwartete Antwort")

    candidates = payload.get("candidates") or []
    block = (payload.get("promptFeedback") or {}).get("blockReason")
    finish_reasons: list[str] = []
    texte: list[str] = []

    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        reason = cand.get("finishReason") or cand.get("finish_reason")
        if reason:
            finish_reasons.append(str(reason))
        content = cand.get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            if not isinstance(part, dict):
                continue
            text = (part.get("text") or "").strip()
            if text:
                texte.append(text)
            inline = part.get("inlineData") or part.get("inline_data") or {}
            if inline.get("data"):
                mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
                return base64.b64decode(inline["data"]), mime

    if texte:
        raise BildgenerierungFehler(" ".join(texte))

    grund = block or (finish_reasons[0] if finish_reasons else "")
    if grund:
        raise BildgenerierungFehler(f"Gemini lieferte kein Bild (Grund: {grund})")
    raise BildgenerierungFehler("Gemini lieferte eine unerwartete Antwort")
