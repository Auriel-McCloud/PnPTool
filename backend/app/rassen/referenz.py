"""Rassen-Referenzpool für die Bildgenerierung.

Der Schalter und die Bildliste liegen an der Rasse, nicht am Namen im Code.
Eine Generierung zieht zufällig eine vorhandene Datei als Vorlage. In den
Pool kommt nur, was die SL selbst hochlädt, oder ein KI-Portrait, das
übernommen wurde — verworfene Vorschauen nicht.
"""

import mimetypes
import random
import uuid
from pathlib import Path

UPLOAD_DIR = Path("uploads")

# Einmaliger Startwert, nur solange das Feld noch fehlt. Apostroph-Varianten,
# weil der Live-Name nicht im Code steht und ein falsches Zeichen den Schalter
# sonst nie setzt. Danach entscheidet nur noch `referenzAktiv`.
START_NAMEN = frozenset({"dug'rah", "dug’rah", "dug`rah", "sephari", "quill"})

REFERENZ_HINWEIS = (
    " Use the reference image only for species anatomy and distinctive racial"
    " features. This is a different individual — vary face, pose, clothing,"
    " expression and framing. Do not copy the reference person."
)


def name_startet_mit_referenz(name: str) -> bool:
    return (name or "").strip().casefold() in START_NAMEN


def prompt_mit_referenz(prompt: str) -> str:
    return prompt.rstrip() + REFERENZ_HINWEIS


def gemini_parts(prompt: str, referenz: tuple[bytes, str] | None) -> list[dict]:
    """Text, und bei einer Vorlage zusätzlich das Bild als inlineData."""
    text = prompt_mit_referenz(prompt) if referenz else prompt
    parts: list[dict] = [{"text": text}]
    if referenz:
        daten, mime = referenz
        import base64

        parts.append({"inlineData": {"mimeType": mime, "data": base64.b64encode(daten).decode("ascii")}})
    return parts


def waehle_url(urls: list[str]) -> str | None:
    kandidaten = [u for u in urls if u]
    if not kandidaten:
        return None
    return random.choice(kandidaten)


def ist_eigene_url(rasse_id: str, url: str) -> bool:
    prefix = f"/uploads/rassen/{rasse_id}/"
    if not url.startswith(prefix):
        return False
    name = url[len(prefix):]
    return bool(name) and "/" not in name and "\\" not in name and ".." not in name


def datei_zu_pfad(rasse_id: str, url: str) -> Path | None:
    if not ist_eigene_url(rasse_id, url):
        return None
    return UPLOAD_DIR / "rassen" / rasse_id / url.rsplit("/", 1)[-1]


def speichere_kopie(rasse_id: str, inhalt: bytes, mime: str) -> str:
    ordner = UPLOAD_DIR / "rassen" / rasse_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(mime or "") or ".png"
    if endung == ".jpe":
        endung = ".jpg"
    name = f"{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)
    return f"/uploads/rassen/{rasse_id}/{name}"


def loesche_datei(rasse_id: str, url: str) -> None:
    pfad = datei_zu_pfad(rasse_id, url)
    if pfad is not None and pfad.is_file():
        pfad.unlink()


def lies_datei(rasse_id: str, url: str) -> tuple[bytes, str] | None:
    pfad = datei_zu_pfad(rasse_id, url)
    if pfad is None or not pfad.is_file():
        return None
    mime = mimetypes.guess_type(pfad.name)[0] or "image/png"
    return pfad.read_bytes(), mime


async def ziehe_fuer_person(campaign_id: str, person_id: str) -> tuple[bytes, str, str] | None:
    """Zufällige vorhandene Vorlage, oder None wenn der Schalter aus ist."""
    from app.entities.repository import PERSON_FIELDS, get_node
    from app.rassen import repository

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        return None
    rasse = await repository.hole_nach_name(person.get("rasse") or "")
    if rasse is None or not rasse.get("referenzAktiv"):
        return None
    vorhanden = []
    for url in rasse.get("referenzbilder") or []:
        pfad = datei_zu_pfad(rasse["id"], url)
        if pfad is not None and pfad.is_file():
            vorhanden.append(url)
    url = waehle_url(vorhanden)
    if not url:
        return None
    gelesen = lies_datei(rasse["id"], url)
    if gelesen is None:
        return None
    daten, mime = gelesen
    return daten, mime, rasse.get("name") or ""


async def lege_uebernommenes_ab(campaign_id: str, person_id: str, inhalt: bytes, mime: str) -> bool:
    """Kopiert ein übernommenes KI-Portrait in den Pool, wenn der Schalter an ist."""
    from app.entities.repository import PERSON_FIELDS, get_node
    from app.rassen import repository

    person = await get_node("Person", PERSON_FIELDS, campaign_id, person_id)
    if person is None:
        return False
    rasse = await repository.hole_nach_name(person.get("rasse") or "")
    if rasse is None or not rasse.get("referenzAktiv"):
        return False
    url = speichere_kopie(rasse["id"], inhalt, mime)
    await repository.referenz_anhaengen(rasse["id"], url)
    return True
