"""Verkleinerte Vorschaubilder für Übersichten (Mark, 11.11.2026).

Seit fast alles ein Bild hat, lud jede Kachel-Übersicht die Originale (oft
mehrere MB, insgesamt >500 MB) — die Seite brauchte beim Öffnen ewig. Die
Übersichten holen jetzt `/uploads/_vorschau/<breite>/<kampagne>/<datei>`;
Detailansicht, Großbild und Bild-Pushs an die Spieler bleiben beim Original.

Die Vorschau entsteht beim ersten Abruf und liegt danach als WebP unter
`uploads/_vorschau/` — kein Upload-Pfad muss etwas davon wissen, und alle
bestehenden Bilder bekommen ihre Vorschau ohne Migration. Wird ein Original
irgendwann neuer als seine Vorschau, wird sie neu gebaut.

Upload-Dateinamen sind durchweg UUIDs und werden nie überschrieben, deshalb
dürfen Browser Original und Vorschau ein Jahr lang ohne Rückfrage cachen —
beim erneuten Öffnen der Seite fällt so nicht einmal ein 304 pro Bild an.
"""

import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps

UPLOAD_DIR = Path("uploads")
VORSCHAU_ORDNER = "_vorschau"

# Feste Stufen statt freier Breite: sonst könnte jeder beliebig viele
# Varianten erzeugen lassen und die Platte füllen. Die Zahl ist die
# KÜRZERE Bildseite — Kacheln schneiden per object-fit: cover auf ein
# Quadrat zu, ein Querformat bräuchte bei reiner Breitenvorgabe sonst zu
# wenig Höhe und würde unscharf.
ERLAUBTE_BREITEN = {128, 480}

CACHE_KOPF = {"Cache-Control": "public, max-age=31536000, immutable"}

# Nur einfache Dateinamen — nichts, was aus dem Upload-Ordner ausbrechen kann.
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

router = APIRouter()


class CachendeUploads(StaticFiles):
    """StaticFiles mit Langzeit-Cache (Dateinamen sind unveränderliche UUIDs)."""

    def file_response(self, *args, **kwargs):
        antwort = super().file_response(*args, **kwargs)
        if antwort.status_code in (200, 304):
            antwort.headers.update(CACHE_KOPF)
        return antwort


def erzeuge_vorschau(original: Path, ziel: Path, kurze_seite: int) -> bool:
    """Schreibt die Vorschau als WebP. False = Original direkt ausliefern
    (schon klein genug, animiertes GIF, oder kein lesbares Bild)."""
    try:
        with Image.open(original) as bild:
            if getattr(bild, "is_animated", False):
                return False
            breite, hoehe = bild.size
            faktor = kurze_seite / min(breite, hoehe)
            if faktor >= 1:
                return False
            # JPEG gleich beim Dekodieren verkleinern — spart bei großen
            # Fotos den Großteil der Rechenzeit (bleibt immer >= Zielgröße).
            bild.draft("RGB", (round(breite * faktor), round(hoehe * faktor)))
            # Erst drehen, dann die Zielgröße bestimmen — EXIF-Hochformat
            # tauscht Breite und Höhe.
            bild = ImageOps.exif_transpose(bild)
            breite, hoehe = bild.size
            faktor = kurze_seite / min(breite, hoehe)
            ziel_groesse = (max(1, round(breite * faktor)), max(1, round(hoehe * faktor)))
            if bild.mode not in ("RGB", "RGBA"):
                bild = bild.convert("RGBA" if "A" in bild.getbands() or "transparency" in bild.info else "RGB")
            klein = bild.resize(ziel_groesse, Image.Resampling.LANCZOS)
            ziel.parent.mkdir(parents=True, exist_ok=True)
            # Erst in eine Nebendatei, dann umbenennen: zwei gleichzeitige
            # Abrufe dürfen sich keine halb geschriebene Datei ausliefern.
            zwischen = ziel.with_name(f".{uuid.uuid4().hex}.tmp")
            klein.save(zwischen, "WEBP", quality=82, method=4)
            os.replace(zwischen, ziel)
            return True
    except Exception:
        return False


@router.get("/uploads/_vorschau/{breite}/{campaign_id}/{datei}")
def vorschau(breite: int, campaign_id: str, datei: str):
    # Bewusst ohne Login, wie das Original unter /uploads auch.
    if breite not in ERLAUBTE_BREITEN or not _NAME.match(campaign_id) or not _NAME.match(datei):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")
    original = UPLOAD_DIR / campaign_id / datei
    if not original.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden")

    ziel = UPLOAD_DIR / VORSCHAU_ORDNER / str(breite) / campaign_id / f"{datei}.webp"
    aktuell = ziel.is_file() and ziel.stat().st_mtime >= original.stat().st_mtime
    if aktuell or erzeuge_vorschau(original, ziel, breite):
        return FileResponse(ziel, media_type="image/webp", headers=CACHE_KOPF)
    return FileResponse(original, headers=CACHE_KOPF)
