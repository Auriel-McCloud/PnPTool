"""Einmaliges Import-Skript (10.10.2026, Marks Wunsch): übernimmt die
vorgefertigten Gegenstände aus Marks Excel-Transkription
(docs/reference/Neotopia_Gegenstaende.md) als Entwürfe in eine Kampagne.

Bewusst NICHT als UI-Feature gebaut (Mark: "einmaliges Skript jetzt reicht") —
kein eigener Endpunkt, kein Knopf im Tool. Legt jeden Eintrag als
istEntwurf=true-Vorlage an (gleiches Muster wie jeder andere KI-/Ideenschmiede-
Import), damit die SL jeden einzeln in der Ideenschmiede sichten und
freigeben kann, bevor er im Spiel auftaucht — kein Autocommit in die aktive
Kampagne.

Nutzt denselben Helfer wie die echten Anlege-Routen
(items/routes.py::_create_data + items/repository.py::create_gegenstand),
keine eigene Parallel-Logik.

Aufruf (im Backend-.venv, Pfad relativ zu backend/):
    .venv/Scripts/python.exe scripts/import_gegenstaende_aus_regelwerk.py <campaign_id>

Ohne Argument bricht das Skript ab — die Kampagnen-ID muss explizit genannt
werden (Mark: bebop-Kampagne "BÆ-B3L^-1" auf KEINEN Fall versehentlich
überschreiben, nur Items hinzufügen).
"""

import asyncio
import sys

from app.items.repository import create_gegenstand, list_alle_gegenstaende
from app.items.routes import _create_data
from app.items.schemas import GegenstandCreate

# --- Rüstung (Zeilen 41-50 der Tabelle) -------------------------------------
RUESTUNG = [
    # (name, slot, effekt_text, preis, ruestungsbonus)
    ("MonoVisor-Helm", "Kopf", "Rüstungsbonus 1", 100, 1),
    ("Aegis-2 Tactical Helm", "Kopf", "Rüstungsbonus 2", 1000, 2),
    ("NeoFlex-Jacke", "Torso", "Rüstungsbonus 1", 100, 1),
    ("Urban Defender Vest", "Torso", "Rüstungsbonus 2", 500, 2),
    ("Titan-Frame Assault Suit", "Torso", "Rüstungsbonus 3, Malus 1 auf Geschick", 1500, 3),
    ("Cerberus-15 Heavy Blast Suit", "Torso", "Rüstungsbonus 4, Malus 2 auf Geschick", 3000, 4),
    ("SynthWeave-Pants", "Beine", "Rüstungsbonus 1", 100, 1),
    ("HexaMesh Combat Trousers", "Beine", "Rüstungsbonus 2", 1000, 2),
]

# --- Commlinks (Zeilen 72-79) ------------------------------------------------
COMMLINKS = [
    # (name, cyberwall, preis)
    ("Meta Link", 1, 100),
    ("Sony Emperer", 2, 700),
    ("Renraku Sensei", 3, 1000),
    ("Erika Elite", 4, 2500),
    ("Hermes Ikon", 5, 5000),
    ("Transs Avalon", 6, 8000),
]

# --- Riggerkonsolen (Zeilen 89-98) ------------------------------------------
RIGGERKONSOLEN = [
    # (name, rigger_bonus, max_drohnen, preis)
    ("Aus Schrott gebastelt", -2, 1, 1400),
    ("Allegiance Control Center", 0, 1, 8000),
    ("Essy Motos DroneMaster", 1, 2, 16000),
    ("Horizon Oversser", 2, 2, 32000),
    ("Maersk Spider", 1, 3, 34000),
    ("Vulcan Liegelord", 3, 4, 66000),
    ("Ares Red Dog", 4, 5, 75000),
    ("Saeder-Krupp Nexus", 5, 8, 95000),
    ("Renraku Hive", 6, 16, 140000),
]

# --- Cyberdecks (Zeilen 105-115, nur Modelle mit bekanntem Preis) -----------
CYBERDECKS = [
    # (name, brute_force, schleichen, daten, kompilieren, preis, cyberwall_bonus)
    ("Erika MCD-6", 1, 1, 1, 1, 24750, 0),
    ("Spnrad Falcon", 2, 1, 1, 2, 61500, 0),
    ("MCT 360", 1, 3, 2, 2, 95000, 0),
    ("Renraku Kitsune", 2, 3, 3, 1, 107000, 0),
    ("Shiawase Cyber-6", 4, 2, 3, 3, 149000, 0),
    ("Fairlight Excalibur", 3, 4, 2, 2, 410600, 0),
    ("Ono-Sendai Cyberspace VII", 5, 5, 5, 5, 999998, 4),
]

# --- Drogen (Zeilen 121-128) -------------------------------------------------
DROGEN = [
    # (name, wirkung, nebenwirkung, preis)
    ("\"Dash\" (Combat Speed)", "Geschicklichkeit +2, Initiative +2 für 3 Runden",
     "Danach -2 auf alle Würfe für 10 Minuten (Erschöpfung)", 200),
    ("\"Redline\" (Adrenalin-Booster)", "Eine Kampfrunde: zwei zusätzliche Aktionen",
     "Danach 5 Minuten -3 auf alle Würfe (Nervenschäden)", 500),
    ("\"Ghost\" (Neural Overclock)", "+2 auf Hacking-/Neurowave-Würfe für eine Szene",
     "Danach 10 Minuten keine Cyberware/Matrix nutzbar (Overload)", 300),
    ("\"Synapse\" (Denker-Modus)", "Geistesschärfe +3 für eine Szene",
     "Danach -2 Geistesschärfe für 3 Stunden (mentale Überlastung)", 600),
    ("\"Chrome\" (Euphorie & Schmerzunterdrückung)",
     "Willenskraftverlust durch Cyberware für eine Szene negiert",
     "Während der Wirkung -1 auf Geistesschärfe & Wahrnehmung", 150),
    ("\"Neon Dust\" (Halluzinogen)",
     "Euphorie, visuelle Halluzinationen, kein Angstgefühl für eine Szene",
     "Während der Wirkung -2 auf alle mentalen Proben", 100),
    ("\"Blackout\" (Schmerz- & Traumablocker)",
     "Nächste Szene: kein Aufhalten durch Schlagschaden",
     "Danach 48h Koma oder Tod (Konstitutionswurf nötig)", 1000),
    ("\"Overclock\" (illegale Militärdroge)",
     "Alle körperlichen Werte +3, doppelte Bewegung, Angstimmunität für 5 Minuten",
     "Danach 24h -3 auf alle körperlichen Werte (Organschäden)", 2500),
]

# --- Waffen-Richtwerte (Zeilen 58-64) — als repräsentative Beispiele, kein
# konkretes Markenmodell im Excel genannt, deshalb bewusst generische Namen.
# schadenArt: schlag / schwer (Tödlich) / aggraviert (Unheilbar).
WAFFEN = [
    # (name, schaden, schaden_art, preis, beschreibung)
    ("Schlagring", 1, "schlag", 50, "Einfache Nahkampfwaffe für die Faust."),
    ("Dolch", 2, "schwer", 100, "Leichte, verdeckt tragbare Klingenwaffe."),
    ("Leichte Pistole", 3, "schwer", 700, "Standard-Handfeuerwaffe, leicht zu beschaffen."),
    ("Schwere Pistole", 4, "schwer", 3000, "Kräftigere Faustfeuerwaffe mit mehr Durchschlag."),
    ("Scharfschützengewehr", 5, "schwer", 12000, "Präzisionswaffe für Entfernung."),
    ("MiniGun", 6, "schwer", 50000, "Schwere automatische Waffe, selten in Zivilhand."),
    ("Raketenwerfer", 7, "aggraviert", 6000, "Militärische Großwaffe, extrem destruktiv."),
]

# --- Reflex-Booster (Cyberware-Idee, Zeilen 421-444) — eigens ausformulierte
# Mechanik, nachträglich ergänzt (10.10.2026, beim ersten Lauf übersehen:
# stand im Excel unter einem eigenen "Cyberware-Idee"-Abschnitt, nicht in der
# allgemeinen Cyberware-Kostentabelle). initiativeBonus und zusatzaktionen
# sind bereits voll im Kampfmodus verdrahtet (kampf/booster.py) — hier nur
# Preis/WVerlust/Beschreibung je Stufe setzen, keine neue Mechanik nötig.
# zusatzaktionen: 1 (Stufe 1), 2 (Stufe 2), -1 = jede Runde (Stufe 3).
REFLEX_BOOSTER = [
    # (name, initiative_bonus, zusatzaktionen, w_verlust, preis, beschreibung)
    (
        "Reflex-Booster (Günstig)", 1, 1, 1.0, 5000,
        "Initiative +1; einmal pro Kampf eine zusätzliche Aktion (nur Bewegung oder Angriff).",
    ),
    (
        "Reflex-Booster (Militärisch)", 3, 2, 2.0, 20000,
        "Initiative +3; zweimal pro Kampf eine zusätzliche Aktion; Gegner -1 Würfel beim Zielen auf dich.",
    ),
    (
        "Reflex-Booster (Illegales Prototypen-Modell)", 6, -1, 4.0, 50000,
        "Initiative +6; jede Runde eine zusätzliche Aktion; Gegner -2 Würfel beim Zielen. "
        "Nachteil: Überhitzung — nach 3 Runden in Folge Geistesschärfe+Willenskraft-Probe gegen 3, "
        "sonst 1 Runde paralysiert.",
    ),
]


def _vorlage(name: str, typ: str, beschreibung: str, preis: int, **extra) -> GegenstandCreate:
    return GegenstandCreate(
        name=name,
        description=beschreibung,
        typ=typ,
        preis=preis,
        istEntwurf=True,
        **extra,
    )


def _sammlung() -> list[GegenstandCreate]:
    vorlagen: list[GegenstandCreate] = []

    for name, slot, effekt, preis, bonus in RUESTUNG:
        vorlagen.append(
            _vorlage(
                name, "Rüstung", f"{slot}-Rüstung. {effekt}.", preis,
                ruestungReduktionBasis=bonus, ruestungKaestchenMax=bonus * 2,
            )
        )

    for name, cyberwall, preis in COMMLINKS:
        vorlagen.append(
            _vorlage(name, "Commlink", f"Commlink mit Cyberwall (I.C.E.) {cyberwall}.", preis,
                      cyberwall=cyberwall)
        )

    for name, rigger_bonus, max_drohnen, preis in RIGGERKONSOLEN:
        vorlagen.append(
            _vorlage(
                name, "Riggerkonsole",
                f"Riggerkonsole, Rigger-Bonus {rigger_bonus:+d}, max. {max_drohnen} Drohne(n).",
                preis, riggerBonus=rigger_bonus, maxDrohnen=max_drohnen,
            )
        )

    for name, bf, sl, da, ko, preis, cw_bonus in CYBERDECKS:
        beschreibung = f"Cyberdeck B/S/D/K {bf}/{sl}/{da}/{ko}."
        if cw_bonus:
            beschreibung += f" Cyberwall +{cw_bonus}."
        vorlagen.append(
            _vorlage(
                name, "Cyberdeck", beschreibung, preis,
                deckBruteForce=bf, deckSchleichen=sl, deckDaten=da, deckKompilieren=ko,
            )
        )

    for name, wirkung, nebenwirkung, preis in DROGEN:
        vorlagen.append(
            _vorlage(name, "Droge", f"Wirkung: {wirkung} Nebenwirkung: {nebenwirkung}", preis)
        )

    for name, schaden, schaden_art, preis, beschreibung in WAFFEN:
        vorlagen.append(
            _vorlage(
                name, "Waffe", beschreibung, preis,
                istWaffe=True, schaden=schaden, kraft=schaden, schadenArt=schaden_art,
            )
        )

    for name, init_bonus, zusatzaktionen, w_verlust, preis, beschreibung in REFLEX_BOOSTER:
        vorlagen.append(
            _vorlage(
                name, "Cyberware", beschreibung, preis,
                initiativeBonus=init_bonus, zusatzaktionen=zusatzaktionen, wVerlust=w_verlust,
                koerperzone="Kopf",
            )
        )

    return vorlagen


async def main(campaign_id: str) -> None:
    vorlagen = _sammlung()

    # Dedupe: Namen, die als Vorlage (egal ob Entwurf oder freigegeben) schon
    # existieren, werden übersprungen — ein zweiter Lauf des Skripts (z.B.
    # nach einem Abbruch) darf nichts verdoppeln.
    bestehende = await list_alle_gegenstaende(campaign_id)
    bestehende_namen = {g["name"] for g in bestehende if g.get("istVorlage")}

    angelegt = 0
    uebersprungen = 0
    for body in vorlagen:
        if body.name in bestehende_namen:
            uebersprungen += 1
            print(f"übersprungen (existiert bereits): {body.name}")
            continue
        data = _create_data(body, True, "GM", [])
        gegenstand = await create_gegenstand(campaign_id, None, data)
        if gegenstand is None:
            print(f"FEHLER beim Anlegen: {body.name}")
            continue
        angelegt += 1
        print(f"angelegt (Entwurf): {body.name} — {body.preis}¥")

    print(f"\nFertig: {angelegt} neu angelegt, {uebersprungen} übersprungen "
          f"(bereits vorhanden), insgesamt {len(vorlagen)} Einträge aus dem Regelwerk.")
    print("Alle neuen Einträge sind istEntwurf=true — in der Ideenschmiede "
          "einzeln prüfen und freigeben.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Aufruf: python scripts/import_gegenstaende_aus_regelwerk.py <campaign_id>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
