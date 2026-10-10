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

# Richtwerte aus Marks Excel-Regelwerk (docs/reference/Neotopia_Gegenstaende.md,
# selbst .gitignore't — siehe pnptool-development-Skill/ki-gemini-integration.md
# "Trait-Beschreibungen"-Muster). Gekürzt auf das Preis-/Stärke-relevante je
# Typ, damit der Prompt kurz bleibt — kein Abtippen der ganzen Tabelle.
# Mark (10.10.2026): Richtwert-Kontext, KEINE harte Grenze — die KI darf
# begründet abweichen (Einzelstück, Rabatt, Spezialanfertigung), soll sich
# aber an der Größenordnung orientieren statt frei zu raten. Von BEIDEN
# KI-Einstiegspunkten genutzt (vorschlaege() UND ware_anlegen()), eine Quelle.
_RICHTWERTE: dict[str, str] = {
    "Waffe": (
        "Schadensbonus->Preis: 1=Schlagring/Knüppel ~50¥, 2=Dolch/Baseballschläger "
        "50-200¥, 3=Schwert/Leichte Pistole 400-1.000¥, 4=Schwere Pistole/Gewehr "
        "1.000-11.000¥, 5=Scharfschützengewehr 9.000-15.000¥, 6=MiniGun ~50.000¥, "
        "7=Raketenwerfer/Granate 1.800-10.000¥. SmartLink/erweitertes Magazin/"
        "Sonderanfertigung je +50% Waffenwert."
    ),
    "Rüstung": (
        "Rüstungsbonus->Preis (Beispiele je Slot): Bonus 1 ~100¥, Bonus 2 "
        "500-1.000¥, Bonus 3 (+Malus 1) ~1.500¥, Bonus 4 (+Malus 2) ~3.000¥. "
        "Bonus 3 gibt -1 auf Geschick, Bonus 4 gibt -2 auf Geschick."
    ),
    "Cyberware": (
        "Kosten pro Bonuspunkt (höherer Willenskraftverlust = günstiger): "
        "500¥/Punkt -> WVerlust Bonus×2, 2.000¥/Punkt -> WVerlust Bonus, "
        "5.000¥/Punkt -> WVerlust Bonus/2, 10.000¥/Punkt -> WVerlust Bonus/3, "
        "20.000¥/Punkt -> WVerlust Bonus/4. Prothese 10.000¥ (WVerlust 2), "
        "Prothesen-Gadget 5.000¥."
    ),
    "Bioware": (
        "Gleiche Kosten-/WVerlust-Staffel wie Cyberware: 500¥/Punkt (WVerlust "
        "Bonus×2) bis 20.000¥/Punkt (WVerlust Bonus/4)."
    ),
    "Droge": (
        "Richtwert nach Stärke des Effekts: leichte Boni (einzelner Wert +2-3 "
        "für eine Szene) 100-300¥, starke Kampfdrogen (Extra-Aktionen, mehrere "
        "Attribute) 500-1.000¥, militärisch/illegal mit großer Wirkung und "
        "harter Nebenwirkung 1.000-2.500¥. Jede Droge braucht eine spürbare "
        "Nebenwirkung passend zur Stärke."
    ),
    "Commlink": (
        "Cyberwall (I.C.E.) bestimmt den Preis: 200¥/Punkt bis Cyberwall 5, "
        "danach 500¥/Punkt (Beispiele: Cyberwall 1 = 100¥, 3 = 1.000¥, "
        "5 = 5.000¥, 6 = 8.000¥)."
    ),
    "Riggerkonsole": (
        "Rigger-Bonus (kann negativ sein) und maximale Drohnenzahl treiben den "
        "Preis: improvisiert (-2 Bonus, 1 Drohne) ~1.400¥, solide Einsteiger-"
        "konsole (0-1 Bonus, 1-2 Drohnen) 8.000-16.000¥, gehobene Konsole "
        "(2-3 Bonus, 2-4 Drohnen) 32.000-66.000¥, High-End (4-6 Bonus, "
        "5-16 Drohnen) 75.000-140.000¥."
    ),
    "Cyberdeck": (
        "Vier Matrix-Werte (Brute Force/Schleichen/Daten/Kompilieren) treiben "
        "den Preis: niedrig (alle ~1) ~25.000¥, mittel (Summe ~8-10) "
        "95.000-150.000¥, hochwertig (Summe ~12+) 400.000¥+. Zusätzliche "
        "Cyberwall-Boni auf dem Deck selbst nur bei absoluten Spitzenmodellen."
    ),
    "Fahrzeug": (
        "Preisformel nach Stufe: Stufe × 5.000¥ bis Stufe 5, ab Stufe 5 × "
        "20.000¥, ab Stufe 10 × 40.000¥ (Beispiele: Stufe 5 = 25.000¥, "
        "Stufe 10 = 200.000¥, Stufe 15 = 600.000¥)."
    ),
    "Drohne": (
        "Preisformel nach Stufe: Stufe × 500¥ bis Stufe 5, ab Stufe 5 × "
        "1.000¥, ab Stufe 10 × 5.000¥ (Beispiele: Stufe 5 = 2.500¥, "
        "Stufe 10 = 10.000¥, Stufe 15 = 25.000¥)."
    ),
}

_RICHTWERT_FALLBACK = (
    "Kein fester Richtwert für diesen Typ hinterlegt — realistischen Preis "
    "wie bei einem vergleichbaren echten Gegenstand ansetzen (€ = ¥ in dieser Welt)."
)

_RICHTWERTE_TEXT = "\n".join(f"- {typ}: {text}" for typ, text in _RICHTWERTE.items())

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
    + ". Vermeide Duplikate zu bereits genannten Vorschlägen. preis in Nuyen, "
    "orientiert an diesen Richtwerten aus dem Regelwerk (Orientierung, keine "
    "starre Vorgabe — bei einem begründeten Sonderfall darfst du abweichen):\n"
    + _RICHTWERTE_TEXT
    + "\nseltenheit 1 (überall erhältlich) bis 5 (nur Speziallabor/Schwarzmarkt) "
    "— nur relevant für neu erfundene Ware, bei bestehenden Vorlagen wird sie "
    "ignoriert."
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
    ergebnis = await generiere_json(prompt, _SYSTEM, _SCHEMA, campaign_id=campaign_id)

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


class WareAnlegenErgebnis(BaseModel):
    name: str
    preis: int
    bildHinweis: str = ""


_WARE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "name": {"type": "STRING"},
        "beschreibung": {"type": "STRING"},
        "notizen": {"type": "STRING"},
        "preis": {"type": "INTEGER"},
        "seltenheit": {"type": "INTEGER"},
    },
    "required": ["name", "beschreibung", "preis"],
}


async def ware_anlegen(
    campaign_id: str, haendler_id: str, prompt: str, typ: str, bild: bool
) -> WareAnlegenErgebnis | None:
    """Legt eine Vorlage in der gewählten Kategorie an und hängt sie an den Laden.

    Der Typ kommt von der Kategorie, in der die SL gerade steht — die KI
    darf ihn nicht umbiegen. Bild ist optional und darf den Gegenstand
    nicht mitreißen, wenn die Generierung scheitert.
    """
    if typ not in GEGENSTAND_TYPEN:
        raise ValueError(f"Unbekannter Gegenstandstyp: {typ}")
    haendler = await repository.hole(campaign_id, haendler_id)
    if haendler is None:
        return None

    system = (
        "Du erfindest EINEN Gegenstand für einen Laden in der Welt von NeotopiA "
        "(deutsches Cyberpunk-Pen-and-Paper). Der Typ ist fest vorgegeben und "
        "darf nicht geändert werden. preis in Nuyen. "
        f"Richtwert für Typ '{typ}': {_RICHTWERTE.get(typ, _RICHTWERT_FALLBACK)} "
        "Das ist eine Orientierung aus dem Regelwerk, keine starre Vorgabe — "
        "bei einem begründeten Sonderfall (Einzelstück, Billigware, "
        "Spezialanfertigung) darfst du sinnvoll abweichen. "
        "seltenheit 1 (überall erhältlich) bis 5 (Speziallabor/Schwarzmarkt)."
    )
    ergebnis = await generiere_json(
        f"Laden: {haendler['name']}\nKategorie: {typ}\nWunsch: {prompt.strip()}",
        system,
        _WARE_SCHEMA,
        campaign_id=campaign_id,
    )
    name = (ergebnis.get("name") or "").strip() or "Unbenannte Ware"
    beschreibung = (ergebnis.get("beschreibung") or "").strip()
    preis = max(0, int(ergebnis.get("preis") or 0))
    seltenheit = max(1, min(int(ergebnis.get("seltenheit") or 1), 5))
    body = GegenstandCreate(
        name=name,
        description=beschreibung,
        notes=(ergebnis.get("notizen") or "").strip(),
        typ=typ,
        preis=preis,
        seltenheit=seltenheit,
        istEntwurf=False,
    )
    gegenstand = await create_gegenstand(campaign_id, None, _create_data(body, True, "GM", []))
    if gegenstand is None:
        return None
    if not await repository.verkauft_hinzufuegen(campaign_id, haendler_id, gegenstand["id"], preis):
        return None

    bild_hinweis = ""
    if bild:
        try:
            from app.items.routes import speichere_bild_bytes
            from app.ki.bildgenerierung import generiere_bild

            inhalt, content_type = await generiere_bild(
                "cloud",
                f"Produktsfoto, cyberpunk, {typ}: {name}. {beschreibung}",
            )
            url = speichere_bild_bytes(campaign_id, inhalt, content_type)
            from app.items.repository import set_bild_url

            await set_bild_url(campaign_id, gegenstand["id"], url)
        except Exception as e:
            bild_hinweis = str(e) or "Bildgenerierung fehlgeschlagen"
    return WareAnlegenErgebnis(name=name, preis=preis, bildHinweis=bild_hinweis)
