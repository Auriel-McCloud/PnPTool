"""KI-Sortiment-Vorschlag für Händler: schlägt Waren vor, die zu Name,
Beschreibung und Spezialisierung des Händlers passen (Marks Wunsch
23.09.2026, aufbauend auf dem generischen KI-Gegenstandstyp der
Ideenschmiede, siehe ki/routes.py::_GEGENSTAND_SCHEMA).

Bevorzugt BESTEHENDE Gegenstands-Vorlagen der Kampagne wiederzuverwenden,
erfindet nur bei einer echten Lücke etwas Neues — dasselbe Vorrang-Prinzip
wie beim Story-/Charakter-Kontext (ki/kontext.py) und der Auto-Verknüpfung
(Marks Entscheidung: "beides: bevorzugt Bestehendes wiederverwenden, nur
bei Lücken etwas Neues vorschlagen").

Zweistufig wie auto_verknuepfung.py: `vorschlaege` ermittelt (nichts wird
gespeichert, der SL sieht erst eine Liste), `anwenden` übernimmt EINEN
bestätigten Vorschlag ins Sortiment — bei einer neu erfundenen Ware wird
zuerst eine Vorlage angelegt (istEntwurf=true, wie jeder andere
KI-Gegenstand aus der Ideenschmiede), danach genau wie bei einer
bestehenden Vorlage ins Sortiment aufgenommen (repository.py::
verkauft_hinzufuegen). Bewusst PRO VORSCHLAG einzeln, kein Sammel-Übernehmen
(dieselbe Vorgabe wie bei der Auto-Verknüpfung: der SL prüft jede neue
Ware, kein Autocommit ganzer Listen in die Kampagne)."""

from pydantic import BaseModel

from app.haendler import repository
from app.items.repository import create_gegenstand, list_alle_gegenstaende
from app.items.routes import _create_data
from app.items.schemas import GEGENSTAND_TYPEN, GegenstandCreate
from app.ki.client import generiere_json

_SYSTEM = (
    "Du schlägst Waren für das Sortiment eines Händlers in der Welt von "
    "NeotopiA vor (deutsches Cyberpunk-Pen-and-Paper-Rollenspiel). Du "
    "bekommst Name/Beschreibung/Spezialisierung des Händlers sowie eine "
    "Liste bereits existierender Gegenstands-Vorlagen dieser Kampagne, die "
    "NOCH NICHT in seinem Sortiment sind. Bevorzuge IMMER bestehende "
    "Vorlagen aus dieser Liste, wenn sie zum Händler passen — setze dafür "
    "'gegenstandId' auf die exakte ID aus der Liste und 'name'/'typ' auf "
    "die dort genannten Werte. NUR wenn keine passende bestehende Vorlage "
    "existiert, erfinde eine neue Ware: dann 'gegenstandId' weglassen, "
    "'typ' MUSS exakt einer der folgenden Werte sein: "
    + ", ".join(GEGENSTAND_TYPEN)
    + ". Vermeide Duplikate zu bereits genannten Vorschlägen. preis in "
    "Nuyen, realistisch für den Typ. seltenheit 1 (überall erhältlich) bis "
    "5 (nur Speziallabor/Schwarzmarkt) — nur relevant für neu erfundene "
    "Ware, bei bestehenden Vorlagen wird sie ignoriert."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "vorschlaege": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "gegenstandId": {"type": "STRING"},
                    "name": {"type": "STRING"},
                    "typ": {"type": "STRING", "enum": list(GEGENSTAND_TYPEN)},
                    "beschreibung": {"type": "STRING"},
                    "preis": {"type": "INTEGER"},
                    "seltenheit": {"type": "INTEGER"},
                },
                "required": ["name", "typ", "preis"],
            },
        },
    },
    "required": ["vorschlaege"],
}


class SortimentVorschlag(BaseModel):
    # Gesetzt bei Wiederverwendung einer bestehenden Vorlage — "anwenden"
    # nimmt sie dann direkt ins Sortiment auf, statt eine neue anzulegen.
    gegenstandId: str | None = None
    name: str
    typ: str
    beschreibung: str = ""
    preis: int = 0
    seltenheit: int = 1


class VorschlaegeAntwort(BaseModel):
    vorschlaege: list[SortimentVorschlag] = []


async def vorschlaege(campaign_id: str, haendler_id: str, anzahl: int = 5) -> VorschlaegeAntwort:
    """Lässt die KI Sortiment-Lücken für diesen Händler füllen.

    Die Kandidatenliste bestehender Vorlagen schließt bewusst alles aus,
    was bereits im Sortiment steht (explizit ODER automatisch, siehe
    repository.py::sortiment) — sonst würde die KI ständig Ware
    vorschlagen, die der Händler ohnehin schon führt.
    """
    haendler = await repository.hole(campaign_id, haendler_id)
    if haendler is None:
        return VorschlaegeAntwort()

    aktuelles_sortiment = await repository.sortiment(campaign_id, haendler_id)
    bereits_ids = {e["gegenstandId"] for e in aktuelles_sortiment}

    alle = await list_alle_gegenstaende(campaign_id)
    kandidaten = [
        g for g in alle
        if g.get("istVorlage") and not g.get("istEntwurf") and g["id"] not in bereits_ids
    ]
    kandidaten_index = {g["id"]: g for g in kandidaten}

    liste_text = (
        "\n".join(f"- ({g['id']}) {g['name']} [{g['typ']}, {g['preis']}¥]" for g in kandidaten)
        or "(noch keine anderen Gegenstands-Vorlagen in dieser Kampagne)"
    )
    spezialisierung = ", ".join(haendler["spezialisierung"]) or "Gemischtwarenladen (keine Einschränkung)"

    prompt = (
        f"Händler: {haendler['name']}\n"
        f"Beschreibung: {haendler['beschreibung'] or '(keine)'}\n"
        f"Spezialisierung: {spezialisierung}\n\n"
        f"Bereits existierende Gegenstands-Vorlagen dieser Kampagne, noch NICHT "
        f"im Sortiment dieses Händlers:\n{liste_text}\n\n"
        f"Schlage {anzahl} Waren für das Sortiment vor."
    )
    ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA)

    vorschlags_liste: list[SortimentVorschlag] = []
    gesehen: set[str] = set()
    for eintrag in (ergebnis.get("vorschlaege") or [])[:anzahl]:
        gegenstand_id = (eintrag.get("gegenstandId") or "").strip() or None
        if gegenstand_id and gegenstand_id in kandidaten_index:
            # Wiederverwendung — Name/Typ/Preis von der echten Vorlage
            # übernehmen, nicht von der KI (Tippfehler/Halluzination
            # dürften den Bezug nicht verfälschen), analog
            # auto_verknuepfung.py: der Namensabgleich zählt, nicht der
            # KI-Text.
            vorlage = kandidaten_index[gegenstand_id]
            if gegenstand_id in gesehen:
                continue
            gesehen.add(gegenstand_id)
            vorschlags_liste.append(
                SortimentVorschlag(
                    gegenstandId=gegenstand_id,
                    name=vorlage["name"],
                    typ=vorlage["typ"],
                    beschreibung=vorlage.get("description") or "",
                    preis=vorlage.get("preis") or 0,
                )
            )
            continue

        name = (eintrag.get("name") or "").strip()
        typ = eintrag.get("typ") or ""
        if not name or typ not in GEGENSTAND_TYPEN or name in gesehen:
            continue
        gesehen.add(name)
        seltenheit = max(1, min(int(eintrag.get("seltenheit") or 1), 5))
        vorschlags_liste.append(
            SortimentVorschlag(
                name=name,
                typ=typ,
                beschreibung=(eintrag.get("beschreibung") or "").strip(),
                preis=max(0, int(eintrag.get("preis") or 0)),
                seltenheit=seltenheit,
            )
        )

    return VorschlaegeAntwort(vorschlaege=vorschlags_liste)


class AnwendenErgebnis(BaseModel):
    gegenstandId: str
    neuAngelegt: bool


async def anwenden(campaign_id: str, haendler_id: str, vorschlag: SortimentVorschlag) -> AnwendenErgebnis | None:
    """Übernimmt EINEN bestätigten Vorschlag ins Sortiment.

    Bei einer neu erfundenen Ware wird zuerst eine Vorlage angelegt
    (istEntwurf=true — der SL sieht sie danach auch in der Ideenschmiede
    und kann Details nachjustieren, bevor Spieler sie im Laden sehen;
    Marks Vorgabe: kein Autocommit direkt in die aktive Kampagne).
    """
    if vorschlag.gegenstandId:
        gegenstand_id = vorschlag.gegenstandId
        neu_angelegt = False
    else:
        body = GegenstandCreate(
            name=vorschlag.name,
            description=vorschlag.beschreibung,
            typ=vorschlag.typ,
            preis=vorschlag.preis,
            seltenheit=vorschlag.seltenheit,
            istEntwurf=True,
        )
        gegenstand = await create_gegenstand(campaign_id, None, _create_data(body, True, "GM", []))
        if gegenstand is None:
            return None
        gegenstand_id = gegenstand["id"]
        neu_angelegt = True

    if not await repository.verkauft_hinzufuegen(campaign_id, haendler_id, gegenstand_id, vorschlag.preis):
        return None
    return AnwendenErgebnis(gegenstandId=gegenstand_id, neuAngelegt=neu_angelegt)
