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
from typing import cast

import httpx
from pydantic import BaseModel

from app.config import settings
from app.ki import massenjobs


class BildgenerierungFehler(Exception):
    """Lesbare Fehlermeldung, unabhängig vom Provider dahinter."""


class _BildgenerierungKeinBildFehler(BildgenerierungFehler):
    """Internes Signal fuer den Retry in `_generiere_gemini`: Gemini hat aus
    Modell-Unzuverlaessigkeit kein Bild geliefert (FinishReason NO_IMAGE/
    IMAGE_OTHER laut Google-API-Doku) — ausdruecklich KEIN bewusster
    Inhalts-Block (das waere IMAGE_SAFETY/SAFETY/RECITATION oder ein
    promptFeedback.blockReason, beides nicht retrybar, siehe
    bild_aus_gemini_antwort). Ein erneuter Versuch mit identischem Prompt
    liefert in der Praxis oft doch ein Bild (Mark, 20.11.2026: "Gemini
    liefert kein Bild (Grund: No Image)" beim ERSTEN Versuch mit
    Rassen-Referenzbild, siehe rassen-referenzbilder.md)."""


class BildJobGestartet(BaseModel):
    """Sofortige Antwort beim Start — siehe starte_bild_job."""

    jobId: str


class BildJobStatus(BaseModel):
    """Antwort auf das Fortschritts-Polling. `fertig` erst wahr, wenn das
    Bild fertig generiert ist ODER die Generierung endgueltig fehlgeschlagen
    ist (dann `fehler` gesetzt)."""

    fertig: bool
    bildBase64: str | None = None
    contentType: str | None = None
    referenz: str | None = None
    fehler: str | None = None


async def generiere_bild(
    provider: str,
    prompt: str,
    referenz: tuple[bytes, str] | None = None,
) -> tuple[bytes, str]:
    """Generiert ein Bild aus einem Prompt. Gibt (bytes, content_type) zurück.

    provider: "lokal" (Fooocus) oder "cloud" (Gemini).
    referenz: optionale Vorlage (bytes, mime) — Rassenmerkmale, kein Abbild.
    """
    if provider == "lokal":
        return await _generiere_fooocus(prompt, referenz)
    if provider == "cloud":
        return await _generiere_gemini(prompt, referenz)
    raise BildgenerierungFehler(f"Unbekannter Bild-Provider '{provider}' (erwartet: lokal, cloud)")


async def _generiere_fooocus(prompt: str, referenz: tuple[bytes, str] | None = None) -> tuple[bytes, str]:
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
                    **(
                        {
                            "referenz_b64": base64.b64encode(referenz[0]).decode("ascii"),
                            "referenz_mime": referenz[1],
                        }
                        if referenz
                        else {}
                    ),
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
    if referenz and not resp.json().get("referenz"):
        raise BildgenerierungFehler(
            "Fooocus-Wrapper kennt noch keine Bildreferenz — pnptool_server.py neu starten."
        )

    try:
        with open(pfad, "rb") as f:
            daten = f.read()
    except OSError as e:
        raise BildgenerierungFehler(f"Von Fooocus gemeldete Datei nicht lesbar: {pfad}") from e

    content_type = "image/webp" if pfad.lower().endswith(".webp") else "image/png"
    return daten, content_type


async def _generiere_gemini(prompt: str, referenz: tuple[bytes, str] | None = None) -> tuple[bytes, str]:
    """Google Gemini Bildgenerierung — derselbe REST-Stil wie gemini.py,
    aber mit `responseModalities: ["IMAGE"]` statt JSON-Schema-Output.
    """
    if not settings.gemini_api_key:
        raise BildgenerierungFehler("Kein Gemini-API-Key konfiguriert (backend/.env)")

    from app.rassen.referenz import gemini_parts

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_image_model}:generateContent"
    body = {
        "contents": [{"parts": gemini_parts(prompt, referenz)}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    # NO_IMAGE/IMAGE_OTHER ist Modell-Unzuverlässigkeit, kein bewusster Block
    # (siehe _BildgenerierungKeinBildFehler) — bis zu 2 weitere Versuche mit
    # demselben Prompt, bevor wir das dem Nutzer als Fehler zeigen.
    _MAX_VERSUCHE = 3
    letzter_fehler: _BildgenerierungKeinBildFehler | None = None
    for _ in range(_MAX_VERSUCHE):
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

        try:
            return bild_aus_gemini_antwort(payload)
        except _BildgenerierungKeinBildFehler as e:
            letzter_fehler = e
            continue

    raise BildgenerierungFehler(f"{letzter_fehler} (auch nach {_MAX_VERSUCHE} Versuchen)")


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
        # NO_IMAGE/IMAGE_OTHER (Google-Doku: "model was expected to generate
        # an image, but none was generated" / "miscellaneous issue") sind
        # Modell-Unzuverlässigkeit, kein Inhalts-Entscheid — retrybar. Ein
        # explizites blockReason (promptFeedback) oder ein anderer
        # FinishReason (SAFETY, IMAGE_SAFETY, RECITATION, …) ist ein
        # bewusster Block und bleibt bei Wiederholung derselbe.
        retrybar = not block and grund in {"NO_IMAGE", "IMAGE_OTHER"}
        fehlerklasse = _BildgenerierungKeinBildFehler if retrybar else BildgenerierungFehler
        raise fehlerklasse(f"Gemini lieferte kein Bild (Grund: {grund})")
    raise BildgenerierungFehler("Gemini lieferte eine unerwartete Antwort")


def starte_bild_job(
    campaign_id: str,
    provider: str,
    prompt: str,
    referenz: tuple[bytes, str] | None,
    rassen_name: str,
) -> str:
    """Startet die Bildgenerierung als Hintergrund-Job (siehe massenjobs.py).

    Derselbe Grund wie bei der Massen-KI-Anlage (05.10.2026): ein einzelner,
    lange offener Request stirbt bei einem Netzwerk-Hänger mit "Failed to
    fetch", bevor das — je nach Provider mehrere zig Sekunden dauernde —
    Bild fertig ist (Mark, 20.11.2026). Die Route startet nur noch den Job
    und antwortet sofort mit einer Job-ID; das Frontend pollt den
    Fortschritt über bild_job_status.
    """
    from app.ereignisprotokoll import hooks

    async def _arbeit(job: massenjobs.MassenJob) -> dict:
        inhalt, content_type = await generiere_bild(provider, prompt, referenz)
        job.erstellt = 1
        await hooks.ki(
            campaign_id, anlass="bild-generieren", prompt=prompt,
            antwort_text=f"{provider}: {len(inhalt)} Bytes", uebernommen=False,
        )
        return {"inhalt": inhalt, "contentType": content_type, "referenz": rassen_name or None}

    return massenjobs.starten(1, _arbeit)


def bild_job_status(job_id: str) -> BildJobStatus | None:
    """None = Job unbekannt (schon abgeholt oder Server neugestartet, siehe
    massenjobs.py) — der Aufrufer macht daraus ein HTTP 404."""
    job = massenjobs.status(job_id)
    if job is None:
        return None
    if not job.fertig:
        return BildJobStatus(fertig=False)
    if job.fehler:
        return BildJobStatus(fertig=True, fehler=job.fehler)
    # job.ergebnis ist generisch als `object | None` typisiert (massenjobs.py
    # kennt den Inhalt nicht) — hier wissen wir, dass starte_bild_job() immer
    # dieses dict zurückgibt.
    ergebnis = cast(dict, job.ergebnis or {})
    return BildJobStatus(
        fertig=True,
        bildBase64=base64.b64encode(ergebnis["inhalt"]).decode("ascii"),
        contentType=ergebnis["contentType"],
        referenz=ergebnis.get("referenz"),
    )
