"""Was ein Spieler von der Initiativliste sehen darf.

Marks Vorgabe: *"die Spieler dürfen nur die Alias Namen der NPCs sehen nicht
ihre richtigen Namen!"* — die Liste selbst bleibt vollständig sichtbar
(Reihenfolge, Initiative, wer dran ist), nur die Identität der Gegner ist
geschützt.

Baut auf `app/kontakte/logic.py` auf: dieselbe Aliaslogik wie im Messenger,
damit ein NPC nicht im Kampf anders heisst als im Kontaktverzeichnis.
"""

from app.kontakte.logic import effektiver_alias, standard_alias


def fuer_spieler(
    teilnehmer: list[dict],
    rassen: dict[str, str],
    aliase: dict[str, str] | None = None,
    eigene_person_id: str | None = None,
    begleiter_besitzer: dict[str, str] | None = None,
    npc_ids: set[str] | None = None,
) -> list[dict]:
    """Ersetzt echte NPC-Namen durch Aliase und entfernt SL-Notizen.

    ``rassen`` bildet Personen-Kennung auf Rasse ab (für "Unbekannter Ork"),
    ``aliase`` optional auf einen persönlichen Alias, sobald das Kontaktsystem
    steht. ``begleiter_besitzer`` und ``npc_ids`` verdecken Drohnen und
    Begleiter von NPCs — sonst verriete "Kampfdrohne von Viktor" den Namen
    durch die Hintertür.

    Arbeitet auf Kopien: die Liste wird pro Aufruf gefiltert, das Original
    bleibt für andere Empfänger unberührt.
    """
    aliase = aliase or {}
    begleiter_besitzer = begleiter_besitzer or {}
    npc_ids = npc_ids or set()

    gefiltert = []
    for eintrag in teilnehmer:
        t = dict(eintrag)
        person_id = t.get("personId")
        eigener = bool(person_id) and person_id == eigene_person_id

        if t.get("personType") == "NPC" and person_id:
            # Der echte Name verschwindet vollständig — er darf nicht einmal
            # in einem anderen Feld weiterleben.
            t["name"] = effektiver_alias(
                standard_alias(rassen.get(person_id)),
                aliase.get(person_id),
            )
        elif t.get("begleiterId"):
            besitzer = begleiter_besitzer.get(t["begleiterId"])
            if besitzer and besitzer in npc_ids:
                t["name"] = "Unbekannte Begleitung"

        # Die Notiz ist die Gedächtnisstütze der Spielleitung ("blutet stark",
        # "flieht bei 2 HP") — nur am eigenen Charakter sinnvoll sichtbar.
        if not eigener:
            t["notiz"] = ""

        gefiltert.append(t)

    return gefiltert
