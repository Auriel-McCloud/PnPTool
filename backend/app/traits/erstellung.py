"""Charaktererstellung nach den NeotopiA-Regeln.

Quelle: `docs/reference/Neotopia.xlsx`, Blatt *Regeln*, Zeilen 1-42. Die
Zahlen stehen bewusst hier und nicht im Frontend — sonst müsste jede
Regeländerung an zwei Stellen nachgezogen werden, und die Prüfung, ob eine
eingereichte Erstellung überhaupt regelkonform ist, muss ohnehin auf dem
Server stattfinden.

Ablauf laut Excel:

1. Jeder startet mit **1 Punkt in allen Attributen**, verändert durch die
   Rasse (Zeile 2).
2. Die Rasse gibt drei Kontingente frei verteilbarer Attributpunkte
   (Mensch 7/5/3). Welches Kontingent auf körperlich, gesellschaftlich oder
   geistig fällt, entscheidet die Spielerin (Zeilen 20-22).
3. Fertigkeiten kommen aus einem von drei Paketen (Zeilen 28-30). Hexkraft,
   Sphären und NeuroWeaving zählen dabei als Fertigkeit (Zeile 27).
4. 15 Freebees zum Nachbessern (Zeilen 37-42).

Freebees dürfen über den **StartMax** der Rasse hinaus (Zeile 24), aber nicht
über das Maximum des Wertes selbst — ein Attribut endet bei 6, eine Fertigkeit
ebenfalls bei 6 (20.09.2026 von 5 angehoben, Marks Wunsch nach Einheitlichkeit).
Sphären zogen am 23.10.2026 nach (ebenfalls 5→6): pro Sphäre kam eine neue
Zwischenstufe dazu, "vollständig beherrschen" rutschte von Stufe 5 auf 6 —
siehe CLAUDE.md und `docs/reference/Master/*.md`. Das steht so nicht im Excel,
ergibt sich aber daraus, dass die Maxima für den ganzen Charakterbogen gelten
und nicht nur für die Erstellung.

**Noch nicht aus dem Regelwerk belegt** (Mark klärt das beim Feinschliff):
Hintergründe kommen im Excel nicht vor — die Liste unten ist ein Vorschlag
fürs Setting. Ebenso der Freebee-Preis von 1 je Hintergrundpunkt; vorgegeben
war nur Marks "bis zu 5 Punkte". Und ob Sphären beim Freebee-Kauf wie
Fertigkeiten zählen (2) oder wie Hexkraft (5) — Zeile 39 nennt nur
"Attribut / Hexkraft NeuroWeaving 5", Zeile 27 stellt Sphären aber zu den
Fertigkeiten. Hier gilt vorerst der Fertigkeitspreis.
"""

from typing import Any

# --- Attribute ---------------------------------------------------------

ATTRIBUT_KATEGORIEN = ["AttributKörperlich", "AttributGesellschaftlich", "AttributGeistig"]

KATEGORIE_NAMEN = {
    "AttributKörperlich": "Körperlich",
    "AttributGesellschaftlich": "Gesellschaftlich",
    "AttributGeistig": "Geistig",
}

ATTRIBUTE_JE_KATEGORIE = {
    "AttributKörperlich": ["Körperkraft", "Geschicklichkeit", "Widerstandsfähigkeit"],
    "AttributGesellschaftlich": ["Charisma", "Manipulation", "Fassung"],
    "AttributGeistig": ["Intelligenz", "Geistesschärfe", "Entschlossenheit"],
}

# Flache Liste aller neun Attribute — u.a. für die KI-Freebee-Zielliste
# (ki_routes baut daraus zusammen mit Fertigkeiten/Hintergründen das Enum,
# aus dem die KI ihre Freebee-Wünsche wählt).
ATTRIBUT_NAMEN_ALLE = [n for namen in ATTRIBUTE_JE_KATEGORIE.values() for n in namen]

# Jeder beginnt hier, bevor die Rasse etwas verändert (Zeile 2).
ATTRIBUT_GRUNDWERT = 1

# Obergrenze bei der Erstellung für ein unverändertes Attribut. Die
# Rassentabelle listet je Rasse den StartMax der von ihr berührten Attribute:
# ohne Änderung 4, bei +1 dann 5, bei +2 dann 6, bei -1 dann 3. Der Wert ist
# also durchgehend 4 + Modifikator, deshalb steht hier nur die Grundzahl.
ATTRIBUT_STARTMAX = 4

# --- Rassen (Zeilen 4-18) ----------------------------------------------
# freiePunkte: die drei Kontingente, frei auf die drei Attributspalten
# verteilbar. modifikatoren: Aufschlag auf Startwert *und* StartMax.

RASSEN: dict[str, dict[str, Any]] = {
    "Mensch": {
        "modifikatoren": {},
        "freiePunkte": [7, 5, 3],
        "beschreibung": "Wandlungsfähig ohne Sonderrechte — dafür die meisten freien Punkte.",
        # Rassen-Feature (10.10.2026, Mark: "2 Freebees mehr wäre garkeine
        # schlechte Idee" — "langweiliges Geld"). Budget-neutral, siehe
        # app/rassen/schemas.py.
        "bonusFreebees": 2,
    },
    "Elf": {
        "modifikatoren": {"Charisma": 1, "Geschicklichkeit": 1, "Widerstandsfähigkeit": -1},
        # War [5, 5, 3] (13) — +1 im zweiten Kontingent macht 14, siehe Ork.
        "freiePunkte": [5, 6, 3],
        "beschreibung": "Gewandt und einnehmend, körperlich aber nicht sonderlich zäh.",
    },
    "Ork": {
        "modifikatoren": {"Körperkraft": 1, "Intelligenz": -1},
        # War [6, 5, 3] (nur 14 — Nachteile brachten keine Punkte). Seit
        # Marks Fairness-Wunsch (05.10.2026: "ein Minus Punkt gibt einen
        # Punkt zurück, es soll immer 24 rauskommen") +1 im zweiten
        # Kontingent, macht 15 — siehe app/rassen/balance.py.
        "freiePunkte": [6, 6, 3],
        "beschreibung": "Kräftig gebaut, und nach dem Menschen am breitesten aufgestellt.",
    },
    "Zwerg": {
        "modifikatoren": {"Widerstandsfähigkeit": 1, "Fassung": 1, "Charisma": -1},
        # War [5, 5, 3] (13) — +1 im zweiten Kontingent macht 14, siehe Ork.
        "freiePunkte": [5, 6, 3],
        "beschreibung": "Hält aus und behält die Ruhe; Sympathien gewinnt er weniger leicht.",
    },
    "Troll": {
        "modifikatoren": {
            "Körperkraft": 2,
            "Widerstandsfähigkeit": 1,
            "Geistesschärfe": -1,
            "Geschicklichkeit": -1,
        },
        # War [5, 4, 3] (12) — 2 Nachteile geben jetzt 2 Punkte zurück,
        # macht 14. Beide im zweiten Kontingent (4 -> 6), siehe Ork.
        "freiePunkte": [5, 6, 3],
        "beschreibung": "Wuchtig und schwer umzuwerfen, dafür langsam von Auffassung und Hand.",
    },
}

# --- Wege ---------------------------------------------------------------
# Deckt sich mit Person.weg; hier zusätzlich mit Erklärtext für die Auswahl.

WEGE: list[dict[str, str]] = [
    {
        "id": "KEINER",
        # Hiess "Normal" — Marks Einwand: klingt fad. Wer weder zaubert noch
        # webt, ist nicht der Rest, sondern hat sich für einen anderen Weg
        # entschieden.
        "name": "Weg des Chroms",
        "beschreibung": "Du bist nicht geboren worden, du wurdest gebaut — Stück für Stück, Naht "
        "für Naht. Reflexe, die schneller sind als dein Gedanke. Augen, die durch Wände sehen. "
        "Arme, die Stahl biegen, und ein Rückgrat aus Legierung, das nicht bricht. Jedes Teil "
        "hast du dir verdient, gekauft oder aus jemandem herausgeschnitten. Fleisch war die "
        "Rohfassung. Du bist die Endversion.",
    },
    {
        "id": "MAGIER",
        "name": "Magier",
        "beschreibung": "Die Welt unterliegt deiner Vorstellungskraft. Es gibt „die“ Wirklichkeit "
        "— und es gibt deine. Warum hältst du der Welt keinen Spiegel vor und zeigst ihr, wie "
        "schön sie sein könnte? Oder wie grausam. Du bittest nicht um Erlaubnis, du korrigierst: "
        "Feuer, wo Regen war. Eine Tür, wo eine Wand stand. Nichts, wo eben noch jemand stand.",
    },
    {
        # Häretiker (24.09.2026, Marks Konzept, siehe CLAUDE.md Punkt 14):
        # mechanisch 100% identisch zu Magier — dieselbe Sphären-/Hexkraft-
        # Logik, nur andere Begriffe (Hexkraft→Glauben, Wilde Magie→
        # Blasphemie, Sphären→Götternamen). Eigene Karte bei der Erstellung,
        # aber KEIN eigener "weg"-Wert: das Frontend schickt bei dieser Wahl
        # weg="MAGIER" + magieFlavor="HAERETIKER" (siehe
        # frontend/src/traits/Charaktererstellung.tsx::SchrittWeg), damit die
        # gesamte Magie-Mechanik (bogen.py, items/routes.py, ki/routes.py)
        # nicht dupliziert werden muss.
        "id": "HAERETIKER",
        "name": "Häretiker",
        "beschreibung": "Nonne, Priester, Glaubenskrieger, Inquisitor — du glaubst an eine höhere "
        "Macht, in einer Welt, die den Glauben für tot erklärt hat. Und sie antwortet dir. Du "
        "betest nicht um Trost, du betest um Wirkung: Der Häretiker formt die Welt nach dem "
        "Willen seines Gottes. Segen für die, die zu dir halten. Und für die anderen das, was in "
        "den alten Büchern steht.",
    },
    {
        "id": "NEUROWEAVER",
        "name": "NeuroWeaver",
        "beschreibung": "Das Universum ist im Wandel. Ich spüre es in den Pixeln, ich spüre es im "
        "Datenstrom, ich rieche es in der Virtuellen Realität. Vieles, was einst war, ist "
        "verloren, da niemand mehr lebt, der sich erinnert, was es außerhalb der Matrix gab. Du "
        "bist die nächste Generation. Dein Körper ist nur noch Ballast, deine Realität ist die "
        "Matrix, und sie unterwirft sich deinem Willen. Nichts läuft mehr ohne sie. Nichts läuft "
        "mehr ohne dich.",
    },
]

# Auf dem Blatt steht "Hexkraft != NeuroWeaving" — beides zugleich gibt es nicht.
# "HAERETIKER" ist keine eigene Werte-Kategorie-Gruppe (siehe oben) — dieser
# Wert kommt in `weg` nie an, nur in `magieFlavor`, deshalb kein Eintrag hier.
KATEGORIEN_JE_WEG = {
    "KEINER": set(),
    "MAGIER": {"Hexkraft", "Sphäre"},
    "NEUROWEAVER": {"NeuroWeavingWert", "NeuroWeaving"},
}

# --- Fertigkeitspakete (Zeilen 28-30) -----------------------------------
# verteilung: Wert -> Anzahl der Fertigkeiten, die genau diesen Wert bekommen.

FERTIGKEITS_PAKETE: dict[str, dict[str, Any]] = {
    "PROFI": {
        "name": "Profi",
        "verteilung": {4: 1, 3: 3, 2: 3, 1: 1},
        "beschreibung": "Acht Fertigkeiten, eine davon herausragend. Wer weiß, was er kann — "
        "und was er lieber jemand anderem überlässt.",
    },
    "AUSGEGLICHEN": {
        "name": "Ausgeglichen",
        "verteilung": {3: 3, 2: 5, 1: 7},
        "beschreibung": "Fünfzehn Fertigkeiten ohne Ausreißer nach oben. Selten überfordert, "
        "selten der Beste im Raum.",
    },
    "VIELSEITIG": {
        "name": "Jack of all Trades",
        "verteilung": {3: 1, 2: 8, 1: 10},
        "beschreibung": "Neunzehn Fertigkeiten, überall ein Fuß in der Tür. Für alles zu "
        "gebrauchen, für nichts der Fachmann.",
    },
}

# Kategorien, aus denen sich ein Fertigkeitspaket bedienen darf. Zeile 27:
# "Hexkraft, Sphären, bzw. NeuroWeaving zählen als Fähigkeit" — gilt seit
# 27.09.2026 nur noch für Sphären/NeuroWeaving (die "Was ist möglich"-Werte).
# Hexkraft/NeuroWeavingWert selbst sind aus dem Fertigkeitskontingent raus
# und stehen als fixer Sockel da (siehe MAGIE_FIXWERT unten) — bleiben aber
# in dieser Menge, weil ein Profi-Spieler seinen "1"-Slot optional noch
# darauf verwenden darf (siehe pruefe()).
FERTIGKEITS_KATEGORIEN = {"Fertigkeit", "Hexkraft", "Sphäre", "NeuroWeavingWert", "NeuroWeaving"}

# --- Hintergründe -------------------------------------------------------
# VORSCHLAG, nicht aus dem Regelwerk. Bewusst wenige und klar unterscheidbare
# — eine lange Liste hilft bei der Erstellung niemandem weiter.

HINTERGRUENDE: list[dict[str, str]] = [
    {"name": "Kontakte", "beschreibung": "Leute, die ans Telefon gehen. Wie viele und wie gut vernetzt."},
    {"name": "Ressourcen", "beschreibung": "Regelmäßiges Einkommen, das nicht vom nächsten Auftrag abhängt."},
    {"name": "Straßenruf", "beschreibung": "Was man über dich erzählt, bevor du den Raum betrittst."},
    {"name": "Verbündete", "beschreibung": "Einzelne, die für dich einstehen — und selbst etwas können."},
    {"name": "Mentor", "beschreibung": "Jemand, der mehr weiß als du und dir bisweilen etwas davon abgibt."},
    {"name": "Unterschlupf", "beschreibung": "Ein Ort, den außer dir niemand kennt. Größe und Ausstattung."},
    {"name": "Schwarzmarkt", "beschreibung": "Zugang zu dem, was es offiziell nicht zu kaufen gibt."},
    {"name": "Konzernzugang", "beschreibung": "Ausweis, Freigabe, ein Name in einer Datenbank."},
    {"name": "Ausrüstung", "beschreibung": "Gerät über den Startbestand hinaus, das dir bereits gehört."},
    {"name": "Geheimwissen", "beschreibung": "Etwas, das kaum jemand weiß — und das jemand geheim halten will."},
]

HINTERGRUND_KATEGORIE = "Hintergrund"
HINTERGRUND_MAX = 5  # je Hintergrund
HINTERGRUND_PUNKTE_GESAMT = 5  # Marks Vorgabe: bis zu 5 Punkte insgesamt

# --- Freebees (Zeilen 37-42) -------------------------------------------

FREEBEES_GESAMT = 15
STARTKAPITAL = 10_000

# Preis je zusätzlichem Punkt, nach Kategorie des Wertes.
FREEBEE_KOSTEN_JE_KATEGORIE: dict[str, int] = {
    "AttributKörperlich": 5,
    "AttributGesellschaftlich": 5,
    "AttributGeistig": 5,
    "Hexkraft": 5,
    # Der NeuroWeaving-Wert zählt wie Hexkraft zu den Attributen, die vier
    # Fertigkeiten darunter wie Fertigkeiten.
    "NeuroWeavingWert": 5,
    "NeuroWeaving": 2,
    "Fertigkeit": 2,
    "Sphäre": 2,
    HINTERGRUND_KATEGORIE: 1,
}

FREEBEE_KOSTEN_WILLENSKRAFT = 1
# Zeile 42: Kredit ist billiger als Eigenkapital, weil er zurückgezahlt wird.
FREEBEE_KOSTEN_KREDIT = 1
FREEBEE_KOSTEN_EIGENKAPITAL = 2
KAPITAL_JE_FREEBEE = 10_000

# Zeile 40: eine Fertigkeit lässt sich per Freebee nur um einen Punkt heben.
FREEBEE_MAX_JE_FERTIGKEIT = 1

# --- Magiewert-Sockel (Mark, 27.09.2026) --------------------------------
# Vorher zählten Hexkraft/NeuroWeavingWert wie jede andere Fertigkeit zum
# Fertigkeitspaket — ein Magier/NeuroWeaver konnte also seine GESAMTEN
# Fertigkeitsslots in Hexkraft+Sphären (bzw. NeuroWeavingWert+NeuroWeaving)
# stecken und stand ohne jede Alltagsfertigkeit da (0 auf Wahrnehmung,
# Nahkampf, allem) — ein Handicap, das Chrom (kein eigener Magiewert)
# strukturell gar nicht treffen kann. Deshalb: Hexkraft/NeuroWeavingWert
# sind jetzt ein FESTER, kostenloser Sockel (wie der Attribut-Grundwert),
# kein frei wählbarer Fertigkeitsslot mehr. Nur mit dem Profi-Paket lässt
# sich zusätzlich der einzige "1"-Slot des Pakets darauf verwenden (+1,
# macht 4 statt 3) — "Profis können sonst eh nicht viel" (Mark). Freebees
# dürfen den fertigen Wert wie jeden anderen darüber hinaus anheben
# (FREEBEE_KOSTEN_JE_KATEGORIE gilt unverändert).
MAGIE_FIXWERT = 3
MAGIE_FIXWERT_PROFI_BONUS = 1
# category → Trait-Name, damit endwerte() weiß, wem der Sockel zusteht.
MAGIE_WERT_JE_KATEGORIE = {"Hexkraft": "Hexkraft", "NeuroWeavingWert": "NeuroWeaving"}
MAGIE_TRAIT_JE_WEG = {"MAGIER": "Hexkraft", "NEUROWEAVER": "NeuroWeaving"}


def startwerte(rasse: str, rassen: dict[str, dict[str, Any]] | None = None) -> dict[str, int]:
    """Attributwerte vor der Verteilung: Grundwert plus Rassenmodifikator."""
    mods = (rassen or RASSEN).get(rasse, {}).get("modifikatoren", {})
    werte = {}
    for attribute in ATTRIBUTE_JE_KATEGORIE.values():
        for name in attribute:
            werte[name] = ATTRIBUT_GRUNDWERT + mods.get(name, 0)
    return werte


def startmaxima(rasse: str, rassen: dict[str, dict[str, Any]] | None = None) -> dict[str, int]:
    """Obergrenzen bei der Erstellung. Freebees dürfen darüber (Zeile 24)."""
    mods = (rassen or RASSEN).get(rasse, {}).get("modifikatoren", {})
    maxima = {}
    for attribute in ATTRIBUTE_JE_KATEGORIE.values():
        for name in attribute:
            maxima[name] = ATTRIBUT_STARTMAX + mods.get(name, 0)
    return maxima


def lebensmaxima(
    rasse: str, katalog: list[dict], rassen: dict[str, dict[str, Any]] | None = None
) -> dict[str, int]:
    """Dauerhafte Obergrenzen der Attribute: Katalogmaximum + Rassenmodifikator.

    **Nicht zu verwechseln mit `startmaxima`.** Das sind zwei verschiedene
    Deckel, und ihre Verwechslung war der Bug (Mark, 11.09.2026: *"die Wahl
    der z.B. maximalen Stärke sollte sich ins Charakterblatt übertragen"*):

    * `startmaxima` = 4 + Modifikator. Gilt **nur während der Erstellung**;
      ein Mensch startet höchstens mit Körperkraft 4.
    * `lebensmaxima` = Katalogmaximum (6) + Modifikator. Gilt **dauerhaft**;
      ein Troll kommt bei Körperkraft auf 8, ein Elf bei
      Widerstandsfähigkeit nur auf 5.

    Hätte man `startmaxima` als Lebensdeckel ins Blatt geschrieben, wäre
    jeder Mensch für immer bei 4 gefangen gewesen.

    Liefert **alle Attribute**, nicht nur die von der Rasse berührten — auch
    die unveränderten mit ihrem Katalogwert. Das ist nötig, weil die
    Erstellung erneut eingereicht werden kann: stünden hier nur die
    berührten, behielte ein Charakter, der von Zwerg auf Mensch geändert
    wird, stillschweigend den Zwergen-Deckel auf Charisma (5 statt 6).

    Fertigkeiten bleiben bewusst aussen vor: dort gibt es keine
    Rassenmodifikatoren, und ein pauschales Überschreiben würde ein von der
    Spielleitung angehobenes Maximum ("Elder-NPC mit Schusswaffen 8")
    zunichtemachen.
    """
    mods = (rassen or RASSEN).get(rasse, {}).get("modifikatoren", {})
    return {
        eintrag["name"]: eintrag["defaultMax"] + mods.get(eintrag["name"], 0)
        for eintrag in katalog
        if eintrag["category"] in ATTRIBUT_KATEGORIEN
    }


def regelwerk(
    rassen: dict[str, dict[str, Any]] | None = None,
    einstellungen: dict[str, Any] | None = None,
    hintergrund_pool: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Alles, was die Oberfläche zum Führen durch die Erstellung braucht.

    `einstellungen` steuert die Mechanik-Hintergründe (siehe
    hintergruende/seed.py::SYSTEM_HINTERGRUENDE): deaktivierte tauchen im
    Pool gar nicht erst auf, der Kredit-Freebee wird separat über
    `freebees.kreditErlaubt` durchgereicht (Schulden ist kein Pool-Eintrag).

    `hintergrund_pool` ist der tatsächliche Katalog DIESER Kampagne (siehe
    hintergruende/repository.py::pool_fuer_erstellung — narrativer
    Baukasten-Katalog plus aktive Mechanik-Hintergründe). Ohne Angabe fällt
    das hier auf die alte fest verdrahtete `HINTERGRUENDE`-Liste zurück
    (z.B. im KI-Kommentar-Pfad, der nur `attributKategorien` braucht) —
    **diesen Fallback nicht für die echte Erstellung/Prüfung verwenden**,
    sonst laufen Baukasten und Erstellung wieder auseinander (Mark,
    13.10.2026: genau das war der gemeldete Bug).
    """
    einstellungen = einstellungen or {}
    if hintergrund_pool is not None:
        hintergruende_pool = hintergrund_pool
    else:
        deaktivierte_mechanik_namen = {
            name
            for name, schluessel in (("Mentor", "mentorAktiv"), ("Kontakte", "kontakteAktiv"))
            if not einstellungen.get(schluessel, True)
        }
        hintergruende_pool = [h for h in HINTERGRUENDE if h["name"] not in deaktivierte_mechanik_namen]
    return {
        "wege": WEGE,
        "rassen": [
            {
                "name": name,
                "modifikatoren": daten["modifikatoren"],
                "freiePunkte": daten["freiePunkte"],
                "beschreibung": daten["beschreibung"],
                "startwerte": startwerte(name, rassen),
                "startmaxima": startmaxima(name, rassen),
                "bildUrl": daten.get("bildUrl", ""),
                # Rassen-Features (10.10.2026, budget-neutral): reine
                # Durchreiche an die Oberfläche, Rechenlogik siehe
                # freebee_kosten()/endwerte() unten.
                "bonusFreebees": daten.get("bonusFreebees", 0),
                "gratisGegenstandId": daten.get("gratisGegenstandId", ""),
                "gratisErsterKaufTyp": daten.get("gratisErsterKaufTyp", ""),
                # Fehlte hier bisher (23.10.2026, Mark: Vael/Mimikry-Fund) —
                # ohne dieses Feld wusste die Charaktererstellung gar nicht,
                # dass eine Rasse automatisch eine Zusatzfertigkeit bekommt,
                # und konnte sie weder vorauswählen noch den Punkt automatisch
                # setzen. Die Vergabe selbst passiert serverseitig unverändert
                # in routes.py::erstelle_charakter, komplett unabhängig davon,
                # was hier an die Oberfläche durchgereicht wird.
                "gratisZusatzfertigkeitId": daten.get("gratisZusatzfertigkeitId", ""),
                "featureHinweis": daten.get("featureHinweis", ""),
            }
            for name, daten in (rassen or RASSEN).items()
        ],
        "attributKategorien": [
            {"id": k, "name": KATEGORIE_NAMEN[k], "attribute": ATTRIBUTE_JE_KATEGORIE[k]}
            for k in ATTRIBUT_KATEGORIEN
        ],
        "fertigkeitsPakete": [
            {
                "id": kennung,
                "name": paket["name"],
                "beschreibung": paket["beschreibung"],
                # Als Liste, damit die Reihenfolge feststeht: JSON-Objekte
                # haben keine zugesicherte Schlüsselreihenfolge.
                "verteilung": [
                    {"wert": w, "anzahl": a} for w, a in sorted(paket["verteilung"].items(), reverse=True)
                ],
                "anzahl": sum(paket["verteilung"].values()),
            }
            for kennung, paket in FERTIGKEITS_PAKETE.items()
        ],
        "hintergruende": hintergruende_pool,
        "hintergrundMax": HINTERGRUND_MAX,
        "hintergrundPunkteGesamt": HINTERGRUND_PUNKTE_GESAMT,
        "freebees": {
            "gesamt": FREEBEES_GESAMT,
            "kostenJeKategorie": FREEBEE_KOSTEN_JE_KATEGORIE,
            "kostenWillenskraft": FREEBEE_KOSTEN_WILLENSKRAFT,
            "kostenKredit": FREEBEE_KOSTEN_KREDIT,
            "kostenEigenkapital": FREEBEE_KOSTEN_EIGENKAPITAL,
            "kapitalJeFreebee": KAPITAL_JE_FREEBEE,
            "maxJeFertigkeit": FREEBEE_MAX_JE_FERTIGKEIT,
            # Schulden-Mechanik (siehe oben) deaktiviert: Oberfläche blendet
            # den Kredit-Regler aus, statt nur den Pool zu filtern.
            "kreditErlaubt": bool(einstellungen.get("schuldenAktiv", True)),
        },
        "startkapital": STARTKAPITAL,
        # Magiewert-Sockel (siehe MAGIE_FIXWERT oben): Hexkraft/NeuroWeaving
        # stehen fix, kein Fertigkeitsslot mehr — das Frontend braucht die
        # Zahlen, um den Sockel anzuzeigen und den Profi-Bonus anzubieten.
        "magieFixwert": MAGIE_FIXWERT,
        "magieFixwertProfiBonus": MAGIE_FIXWERT_PROFI_BONUS,
    }


def normalisiere_weg(weg: str) -> tuple[str, str]:
    """Häretiker ist kein eigener Weg (siehe WEGE oben) — nur ein anderes
    Vokabular für denselben Magier-Weg. Gibt (weg, magieFlavor) zurück:
    der erste Wert ist das, was `KATEGORIEN_JE_WEG`/`pruefe`/`endwerte`
    kennen, der zweite bestimmt nur die Anzeige (siehe traits/seed.py::
    HAERETIKER_LABELS). So bleibt die gesamte Magie-Mechanik (hier, in
    bogen.py, items/routes.py, ki/routes.py) auf einer einzigen Quelle.
    """
    if weg == "HAERETIKER":
        return "MAGIER", "HAERETIKER"
    return weg, "MAGIER"


def freebee_kosten(auswahl: dict[str, Any], kategorie_von: dict[str, str]) -> int:
    """Was die eingereichte Erstellung an Freebees verbraucht.

    `kategorie_von` bildet Wertnamen auf ihre Kategorie ab (aus dem Katalog),
    denn der Preis hängt daran: ein Attributpunkt kostet 5, ein
    Fertigkeitspunkt 2, ein Hintergrundpunkt 1.
    """
    summe = 0
    for name, punkte in (auswahl.get("freebeePunkte") or {}).items():
        kategorie = kategorie_von.get(name)
        summe += FREEBEE_KOSTEN_JE_KATEGORIE.get(kategorie or "", 0) * max(0, int(punkte))
    summe += FREEBEE_KOSTEN_WILLENSKRAFT * max(0, int(auswahl.get("freebeeWillenskraft") or 0))
    summe += FREEBEE_KOSTEN_KREDIT * max(0, int(auswahl.get("freebeeKredit") or 0))
    summe += FREEBEE_KOSTEN_EIGENKAPITAL * max(0, int(auswahl.get("freebeeEigenkapital") or 0))
    # Zusatzfertigkeiten: nur der Freebee-Aufschlag kostet (2 je Punkt),
    # die Paketpunkte aus dem Fertigkeiten-Schritt sind schon durch das
    # Fertigkeitspaket abgegolten — analog zu einer normalen Fertigkeit.
    summe += FREEBEE_KOSTEN_JE_KATEGORIE["Fertigkeit"] * sum(
        1 for p in (auswahl.get("zusatzfertigkeitFreebees") or {}).values() if int(p) > 0
    )
    return summe


def pruefe(
    auswahl: dict[str, Any],
    katalog: list[dict],
    rassen: dict[str, dict[str, Any]] | None = None,
    einstellungen: dict[str, Any] | None = None,
    hintergrund_pool: list[dict[str, str]] | None = None,
) -> list[str]:
    """Prüft eine eingereichte Erstellung. Leere Liste = in Ordnung.

    Gibt alle Verstöße auf einmal zurück statt beim ersten abzubrechen —
    wer sich verzählt hat, will nicht nach jeder Korrektur den nächsten
    Einzelfehler vorgesetzt bekommen.

    `hintergrund_pool`: wie bei `regelwerk()` — der tatsächliche Katalog
    dieser Kampagne. Ohne Angabe fällt die Bekanntheitsprüfung auf die alte
    fest verdrahtete Liste zurück.
    """
    fehler: list[str] = []
    einstellungen = einstellungen or {}
    kategorie_von = {t["name"]: t["category"] for t in katalog}

    weg = auswahl.get("weg") or "KEINER"
    if weg not in KATEGORIEN_JE_WEG:
        fehler.append(f"Unbekannter Weg: {weg}")

    verfuegbar = rassen or RASSEN
    rasse = auswahl.get("rasse") or ""
    if rasse not in verfuegbar:
        fehler.append(f"Unbekannte Rasse: {rasse}")
        return fehler  # ohne Rasse lässt sich nichts weiter prüfen

    # --- Attribute: Kontingente und Verteilung --------------------------
    kontingente = auswahl.get("schwerpunkte") or {}
    vergeben = sorted((int(kontingente.get(k, 0)) for k in ATTRIBUT_KATEGORIEN), reverse=True)
    erwartet = sorted(verfuegbar[rasse]["freiePunkte"], reverse=True)
    if vergeben != erwartet:
        fehler.append(
            f"{rasse} verteilt {'/'.join(map(str, erwartet))} Attributpunkte, "
            f"eingereicht wurde {'/'.join(map(str, vergeben))}."
        )

    punkte = auswahl.get("attributPunkte") or {}
    maxima = startmaxima(rasse, verfuegbar)
    start = startwerte(rasse, verfuegbar)
    for kategorie in ATTRIBUT_KATEGORIEN:
        namen = ATTRIBUTE_JE_KATEGORIE[kategorie]
        summe = sum(max(0, int(punkte.get(n, 0))) for n in namen)
        soll = int(kontingente.get(kategorie, 0))
        if summe != soll:
            fehler.append(
                f"{KATEGORIE_NAMEN[kategorie]}: {summe} von {soll} Punkten verteilt."
            )
        for n in namen:
            wert = start[n] + max(0, int(punkte.get(n, 0)))
            if wert > maxima[n]:
                fehler.append(f"{n} steht auf {wert}, erlaubt sind bei der Erstellung {maxima[n]}.")

    # --- Fertigkeiten: Paketverteilung ----------------------------------
    paket_id = auswahl.get("fertigkeitsPaket") or ""
    paket = FERTIGKEITS_PAKETE.get(paket_id)
    if paket is None:
        fehler.append(f"Unbekanntes Fertigkeitspaket: {paket_id}")
    else:
        gewaehlt = {n: int(w) for n, w in (auswahl.get("fertigkeitPunkte") or {}).items() if int(w) > 0}
        # Zusatzfertigkeiten (28.09.2026, Mark: Button → Auswahl → erscheinen
        # im Raster und bekommen dieselben Paketpunkte): ihre Paket-Werte
        # zählen in dieselbe Verteilung, sind aber keine TraitDef-Namen.
        zusatz_paket = {
            zid: int(w)
            for zid, w in (auswahl.get("zusatzfertigkeitPunkte") or {}).items()
            if int(w) > 0
        }
        ist: dict[int, int] = {}
        for wert in list(gewaehlt.values()) + list(zusatz_paket.values()):
            ist[wert] = ist.get(wert, 0) + 1
        if ist != paket["verteilung"]:
            beschreibe = lambda v: ", ".join(f"{a}× auf {w}" for w, a in sorted(v.items(), reverse=True)) or "nichts"
            fehler.append(
                f"Paket {paket['name']} verlangt {beschreibe(paket['verteilung'])} — "
                f"gewählt wurde {beschreibe(ist)}."
            )
        erlaubte = FERTIGKEITS_KATEGORIEN & (
            {"Fertigkeit"} | KATEGORIEN_JE_WEG.get(weg, set())
        )
        for name in gewaehlt:
            kategorie = kategorie_von.get(name)
            if kategorie is None:
                fehler.append(f"Unbekannte Fertigkeit: {name}")
            elif kategorie not in erlaubte:
                fehler.append(f"{name} steht diesem Weg nicht offen.")
            elif kategorie in MAGIE_WERT_JE_KATEGORIE:
                # Neu (27.09.2026): Hexkraft/NeuroWeavingWert sind kein frei
                # wählbarer Fertigkeitsslot mehr, sondern ein fixer Sockel
                # (siehe endwerte()). Über einen Fertigkeitsslot lässt sich
                # nur noch der Profi-Bonus dazukaufen — sonst nichts.
                if paket_id != "PROFI" or gewaehlt[name] != MAGIE_FIXWERT_PROFI_BONUS:
                    fehler.append(
                        f"{name} steht fix auf {MAGIE_FIXWERT}; nur mit dem Profi-Paket "
                        f"lässt sich per Fertigkeitsslot {MAGIE_FIXWERT_PROFI_BONUS} Punkt "
                        f"dazukaufen (macht {MAGIE_FIXWERT + MAGIE_FIXWERT_PROFI_BONUS})."
                    )

    # --- Hintergründe ----------------------------------------------------
    hintergruende = {n: int(w) for n, w in (auswahl.get("hintergrundPunkte") or {}).items() if int(w) > 0}
    bekannte = {h["name"] for h in (hintergrund_pool if hintergrund_pool is not None else HINTERGRUENDE)}
    for name, wert in hintergruende.items():
        if name not in bekannte:
            fehler.append(f"Unbekannter Hintergrund: {name}")
        if wert > HINTERGRUND_MAX:
            fehler.append(f"{name} steht auf {wert}, erlaubt sind {HINTERGRUND_MAX}.")
    if sum(hintergruende.values()) > HINTERGRUND_PUNKTE_GESAMT:
        fehler.append(
            f"{sum(hintergruende.values())} Hintergrundpunkte verteilt, "
            f"erlaubt sind {HINTERGRUND_PUNKTE_GESAMT}."
        )
    # Mechanik-Hintergründe lassen sich je Kampagne abschalten (siehe
    # hintergruende/seed.py::SYSTEM_HINTERGRUENDE) — eine deaktivierte Zeile
    # darf nicht über eine alte/manipulierte Anfrage trotzdem Punkte bekommen.
    if hintergruende.get("Mentor", 0) > 0 and not einstellungen.get("mentorAktiv", True):
        fehler.append("Mentor ist in dieser Kampagne deaktiviert.")
    if hintergruende.get("Kontakte", 0) > 0 and not einstellungen.get("kontakteAktiv", True):
        fehler.append("Kontakte ist in dieser Kampagne deaktiviert.")

    # --- Freebees --------------------------------------------------------
    for name, zusatz in (auswahl.get("freebeePunkte") or {}).items():
        kategorie = kategorie_von.get(name)
        if kategorie is None and name not in bekannte:
            fehler.append(f"Freebees auf einen unbekannten Wert: {name}")
        if kategorie in {"Fertigkeit", "Sphäre"} and int(zusatz) > FREEBEE_MAX_JE_FERTIGKEIT:
            fehler.append(
                f"{name}: Freebees heben eine Fertigkeit um höchstens "
                f"{FREEBEE_MAX_JE_FERTIGKEIT} Punkt."
            )
    # Zusatzfertigkeiten: Paketpunkte unbegrenzt im Rahmen des Pakets
    # (Prüfung oben), Freebee-Aufschlag höchstens FREEBEE_MAX_JE_FERTIGKEIT.
    for zid, zusatz in (auswahl.get("zusatzfertigkeitFreebees") or {}).items():
        zusatz = int(zusatz)
        if zusatz < 0 or zusatz > FREEBEE_MAX_JE_FERTIGKEIT:
            fehler.append(
                f"Zusatzfertigkeit {zid}: Freebees heben höchstens um "
                f"{FREEBEE_MAX_JE_FERTIGKEIT} Punkt."
            )

    kosten = freebee_kosten(auswahl, kategorie_von)
    # Schulden-Mechanik abgeschaltet (siehe oben): Kredit-Freebee ist dann
    # tabu, unabhängig davon, ob er sich noch ausgeht.
    if int(auswahl.get("freebeeKredit") or 0) > 0 and not einstellungen.get("schuldenAktiv", True):
        fehler.append("Schulden (Kredit-Freebee) sind in dieser Kampagne deaktiviert.")
    # Rassen-Feature bonusFreebees (10.10.2026): budget-neutraler Bonus nur
    # für diese Rasse ("langweiliges Geld" beim Menschen) — erweitert das
    # Freebee-Limit, zählt aber NICHT in die 24er-Attribut-Bilanz mit rein.
    freebees_gesamt = FREEBEES_GESAMT + int(verfuegbar.get(rasse, {}).get("bonusFreebees", 0))
    if kosten > freebees_gesamt:
        fehler.append(f"{kosten} Freebees ausgegeben, zur Verfügung stehen {freebees_gesamt}.")

    # --- Endwerte gegen die Obergrenze des Wertes selbst -----------------
    # Zeile 24 hebt nur den **StartMax** für Freebees auf, nicht das Maximum
    # des Wertes: ein Attribut geht bis 6, eine Fertigkeit bis 6 (seit
    # 20.09.2026, vorher 5), Sphären bis 6 (seit 23.10.2026, vorher 5),
    # Hexkraft bis 10.
    # Ohne diese Prüfung liess sich Körperkraft auf 9 kaufen (von Mark gefunden).
    #
    # Bei Attributen, die die Rasse berührt, gilt **ihr** Deckel statt des
    # Katalogwerts (Mark, 11.09.2026): ein Zwerg kam sonst per Freebees auf
    # Charisma 6, obwohl sein Lebensmaximum 5 ist — und umgekehrt nie auf die
    # 7 bei Widerstandsfähigkeit, die ihm zusteht.
    maximum_von = {t["name"]: t["defaultMax"] for t in katalog}
    maximum_von.update(lebensmaxima(rasse, katalog, verfuegbar))
    for name, wert in endwerte(auswahl).items():
        grenze = maximum_von.get(name)
        if grenze is not None and wert > grenze:
            fehler.append(f"{name} käme auf {wert}, mehr als {grenze} geht nicht.")

    return fehler


def endwerte(auswahl: dict[str, Any], rassen: dict[str, dict[str, Any]] | None = None) -> dict[str, int]:
    """Die fertigen Werte: Startwert + verteilte Punkte + Freebees.

    Hintergründe sind hier mit drin — sie liegen im selben Katalog wie
    Attribute und Fertigkeiten, nur in eigener Kategorie.
    """
    rasse = auswahl.get("rasse") or ""
    werte = dict(startwerte(rasse, rassen))
    for name, punkte in (auswahl.get("attributPunkte") or {}).items():
        werte[name] = werte.get(name, 0) + max(0, int(punkte))
    for name, wert in (auswahl.get("fertigkeitPunkte") or {}).items():
        if int(wert) > 0:
            werte[name] = werte.get(name, 0) + int(wert)
    # Magiewert-Sockel (siehe MAGIE_FIXWERT oben): Hexkraft/NeuroWeaving
    # bekommen den festen Grundwert kostenlos, unabhängig davon, ob/was in
    # fertigkeitPunkte dafür stand — der darf laut pruefe() ohnehin nur noch
    # der Profi-Bonus sein, der hier einfach oben draufkommt.
    magie_trait = MAGIE_TRAIT_JE_WEG.get(auswahl.get("weg") or "")
    if magie_trait:
        bonus = max(0, int((auswahl.get("fertigkeitPunkte") or {}).get(magie_trait, 0)))
        werte[magie_trait] = MAGIE_FIXWERT + bonus
    for name, wert in (auswahl.get("hintergrundPunkte") or {}).items():
        if int(wert) > 0:
            werte[name] = werte.get(name, 0) + int(wert)
    for name, zusatz in (auswahl.get("freebeePunkte") or {}).items():
        if int(zusatz) > 0:
            werte[name] = werte.get(name, 0) + int(zusatz)
    return werte


def wende_gratis_fertigkeit_an(
    werte: dict[str, int], rasse_daten: dict[str, Any], katalog: list[dict]
) -> dict[str, int]:
    """Rassen-Feature "gratisFertigkeitName" (10.10.2026, Zorak-Beispiel: +1
    Anführen) — additiv auf eine NORMALE Fertigkeit aus dem Katalog, egal was
    der Spieler dort selbst verteilt hat. Gedeckelt auf das Katalogmaximum
    (Fertigkeiten haben anders als Attribute keinen Rassenmodifikator).

    Eigene, reine Funktion statt Inline-Code in der Route — testbar ohne
    HTTP-Request/Datenbank, derselbe Grund wie bei `endwerte()`/`pruefe()`.
    """
    name = rasse_daten.get("gratisFertigkeitName") or ""
    bonus = int(rasse_daten.get("gratisFertigkeitBonus") or 0)
    if not name or not bonus:
        return werte
    maximum = next((t["defaultMax"] for t in katalog if t["name"] == name), None)
    neu = dict(werte)
    neuer_wert = neu.get(name, 0) + bonus
    neu[name] = min(neuer_wert, maximum) if maximum is not None else neuer_wert
    return neu


def kapital(auswahl: dict[str, Any]) -> tuple[int, int]:
    """Vermögen und Schulden nach der Erstellung.

    Zeile 42: Kredit und Eigenkapital bringen beide 10.000¥ je Freebee-Kauf,
    aber Kredit kostet nur einen Freebee statt zwei — weil er zurückzuzahlen
    ist. Er wird deshalb zugleich als Schuld vermerkt.
    """
    kredit = max(0, int(auswahl.get("freebeeKredit") or 0)) * KAPITAL_JE_FREEBEE
    eigen = max(0, int(auswahl.get("freebeeEigenkapital") or 0)) * KAPITAL_JE_FREEBEE
    return STARTKAPITAL + kredit + eigen, kredit


def _int_dict(roh: Any) -> dict[str, int]:
    if not isinstance(roh, dict):
        return {}
    out: dict[str, int] = {}
    for schluessel, wert in roh.items():
        try:
            out[str(schluessel)] = int(wert)
        except (TypeError, ValueError):
            continue
    return out


def _punkte_map(roh: Any) -> dict[str, int]:
    """Dict {name: n} oder KI-Liste [{name, punkte|rating}]."""
    if isinstance(roh, dict):
        return _int_dict(roh)
    if not isinstance(roh, list):
        return {}
    out: dict[str, int] = {}
    for eintrag in roh:
        if not isinstance(eintrag, dict):
            continue
        name = (eintrag.get("name") or "").strip()
        if not name:
            continue
        roh_wert = eintrag.get("punkte", eintrag.get("rating"))
        if roh_wert is None:
            continue
        try:
            out[name] = int(roh_wert)
        except (TypeError, ValueError):
            continue
    return out


def auswahl_aus_ki(daten: dict[str, Any]) -> dict[str, Any]:
    """KI-JSON → Erstellungsformular. Das alte `traits: [{name, rating}]` fällt weg."""
    weg, _flavor = normalisiere_weg((daten.get("weg") or "KEINER"))
    return {
        "weg": weg,
        "rasse": (daten.get("rasse") or "").strip(),
        "schwerpunkte": _int_dict(daten.get("schwerpunkte")),
        "attributPunkte": _punkte_map(daten.get("attributPunkte")),
        "fertigkeitsPaket": daten.get("fertigkeitsPaket") or "",
        "fertigkeitPunkte": _punkte_map(daten.get("fertigkeitPunkte")),
        "hintergrundPunkte": _punkte_map(daten.get("hintergrundPunkte")),
        "freebeePunkte": _punkte_map(daten.get("freebeePunkte")),
        "zusatzfertigkeitPunkte": _int_dict(daten.get("zusatzfertigkeitPunkte")),
        "zusatzfertigkeitFreebees": _int_dict(daten.get("zusatzfertigkeitFreebees")),
        "freebeeWillenskraft": int(daten.get("freebeeWillenskraft") or 0),
        "freebeeKredit": int(daten.get("freebeeKredit") or 0),
        "freebeeEigenkapital": int(daten.get("freebeeEigenkapital") or 0),
    }


def _attribute_als_endwerte(
    auswahl: dict[str, Any], rassen: dict[str, dict[str, Any]] | None
) -> dict[str, Any] | None:
    """Häufiger KI-Fehler: attributPunkte sind Endwerte, nicht Zusatzpunkte.

    Nur als zweiter Versuch. Wird verworfen, wenn die Umrechnung die
    Prüfung nicht besteht — eine legale Zusatzpunkt-Einreichung darf hier
    nicht still umgeschrieben werden.
    """
    start = startwerte(auswahl.get("rasse") or "", rassen)
    punkte = dict(auswahl.get("attributPunkte") or {})
    if not punkte or not start:
        return None
    umgerechnet: dict[str, int] = {}
    geaendert = False
    for name, wert in punkte.items():
        basis = start.get(name)
        if basis is None or wert < basis:
            umgerechnet[name] = wert
            continue
        zusatz = wert - basis
        umgerechnet[name] = zusatz
        if zusatz != wert:
            geaendert = True
    if not geaendert:
        return None
    return {**auswahl, "attributPunkte": umgerechnet}


def aus_ki_antwort(
    daten: dict[str, Any],
    katalog: list[dict],
    rassen: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, int], list[str]]:
    """KI-JSON als Erstellung prüfen. Bei Verstoß: keine Werte, nur Fehler.

    Roh-Trait-Ratings (der alte ✨-Pfad) werden bewusst ignoriert — die KI
    muss dasselbe Formular füllen wie ein Spieler. Schickt sie trotzdem
    Endwerte in attributPunkte, wird einmal umgerechnet und erneut geprüft.
    """
    auswahl = auswahl_aus_ki(daten)
    fehler = pruefe(auswahl, katalog, rassen)
    if not fehler:
        return endwerte(auswahl, rassen), []
    umgerechnet = _attribute_als_endwerte(auswahl, rassen)
    if umgerechnet is not None and not pruefe(umgerechnet, katalog, rassen):
        return endwerte(umgerechnet, rassen), []
    return {}, fehler


def ki_erstellungsregeln_text(rassen: dict[str, dict[str, Any]] | None = None) -> str:
    """Auftrag: dasselbe Formular wie ein Spieler, keine Katalog-6er."""
    verfuegbar = rassen or RASSEN
    rassen_zeilen = []
    for name, daten in verfuegbar.items():
        mods = daten.get("modifikatoren") or {}
        mod_text = ", ".join(f"{attr} {wert:+d}" for attr, wert in mods.items()) or "keine"
        frei = "/".join(str(n) for n in daten.get("freiePunkte") or [])
        budget = FREEBEES_GESAMT + int(daten.get("bonusFreebees") or 0)
        rassen_zeilen.append(
            f"{name}: Kontingente {frei}, Mods {mod_text}, Freebee-Budget {budget}"
        )
    pakete = []
    for kennung, paket in FERTIGKEITS_PAKETE.items():
        verteilt = ", ".join(
            f"{anzahl}× auf {wert}" for wert, anzahl in sorted(paket["verteilung"].items(), reverse=True)
        )
        pakete.append(f"{kennung}: {verteilt}")
    hintergruende = ", ".join(h["name"] for h in HINTERGRUENDE)
    return (
        "Du füllst dasselbe Erstellungsformular wie ein Spieler, in dieser Reihenfolge: "
        "rasse, weg, Attribute nach Rassenkontingent, genau ein Fertigkeitspaket, "
        "Hintergründe, dann Freebees in Geld und Details. "
        "Keine traits-Liste, keine End-Ratings, die max-Zahlen im Katalog sind Lebensmaxima "
        "und nicht die Erstellung. "
        f"rasse genau eine von: {'; '.join(rassen_zeilen)}. "
        "schwerpunkte: die drei Kontingente dieser Rasse auf AttributKörperlich, "
        "AttributGesellschaftlich und AttributGeistig — dieselben drei Zahlen, jede einmal. "
        "attributPunkte: NUR Zusatzpunkte auf den Startwert (1 + Mod), höchstens 3 je Attribut, "
        "Summe je Spalte = das Kontingent dieser Spalte. StartMax = 4 + Mod. "
        "Nicht den Endwert schicken: Mensch Körperkraft 3 Zusatzpunkte ergibt Endwert 4. "
        f"fertigkeitsPaket genau eines von: {'; '.join(pakete)}. "
        "fertigkeitPunkte: Liste {name, punkte} mit Katalog-Namen, exakt diese Verteilung, "
        "keine zusätzlichen Fertigkeiten. "
        "Hexkraft und Sphären nur bei weg MAGIER oder HAERETIKER, NeuroWeaving nur bei NEUROWEAVER. "
        f"Hexkraft und NeuroWeaving stehen fix auf {MAGIE_FIXWERT}; nur PROFI darf "
        f"{MAGIE_FIXWERT_PROFI_BONUS} Punkt darauf legen. "
        f"hintergrundPunkte: eigener Pool, höchstens {HINTERGRUND_PUNKTE_GESAMT} insgesamt, "
        f"höchstens {HINTERGRUND_MAX} auf einen, Namen nur aus: {hintergruende}. "
        "Freebees sind an das Budget der Rasse gebunden und werden ausgegeben, nicht liegengelassen. "
        f"Kosten: Attribut/Hexkraft/NeuroWeaving {FREEBEE_KOSTEN_JE_KATEGORIE['Hexkraft']} je Punkt "
        "(darf StartMax übersteigen, nicht das Lebensmaximum), "
        f"Fertigkeit/Sphäre {FREEBEE_KOSTEN_JE_KATEGORIE['Fertigkeit']} und höchstens "
        f"+{FREEBEE_MAX_JE_FERTIGKEIT}, Willenskraft {FREEBEE_KOSTEN_WILLENSKRAFT}, "
        f"Kredit {FREEBEE_KOSTEN_KREDIT} je {KAPITAL_JE_FREEBEE}¥, "
        f"Eigenkapital {FREEBEE_KOSTEN_EIGENKAPITAL} je {KAPITAL_JE_FREEBEE}¥. "
        "freebeePunkte sind Zusatzpunkte, nicht Endwerte. "
        "freebeeKredit und freebeeEigenkapital sind die Anzahl der Käufe, nicht Yen. "
        "Einen Teil der Freebees als Geld (Kredit oder Eigenkapital), den Rest als wenige "
        "passende Details (eine Fertigkeit +1, Willenskraft, höchstens ein Attribut). "
        "Nicht jedes Attribut anheben."
    )


# --- Stufenweise KI-Erstellung (13.10.2026, Marks Wunsch) ----------------
#
# Der Ablauf oben (`ki_erstellungsregeln_text` + `aus_ki_antwort`) verlangt
# von der KI, in einem einzigen JSON ALLE Zahlen selbst korrekt auszurechnen
# (Kontingente, Paketverteilung, Freebee-Budget) — reine Arithmetik, die
# Sprachmodelle zuverlässig falsch machen (Mark-Beispiel 13.10.2026: eigene
# schwerpunkte und die Summe der eigenen attributPunkte widersprachen sich
# im selben Response). Bleibt das nach einem Nachbesser-Versuch falsch, sah
# die SL nur einen 422 "KI hat sich nicht an die Regeln gehalten".
#
# Die Funktionen hier kehren das um: die KI liefert nur noch Namen und
# Prioritäten (welche Rasse, welches Attribut ist wichtiger, welche
# Fertigkeit zuerst, welche Freebee-Wünsche in welcher Reihenfolge) — nie
# eine Summe, nie eine exakte Verteilung. Die tatsächlichen Zahlen baut der
# Server aus den festen Spielregeln zusammen. Das Ergebnis ist dadurch
# IMMER strukturell regelkonform, unabhängig davon, ob/wie gut die KI
# rechnen kann — sie hat schlicht keine Stelle mehr, an der sie eine Zahl
# falsch hinschreiben könnte. Siehe app/ki/routes.py für den Aufruf-Ablauf
# (zwei kleine KI-Anfragen statt einer großen).

# Jedes Attribut lässt sich bei der Erstellung um höchstens diesen Betrag
# anheben — rassenunabhängig, weil StartMax und Startwert beide um denselben
# Rassenmodifikator verschoben werden und sich die Differenz daher aufhebt
# (siehe ATTRIBUT_STARTMAX-Kommentar oben).
ATTRIBUT_PUNKTE_MAX_JE_WERT = ATTRIBUT_STARTMAX - ATTRIBUT_GRUNDWERT

# Feste Verteilkurven für das Hintergrund-Budget (Standard 5 Punkte) nach
# Anzahl der von der KI gewählten Hintergründe — absteigend, erster Pick
# bekommt am meisten. Ab 5 gewählten Namen reicht es nur noch für 1 Punkt
# je Name (siehe Fallback in hintergrundpunkte_aus_rangfolge).
_HINTERGRUND_VERTEILUNG: dict[int, list[int]] = {1: [5], 2: [3, 2], 3: [2, 2, 1], 4: [2, 1, 1, 1]}


def schwerpunkte_aus_rangfolge(
    rasse: str, rangfolge: list[str], rassen: dict[str, dict[str, Any]] | None = None
) -> dict[str, int]:
    """Weist die festen Attribut-Kontingente einer Rasse (z.B. Mensch 7/5/3)
    den drei Kategorien zu — nach der Prioritätsreihenfolge der KI, nicht
    nach von ihr selbst erfundenen Zahlen. Liefert IMMER eine vollständige,
    gültige Zuordnung: eine unvollständige oder fehlerhafte Reihenfolge wird
    aufgefüllt, nie verworfen.
    """
    verfuegbar = rassen or RASSEN
    kontingente = sorted(verfuegbar.get(rasse, {}).get("freiePunkte") or [0, 0, 0], reverse=True)
    bereinigt = [k for k in dict.fromkeys(rangfolge or []) if k in ATTRIBUT_KATEGORIEN]
    for k in ATTRIBUT_KATEGORIEN:
        if k not in bereinigt:
            bereinigt.append(k)
    return {kategorie: punkte for kategorie, punkte in zip(bereinigt, kontingente)}


def attributpunkte_aus_rangfolge(kategorie: str, rangfolge: list[str], kontingent: int) -> dict[str, int]:
    """Verteilt das Kontingent einer Attributkategorie nach Prioritätsreihenfolge.

    Die KI sagt nur, welches Attribut ihr für die Figur wichtiger ist — der
    Server füllt von oben nach unten auf, gedeckelt bei
    ATTRIBUT_PUNKTE_MAX_JE_WERT. Das Ergebnis trifft das Kontingent dadurch
    immer exakt, ganz ohne dass die KI selbst addieren müsste.
    """
    namen = ATTRIBUTE_JE_KATEGORIE[kategorie]
    bereinigt = [n for n in dict.fromkeys(rangfolge or []) if n in namen]
    for n in namen:
        if n not in bereinigt:
            bereinigt.append(n)
    rest = max(0, int(kontingent))
    ergebnis = {n: 0 for n in namen}
    for name in bereinigt:
        vergeben = min(rest, ATTRIBUT_PUNKTE_MAX_JE_WERT)
        ergebnis[name] = vergeben
        rest -= vergeben
    return ergebnis


def fertigkeitpunkte_aus_rangfolge(
    paket_id: str,
    rangfolge: list[str],
    erlaubte_namen: list[str],
    magie_bonus: bool = False,
    magie_trait: str | None = None,
) -> dict[str, int]:
    """Verteilt die festen Paketwerte (Profi z.B. 4/3/3/3/2/2/2/1) nach der
    von der KI gewünschten Namensreihenfolge — die exakte Verteilung stimmt
    dadurch IMMER, die KI entscheidet nur noch, wer welchen Platz bekommt.

    `magie_bonus` verbraucht (nur bei PROFI, mit gesetztem `magie_trait`)
    einen der 1er-Plätze für den Magie-Sockel-Bonus statt für eine normale
    Fertigkeit — dasselbe Konzept wie der bisherige manuelle Profi-Bonus.
    """
    paket = FERTIGKEITS_PAKETE.get(paket_id)
    if paket is None:
        return {}
    werte: list[int] = []
    for wert, anzahl in sorted(paket["verteilung"].items(), reverse=True):
        werte.extend([wert] * anzahl)

    ergebnis: dict[str, int] = {}
    if magie_bonus and paket_id == "PROFI" and magie_trait and MAGIE_FIXWERT_PROFI_BONUS in werte:
        werte.remove(MAGIE_FIXWERT_PROFI_BONUS)
        ergebnis[magie_trait] = MAGIE_FIXWERT_PROFI_BONUS

    bereinigt = [n for n in dict.fromkeys(rangfolge or []) if n in erlaubte_namen]
    for n in erlaubte_namen:
        if len(bereinigt) >= len(werte):
            break
        if n not in bereinigt:
            bereinigt.append(n)

    for name, wert in zip(bereinigt, werte):
        ergebnis[name] = wert
    return ergebnis


def hintergrundpunkte_aus_rangfolge(
    rangfolge: list[str],
    pool_namen: set[str] | list[str],
    gesamt: int = HINTERGRUND_PUNKTE_GESAMT,
    max_je: int = HINTERGRUND_MAX,
) -> dict[str, int]:
    """Verteilt das feste Hintergrund-Budget auf die priorisierten Namen der
    KI — keine Summen-Arithmetik mehr nötig, nur Auswahl und Reihenfolge.
    Unbekannte Namen werden stillschweigend übersprungen statt abgelehnt.
    """
    pool = set(pool_namen)
    bereinigt = [n for n in dict.fromkeys(rangfolge or []) if n in pool]
    if not bereinigt:
        return {}
    verteilung = _HINTERGRUND_VERTEILUNG.get(len(bereinigt), [1] * len(bereinigt))
    ergebnis: dict[str, int] = {}
    rest = gesamt
    for name, wert in zip(bereinigt, verteilung):
        wert = min(wert, max_je, rest)
        if wert <= 0:
            break
        ergebnis[name] = wert
        rest -= wert
    return ergebnis


def freebees_aus_wunsch(
    budget: int,
    kredit_wunsch: int,
    eigenkapital_wunsch: int,
    ziel_rangfolge: list[str],
    kategorie_von: dict[str, str],
    hintergrund_namen: set[str],
    aktuelle_werte: dict[str, int],
    maximum_von: dict[str, int],
    mindest_geld: bool = True,
) -> dict[str, Any]:
    """Finanziert die Freebee-Wünsche der KI strikt innerhalb des Budgets —
    Geld zuerst, dann die Zielliste in der gewünschten Reihenfolge, bis das
    Budget verbraucht ist. Reicht es nicht für alles, werden die hinteren
    Wünsche gestrichen statt die ganze Erstellung abzulehnen: die KI kann
    ihr Budget dadurch gar nicht mehr überziehen. Jedes Ziel wird außerdem
    auf `maximum_von` gedeckelt — das Ergebnis übersteigt nie das
    Lebensmaximum eines Wertes, selbst wenn die KI das Budget dafür hätte.

    `mindest_geld`: mindestens 1 Kredit-Kauf, falls die KI gar kein Geld
    wünscht und noch Budget übrig ist (bisher ein eigener Fehler/
    Nachbesser-Versuch, jetzt ein stiller Server-Default).
    """
    rest = max(0, int(budget))
    kredit = max(0, int(kredit_wunsch))
    eigen = max(0, int(eigenkapital_wunsch))

    while kredit and kredit * FREEBEE_KOSTEN_KREDIT > rest:
        kredit -= 1
    rest -= kredit * FREEBEE_KOSTEN_KREDIT
    while eigen and eigen * FREEBEE_KOSTEN_EIGENKAPITAL > rest:
        eigen -= 1
    rest -= eigen * FREEBEE_KOSTEN_EIGENKAPITAL

    if mindest_geld and kredit == 0 and eigen == 0 and rest >= FREEBEE_KOSTEN_KREDIT:
        kredit = 1
        rest -= FREEBEE_KOSTEN_KREDIT

    willenskraft = 0
    freebee_punkte: dict[str, int] = {}
    for ziel in dict.fromkeys(ziel_rangfolge or []):
        if ziel == "Willenskraft":
            if rest >= FREEBEE_KOSTEN_WILLENSKRAFT:
                willenskraft += 1
                rest -= FREEBEE_KOSTEN_WILLENSKRAFT
            continue
        if ziel in freebee_punkte:
            continue
        kategorie = kategorie_von.get(ziel)
        if kategorie is None and ziel not in hintergrund_namen:
            continue  # unbekannter Name: überspringen statt ablehnen
        kosten_je_punkt = FREEBEE_KOSTEN_JE_KATEGORIE.get(kategorie or HINTERGRUND_KATEGORIE, 0)
        if kosten_je_punkt <= 0:
            continue
        obergrenze = FREEBEE_MAX_JE_FERTIGKEIT if kategorie in {"Fertigkeit", "Sphäre"} else 99
        frei_bis_maximum = maximum_von.get(ziel)
        if frei_bis_maximum is not None:
            obergrenze = min(obergrenze, max(0, frei_bis_maximum - aktuelle_werte.get(ziel, 0)))
        punkte = 0
        while punkte < obergrenze and rest >= kosten_je_punkt:
            punkte += 1
            rest -= kosten_je_punkt
        if punkte:
            freebee_punkte[ziel] = punkte

    return {
        "freebeePunkte": freebee_punkte,
        "freebeeWillenskraft": willenskraft,
        "freebeeKredit": kredit,
        "freebeeEigenkapital": eigen,
    }


def ki_konzept_text(
    rassen: dict[str, dict[str, Any]] | None = None,
    archetypen: list[str] | None = None,
) -> str:
    """Anleitung für Stufe 1 der KI-Charaktererstellung: Konzept, Rasse, Weg,
    Fertigkeitspaket und Attribut-Prioritäten — bewusst OHNE eine einzige
    Zahl, die die KI selbst berechnen müsste. Die tatsächlichen Kontingente
    baut der Server aus den hier gelieferten Prioritäten zusammen, siehe
    schwerpunkte_aus_rangfolge/attributpunkte_aus_rangfolge oben.
    """
    verfuegbar = rassen or RASSEN
    rassen_zeilen = []
    for name, daten in verfuegbar.items():
        mods = daten.get("modifikatoren") or {}
        mod_text = ", ".join(f"{attr} {wert:+d}" for attr, wert in mods.items()) or "keine Besonderheiten"
        rassen_zeilen.append(f"{name} ({mod_text})")
    wege_zeilen = [f"{w['id']} ({w['name']})" for w in WEGE]
    pakete_zeilen = [
        f"{kennung} ({paket['name']}, {sum(paket['verteilung'].values())} Fertigkeiten)"
        for kennung, paket in FERTIGKEITS_PAKETE.items()
    ]
    if archetypen:
        archetyp_satz = (
            "ambition und verlangen: je genau einer dieser Archetyp-Namen, exakt "
            "so geschrieben, zwei verschiedene, nie eigener Text: "
            + ", ".join(archetypen)
            + ". "
        )
    else:
        archetyp_satz = (
            "ambition und verlangen leer lassen — ohne Vorlagen ist eigener Text verboten. "
        )
    return (
        "Das ist Stufe 1 von 2 der Charaktererstellung. Schreib den Konzept-Text, "
        "wähle Rasse, Weg und Fertigkeitspaket, und sag danach nur noch, WELCHE "
        "Attributkategorie und welches einzelne Attribut der Figur am wichtigsten "
        "ist — keine Zahlen, keine Summen, die Verteilung übernimmt der Server "
        "automatisch nach den festen Regeln. "
        + archetyp_satz
        + (
            f"rasse: genau eine von {', '.join(rassen_zeilen)}. "
            f"weg: genau eine von {', '.join(wege_zeilen)} — MAGIER für klassische Zauberer, "
            "HAERETIKER für dieselbe Magie mit Glaubens-Flavor (Priester/Inquisitor), "
            "NEUROWEAVER nur, wenn die Figur NeuroWeaving nutzt, sonst KEINER. "
            f"fertigkeitsPaket: genau eine von {', '.join(pakete_zeilen)}. "
            "kategorienReihenfolge: die drei Kategorien AttributKörperlich, "
            "AttributGesellschaftlich, AttributGeistig — wichtigste zuerst. Diese "
            "Kategorie bekommt automatisch das größte Attribut-Kontingent der Rasse. "
            "attributReihenfolgeKoerperlich/Gesellschaftlich/Geistig: innerhalb jeder "
            "Kategorie die drei zugehörigen Attribute nach Wichtigkeit für die Figur "
            "sortiert, wichtigstes zuerst — der Server verteilt die Punkte danach."
        )
    )
