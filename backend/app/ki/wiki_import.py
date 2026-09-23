"""Wiki-Import: SL lädt ein Word/PDF-Dokument hoch, die KI teilt es anhand
seiner Struktur in eine oder mehrere Wiki-Seiten-Entwürfe auf.

Ablauf (Marks Entscheidung, 22.09.2026 — siehe CLAUDE.md "Zuletzt gebaut"):

1. ``dokument_zu_text()`` liest die hochgeladene Datei (.docx via
   python-docx, .pdf via pypdf) und liefert reinen Text — bei .docx bleiben
   erkannte Überschriften-Formatvorlagen (Heading 1/2/3) als Markdown-artige
   ``#``/``##``-Präfixe erhalten, damit die KI die Gliederung sieht, ohne
   selbst raten zu müssen; .pdf liefert nur Fließtext (pypdf kennt keine
   Formatvorlagen), die KI muss die Kapitelstruktur dort rein aus dem
   Textmuster erkennen.
2. ``gliedere_dokument()`` schickt den Text an die Text-KI
   (``app/ki/client.py``, wie der Ideenschmiede-„✨ KI"-Knopf) mit dem
   Kampagnenkontext (``sammle_kontext()``) und lässt sie eine Liste von
   Seiten-Vorschlägen (Titel + Inhalt + optionaler Eltern-Index für
   Unterseiten) liefern.
3. ``importiere()`` legt daraus echte ``istEntwurf=true``-Wiki-Seiten an
   (``wiki/repository.create_seite``, GENAU der Weg, den auch der
   Ideenschmiede-Story-Typ nutzt) — Unterseiten zuerst mit vorläufigem
   ``parent_id=None`` angelegt und danach in einem zweiten Durchlauf per
   ``update_seite`` verknüpft (die IDs der Elternseiten sind erst nach dem
   Anlegen bekannt). Pro neu angelegter Seite läuft anschliessend die
   bestehende Auto-Verknüpfung (``auto_verknuepfung.py``) — dieselbe Logik
   wie der „⧉✨ Auto-Verknüpfung"-Knopf im Wiki-Editor, hier nur automatisch
   für JEDEN gefundenen Vorschlag angewandt statt einzeln vom SL bestätigt
   (Mark: „nach dem Erzeugen der Entwurfs-Seiten soll pro Seite automatisch
   die bestehende Auto-Verknüpfungs-Logik laufen").
"""

import io

from pydantic import BaseModel

from app.ki.auto_verknuepfung import anwenden as verknuepfung_anwenden
from app.ki.auto_verknuepfung import beziehung_anwenden as verknuepfung_beziehung_anwenden
from app.ki.auto_verknuepfung import vorschlaege as verknuepfung_vorschlaege
from app.ki.client import KiFehler, generiere_json
from app.ki.kontext import sammle_kontext
from app.wiki import repository

# Ein Dokument, das die KI nicht mehr sinnvoll auf einen Blick gliedern
# kann (Kontextfenster, Prompt-Kosten) — grosszügig genug für eine lange
# Session-Zusammenfassung, aber keine Buch-Länge. Mark wollte laut Aufgabe
# eine sinnvolle Grenze statt eines stundenlangen Kampfs mit riesigen
# Dokumenten (siehe Blocker-Hinweis in der Aufgabenbeschreibung).
MAX_ZEICHEN = 60_000

ERLAUBTE_ENDUNGEN = {".docx", ".pdf"}


class DokumentZuGrossFehler(Exception):
    """Das Dokument überschreitet MAX_ZEICHEN — der Import lehnt bewusst ab,
    statt einen abgeschnittenen/unvollständigen Import zu riskieren."""


class DokumentFormatFehler(Exception):
    """Weder .docx noch .pdf, oder die Datei liess sich nicht lesen."""


def _docx_zu_text(inhalt: bytes) -> str:
    """Liest ein .docx, hängt erkannte Überschriften als #-Präfix an.

    python-docx benennt Überschriften-Formatvorlagen "Heading 1".."Heading 9"
    (auch bei einer deutschen Word-Oberfläche bleibt der interne Style-Name
    englisch) — die Ziffer wird direkt als Gliederungstiefe übernommen.
    """
    import docx  # lazy: teuer beim Modulimport, nur hier gebraucht

    dokument = docx.Document(io.BytesIO(inhalt))
    zeilen: list[str] = []
    for absatz in dokument.paragraphs:
        text = absatz.text.strip()
        if not text:
            continue
        stil = (absatz.style.name or "") if absatz.style else ""
        if stil.startswith("Heading "):
            try:
                stufe = int(stil.removeprefix("Heading "))
            except ValueError:
                stufe = 1
            zeilen.append(f"{'#' * max(1, min(stufe, 6))} {text}")
        elif stil == "Title":
            zeilen.append(f"# {text}")
        else:
            zeilen.append(text)
    return "\n\n".join(zeilen)


def _pdf_zu_text(inhalt: bytes) -> str:
    """Liest ein .pdf als reinen Fließtext (keine Formatvorlagen bekannt)."""
    import pypdf  # lazy: teuer beim Modulimport, nur hier gebraucht

    reader = pypdf.PdfReader(io.BytesIO(inhalt))
    seiten = [seite.extract_text() or "" for seite in reader.pages]
    return "\n\n".join(s.strip() for s in seiten if s.strip())


def dokument_zu_text(dateiname: str, inhalt: bytes) -> str:
    """Extrahiert reinen Text aus einer hochgeladenen .docx/.pdf-Datei."""
    name = dateiname.lower()
    try:
        if name.endswith(".docx"):
            text = _docx_zu_text(inhalt)
        elif name.endswith(".pdf"):
            text = _pdf_zu_text(inhalt)
        else:
            raise DokumentFormatFehler(
                "Nur .docx- oder .pdf-Dateien werden unterstützt."
            )
    except DokumentFormatFehler:
        raise
    except Exception as e:  # pragma: no cover - defensiv, Bibliotheksfehler variieren
        raise DokumentFormatFehler(f"Dokument konnte nicht gelesen werden: {e}") from e

    if len(text) > MAX_ZEICHEN:
        raise DokumentZuGrossFehler(
            f"Das Dokument ist mit {len(text)} Zeichen zu groß für einen KI-Import "
            f"(Grenze: {MAX_ZEICHEN}). Bitte in kleinere Abschnitte aufteilen."
        )
    return text


_SYSTEM = (
    "Du bist ein Spielleiter-Assistent für das Cyberpunk-Pen-and-Paper-Rollenspiel "
    "NeotopiA. Ein Dokument (Session-Vorbereitung, Hintergrundtext, Kapitel-"
    "Sammlung) soll ins Kampagnen-Wiki importiert werden. Erkenne die Struktur "
    "des Textes (Überschriften, Kapitel, thematische Abschnitte) und teile ihn "
    "in sinnvolle Wiki-Seiten auf — bei einem kurzen, unstrukturierten Text kann "
    "das auch NUR EINE Seite sein. Erkennst du eine Hierarchie (ein Kapitel mit "
    "mehreren Unterabschnitten), gib den Unterseiten einen 'elternIndex' auf den "
    "Index der übergeordneten Seite in deiner eigenen Liste (0-basiert) — bei "
    "keinem erkennbaren Elternteil lass 'elternIndex' weg. Schreibe den Inhalt "
    "jeder Seite als sauberen Fließtext in Absätzen (leere Zeile = neuer Absatz), "
    "übernimm dabei den Sinn des Originaltextes, ändere ihn nicht künstlich um. "
    "Auf Deutsch."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "seiten": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "titel": {"type": "STRING"},
                    "inhalt": {"type": "STRING"},
                    "elternIndex": {"type": "INTEGER"},
                },
                "required": ["titel", "inhalt"],
            },
        },
    },
    "required": ["seiten"],
}


class SeitenVorschlag(BaseModel):
    titel: str
    inhalt: str
    elternIndex: int | None = None


async def gliedere_dokument(campaign_id: str, text: str) -> list[SeitenVorschlag]:
    """Lässt die KI den Dokumenttext in Seiten-Vorschläge aufteilen.

    Hängt denselben Kampagnenkontext an wie jede andere KI-Generierung
    (``sammle_kontext``) — nicht damit die KI Namen erfindet, sondern damit
    Anschluss-Formulierungen ("wie bereits bekannt...") stimmig bleiben.
    """
    kontext = await sammle_kontext(campaign_id)
    prompt = f"Zu importierendes Dokument:\n\n{text}"
    if kontext:
        prompt += (
            f"\n\nFreigegebene Welt der Kampagne (nur zur Einordnung, nicht Teil "
            f"des zu importierenden Textes):\n{kontext}"
        )
    ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA)

    vorschlaege: list[SeitenVorschlag] = []
    for eintrag in ergebnis.get("seiten") or []:
        titel = (eintrag.get("titel") or "").strip()
        inhalt = (eintrag.get("inhalt") or "").strip()
        if not titel or not inhalt:
            continue
        eltern_index = eintrag.get("elternIndex")
        vorschlaege.append(
            SeitenVorschlag(
                titel=titel,
                inhalt=inhalt,
                elternIndex=eltern_index if isinstance(eltern_index, int) else None,
            )
        )
    return vorschlaege


def _text_zu_dokument(text: str) -> str:
    """Fließtext in ein TipTap-Dokument umwandeln (Absätze = Paragraph-Nodes).

    Dieselbe kleine Konvertierung wie ``ki/routes.py::_text_zu_dokument`` für
    den Story-Typ — hier nicht importiert, um keine private Funktion aus
    einem anderen Modul zu ziehen (beide sind bewusst 5 Zeilen kurz, kein
    Grund für eine geteilte dritte Datei).
    """
    import json

    absaetze = [a.strip() for a in text.split("\n\n") if a.strip()]
    if not absaetze and text.strip():
        absaetze = [text.strip()]
    content = [
        {"type": "paragraph", "content": [{"type": "text", "text": a}]}
        for a in absaetze
    ]
    return json.dumps({"type": "doc", "content": content}, ensure_ascii=False)


class ImportierteSeite(BaseModel):
    id: str
    titel: str
    parentId: str | None = None
    # Wie viele Auto-Verknüpfungs-Vorschläge (Verweise + Beziehungen) für
    # diese Seite gefunden UND automatisch angewandt wurden — SL sieht so
    # direkt im Ergebnis, ob sich ein Blick in den Entwurf lohnt.
    verknuepfungen: int = 0


class ImportAntwort(BaseModel):
    seiten: list[ImportierteSeite] = []


async def _auto_verknuepfen(campaign_id: str, seiten_id: str) -> int:
    """Wendet ALLE erkannten Auto-Verknüpfungs-Vorschläge einer Seite direkt an.

    Anders als der manuelle „⧉✨ Auto-Verknüpfung"-Knopf (der jeden Vorschlag
    einzeln zur Bestätigung zeigt) läuft das hier automatisch pro importierter
    Seite — Marks ausdrückliche Vorgabe für den Wiki-Import. Neue Entitäten
    landen trotzdem nur als Entwurf (kein Autocommit in die Kampagne selbst,
    das übernimmt ``anwenden()``/``beziehung_anwenden()`` unverändert aus der
    bestehenden Logik).
    """
    try:
        vorschlaege = await verknuepfung_vorschlaege(campaign_id, seiten_id)
    except KiFehler:
        # Eine fehlschlagende Verknüpfung darf den Import selbst nicht
        # kippen — die Seite steht trotzdem als Entwurf bereit.
        return 0

    anzahl = 0
    for verweis in vorschlaege.verweise:
        ergebnis = await verknuepfung_anwenden(
            campaign_id, seiten_id, verweis.zitat, verweis.typ, verweis.name, verweis.zielId
        )
        if ergebnis is not None and ergebnis.ersetzt:
            anzahl += 1

    for beziehung in vorschlaege.beziehungen:
        from app.ki.auto_verknuepfung import BeziehungAnwendenInput

        await verknuepfung_beziehung_anwenden(
            campaign_id,
            BeziehungAnwendenInput(
                typ1=beziehung.typ1,
                name1=beziehung.name1,
                zielId1=beziehung.zielId1,
                typ2=beziehung.typ2,
                name2=beziehung.name2,
                zielId2=beziehung.zielId2,
                beziehungstyp=beziehung.beziehungstyp,
                beschreibung=beziehung.beschreibung,
            ),
        )
        anzahl += 1

    return anzahl


async def importiere(campaign_id: str, dateiname: str, inhalt: bytes) -> ImportAntwort:
    """Kompletter Ablauf: Text extrahieren → KI gliedert → Entwürfe anlegen
    → Auto-Verknüpfung je Seite. Wirft ``DokumentFormatFehler``/
    ``DokumentZuGrossFehler``/``KiFehler`` bei Problemen (von der Route in
    passende HTTP-Fehler übersetzt).
    """
    text = dokument_zu_text(dateiname, inhalt)
    if not text.strip():
        raise DokumentFormatFehler("Das Dokument enthält keinen lesbaren Text.")

    vorschlaege = await gliedere_dokument(campaign_id, text)
    if not vorschlaege:
        raise KiFehler("Die KI konnte keine Wiki-Seiten aus dem Dokument ableiten.")

    # Seiten zuerst OHNE Elternbeziehung anlegen — die echten IDs der
    # potenziellen Elternseiten stehen erst danach fest (elternIndex zeigt
    # auf die Position in `vorschlaege`, nicht auf eine bereits existierende
    # Seiten-ID). Zweiter Durchlauf verknüpft dann per update_seite.
    angelegte_ids: list[str] = []
    for vorschlag in vorschlaege:
        seite = await repository.create_seite(
            campaign_id,
            titel=vorschlag.titel,
            inhalt=_text_zu_dokument(vorschlag.inhalt),
            ist_entwurf=True,
            sichtbarkeit="GM",
            sichtbar_fuer=[],
        )
        if seite is None:
            raise KiFehler("Kampagne nicht gefunden")
        angelegte_ids.append(seite["id"])

    ergebnis_seiten: list[ImportierteSeite] = []
    for i, vorschlag in enumerate(vorschlaege):
        seiten_id = angelegte_ids[i]
        parent_id: str | None = None
        eltern_index = vorschlag.elternIndex
        if (
            eltern_index is not None
            and 0 <= eltern_index < len(angelegte_ids)
            and eltern_index != i
        ):
            parent_id = angelegte_ids[eltern_index]
            await repository.update_seite(campaign_id, seiten_id, {"parentId": parent_id})

        anzahl_verknuepfungen = await _auto_verknuepfen(campaign_id, seiten_id)
        ergebnis_seiten.append(
            ImportierteSeite(
                id=seiten_id,
                titel=vorschlag.titel,
                parentId=parent_id,
                verknuepfungen=anzahl_verknuepfungen,
            )
        )

    return ImportAntwort(seiten=ergebnis_seiten)
