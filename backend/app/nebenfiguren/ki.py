"""KI-Erzeugung einer Nebenfigur — ein einziger, billiger KI-Aufruf.

Blanko-Kontakte aus dem Kontakte-Hintergrund werden seit 10.11.2026 als
Nebenfigur befüllt statt als voller NPC (Mark: „nur Mentoren als richtige
NPCs“). Kein Bogen, kein Tutorial-Shop-Einkauf — dadurch ein KI-Aufruf statt
drei.
"""

from fastapi import HTTPException

from app.entities.repository import PERSON_FIELDS, create_node
from app.entities.schemas import Nebenfaehigkeit, PersonCreate
from app.ereignisprotokoll import hooks
from app.ki.client import KiFehler, generiere_json
from app.ki.kontext import sammle_kontext
from app.ki.routes import _SYSTEM, _mit_kontext, _rassen_fuer_ki, _text_zu_dokument
from app.nebenfiguren.logic import nebenfaehigkeiten_saeubern, persoenlichkeit_saeubern
from app.rassen import repository as rassen_repository

_NEBENFIGUR_SYSTEM = (
    _SYSTEM
    + " Erschaffe eine einzelne Nebenfigur in NeotopiA — einen Kontakt, Angehörigen "
    "oder Bekannten, der NICHT kämpft und keinen Charakterbogen hat. name ist der "
    "Eigenname. persoenlichkeit ist EIN kurzes Stichwort (z.B. Leitwolf, Angsthase, "
    "Schlitzohr), höchstens drei Wörter. faehigkeiten sind 1 bis 3 frei benannte "
    "Stärken, die für die Spieler nützlich sind (Wissen, Verhandeln, Beziehungen — "
    "keine Kampfwerte), wert 1 bis 5. beschreibung ist kurz und im Spiel sichtbar; "
    "notizen ist das SL-interne Feld für alles Weitere (Motive, Geheimnisse, Haken). "
    "beziehung: nennt der Auftrag einen Bezug („Bezieht sich auf …“), steht hier in 1 bis 3 "
    "Wörtern, wie diese Figur dazu steht (z.B. Mutter von, Bruder von, Stammgast in, "
    "Informant von) — sonst leer."
)


def _schema(rassen_namen: list[str]) -> dict:
    return {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING"},
            "rasse": {"type": "STRING", "enum": rassen_namen},
            "alter": {"type": "STRING"},
            "persoenlichkeit": {"type": "STRING"},
            "beschreibung": {"type": "STRING"},
            "notizen": {"type": "STRING"},
            "beziehung": {"type": "STRING"},
            "faehigkeiten": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {"name": {"type": "STRING"}, "wert": {"type": "INTEGER"}},
                    "required": ["name", "wert"],
                },
            },
        },
        "required": ["name", "rasse", "persoenlichkeit", "beschreibung", "notizen", "faehigkeiten"],
    }


async def nebenfigur_generieren(campaign_id: str, prompt: str, *, entwurf: bool = False) -> dict:
    """Legt eine Nebenfigur per KI an (SL-geheim) und gibt den Knoten zurück.

    ``entwurf=True`` für die Ideenschmiede (✨ KI, Massen, Beratung) — dort
    erst nach „Übernehmen“ in der Kampagne. Kontakt-Plätze bleiben ohne
    Entwurf. Der Knoten trägt zusätzlich ``beziehungVorschlag`` (nicht
    gespeichert): wie die Figur zum genannten Bezug steht.
    """
    rassen = _rassen_fuer_ki(await rassen_repository.liste_fuer_kampagne(campaign_id))
    rassen_namen = sorted(rassen.keys()) or ["Mensch"]
    kontext = await sammle_kontext(campaign_id)
    try:
        ergebnis = await generiere_json(
            _mit_kontext(prompt, kontext), _NEBENFIGUR_SYSTEM, _schema(rassen_namen), campaign_id=campaign_id
        )
    except KiFehler as e:
        raise HTTPException(status_code=502, detail=str(e))

    rasse = (ergebnis.get("rasse") or "").strip()
    if rasse not in rassen_namen:
        rasse = rassen_namen[0]
    name = (ergebnis.get("name") or "").strip() or "Unbenannte Nebenfigur"
    beschreibung = (ergebnis.get("beschreibung") or "").strip()
    notizen = (ergebnis.get("notizen") or "").strip()
    person = await create_node(
        "Person",
        PERSON_FIELDS,
        campaign_id,
        PersonCreate(
            name=name,
            personType="NPC",
            description=_text_zu_dokument(beschreibung) if beschreibung else "",
            notes=_text_zu_dokument(notizen) if notizen else "",
            rasse=rasse,
            alter=(ergebnis.get("alter") or "").strip(),
            istNebenfigur=True,
            persoenlichkeit=persoenlichkeit_saeubern(ergebnis.get("persoenlichkeit")),
            nebenfaehigkeiten=[
                Nebenfaehigkeit(**e) for e in nebenfaehigkeiten_saeubern(ergebnis.get("faehigkeiten"), ki=True)
            ],
            # Keine Ersterstellung: eine Nebenfigur hat nie einen Bogen.
            erstellungAbgeschlossen=True,
            istEntwurf=entwurf,
            sichtbarkeit="GM",
        ).model_dump(),
    )
    person["beziehungVorschlag"] = " ".join((ergebnis.get("beziehung") or "").split())[:40]
    await hooks.ki(
        campaign_id, anlass="nebenfigur", prompt=prompt,
        antwort_text=name, uebernommen=True, betrifft_id=person["id"],
    )
    return person
