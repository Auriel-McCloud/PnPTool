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
3. Fertigkeiten kommen aus einem von drei Paketen (Zeilen 28-30). Arete,
   Sphären und NeuroWeaving zählen dabei als Fertigkeit (Zeile 27).
4. 15 Freebees zum Nachbessern (Zeilen 37-42).

Freebees dürfen über den **StartMax** der Rasse hinaus (Zeile 24), aber nicht
über das Maximum des Wertes selbst — ein Attribut endet bei 6, eine Fertigkeit
bei 5. Das steht so nicht im Excel, ergibt sich aber daraus, dass die Maxima
für den ganzen Charakterbogen gelten und nicht nur für die Erstellung.

**Noch nicht aus dem Regelwerk belegt** (Mark klärt das beim Feinschliff):
Hintergründe kommen im Excel nicht vor — die Liste unten ist ein Vorschlag
fürs Setting. Ebenso der Freebee-Preis von 1 je Hintergrundpunkt; vorgegeben
war nur Marks "bis zu 5 Punkte". Und ob Sphären beim Freebee-Kauf wie
Fertigkeiten zählen (2) oder wie Arete (5) — Zeile 39 nennt nur
"Attribut / Arete NeuroWeaving 5", Zeile 27 stellt Sphären aber zu den
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
    },
    "Elf": {
        "modifikatoren": {"Charisma": 1, "Geschicklichkeit": 1, "Widerstandsfähigkeit": -1},
        "freiePunkte": [5, 5, 3],
        "beschreibung": "Gewandt und einnehmend, körperlich aber nicht sonderlich zäh.",
    },
    "Ork": {
        "modifikatoren": {"Körperkraft": 1, "Intelligenz": -1},
        "freiePunkte": [6, 5, 3],
        "beschreibung": "Kräftig gebaut, und nach dem Menschen am breitesten aufgestellt.",
    },
    "Zwerg": {
        "modifikatoren": {"Widerstandsfähigkeit": 1, "Fassung": 1, "Charisma": -1},
        "freiePunkte": [5, 5, 3],
        "beschreibung": "Hält aus und behält die Ruhe; Sympathien gewinnt er weniger leicht.",
    },
    "Troll": {
        "modifikatoren": {
            "Körperkraft": 2,
            "Widerstandsfähigkeit": 1,
            "Geistesschärfe": -1,
            "Geschicklichkeit": -1,
        },
        "freiePunkte": [5, 4, 3],
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
        "name": "Weg des Chrom",
        "beschreibung": "Kein Zauber, kein Weben — Chrom. Ob du es im Körper trägst oder in der "
        "Hand: du bist nicht geboren worden, du wurdest gebaut, Stück für Stück. Wo andere nach "
        "Sphären greifen, greifst du zum Werkzeug. Und niemand kann dich über die Matrix von "
        "innen angreifen.",
    },
    {
        "id": "MAGIER",
        "name": "Magier",
        "beschreibung": "Arete und die neun Sphären. Die Sphären beschreiben, woran deine Magie "
        "greift und wie groß es sein darf; gewürfelt wird Arete.",
    },
    {
        "id": "TECHNOMANCER",
        "name": "NeuroWeaver",
        "beschreibung": "NeuroWeaving statt Magie: die Matrix ohne Gerät. Deine I.C.E. trägst du "
        "in dir (Fassung + Geistesschärfe), NeuroWeaving-Fertigkeiten geben Bonuswürfel.",
    },
]

# Auf dem Blatt steht "Arete != NeuroWeaving" — beides zugleich gibt es nicht.
KATEGORIEN_JE_WEG = {
    "KEINER": set(),
    "MAGIER": {"Arete", "Sphäre"},
    "TECHNOMANCER": {"NeuroWeaving"},
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
# "Arete, Sphären, bzw. NeuroWeaving zählen als Fähigkeit".
FERTIGKEITS_KATEGORIEN = {"Fertigkeit", "Arete", "Sphäre", "NeuroWeaving"}

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
    "Arete": 5,
    "NeuroWeaving": 5,
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


def startwerte(rasse: str) -> dict[str, int]:
    """Attributwerte vor der Verteilung: Grundwert plus Rassenmodifikator."""
    mods = RASSEN.get(rasse, {}).get("modifikatoren", {})
    werte = {}
    for attribute in ATTRIBUTE_JE_KATEGORIE.values():
        for name in attribute:
            werte[name] = ATTRIBUT_GRUNDWERT + mods.get(name, 0)
    return werte


def startmaxima(rasse: str) -> dict[str, int]:
    """Obergrenzen bei der Erstellung. Freebees dürfen darüber (Zeile 24)."""
    mods = RASSEN.get(rasse, {}).get("modifikatoren", {})
    maxima = {}
    for attribute in ATTRIBUTE_JE_KATEGORIE.values():
        for name in attribute:
            maxima[name] = ATTRIBUT_STARTMAX + mods.get(name, 0)
    return maxima


def regelwerk() -> dict[str, Any]:
    """Alles, was die Oberfläche zum Führen durch die Erstellung braucht."""
    return {
        "wege": WEGE,
        "rassen": [
            {
                "name": name,
                "modifikatoren": daten["modifikatoren"],
                "freiePunkte": daten["freiePunkte"],
                "beschreibung": daten["beschreibung"],
                "startwerte": startwerte(name),
                "startmaxima": startmaxima(name),
            }
            for name, daten in RASSEN.items()
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
        "hintergruende": HINTERGRUENDE,
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
        },
        "startkapital": STARTKAPITAL,
    }


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
    return summe


def pruefe(auswahl: dict[str, Any], katalog: list[dict]) -> list[str]:
    """Prüft eine eingereichte Erstellung. Leere Liste = in Ordnung.

    Gibt alle Verstöße auf einmal zurück statt beim ersten abzubrechen —
    wer sich verzählt hat, will nicht nach jeder Korrektur den nächsten
    Einzelfehler vorgesetzt bekommen.
    """
    fehler: list[str] = []
    kategorie_von = {t["name"]: t["category"] for t in katalog}

    weg = auswahl.get("weg") or "KEINER"
    if weg not in KATEGORIEN_JE_WEG:
        fehler.append(f"Unbekannter Weg: {weg}")

    rasse = auswahl.get("rasse") or ""
    if rasse not in RASSEN:
        fehler.append(f"Unbekannte Rasse: {rasse}")
        return fehler  # ohne Rasse lässt sich nichts weiter prüfen

    # --- Attribute: Kontingente und Verteilung --------------------------
    kontingente = auswahl.get("schwerpunkte") or {}
    vergeben = sorted((int(kontingente.get(k, 0)) for k in ATTRIBUT_KATEGORIEN), reverse=True)
    erwartet = sorted(RASSEN[rasse]["freiePunkte"], reverse=True)
    if vergeben != erwartet:
        fehler.append(
            f"{rasse} verteilt {'/'.join(map(str, erwartet))} Attributpunkte, "
            f"eingereicht wurde {'/'.join(map(str, vergeben))}."
        )

    punkte = auswahl.get("attributPunkte") or {}
    maxima = startmaxima(rasse)
    start = startwerte(rasse)
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
        ist: dict[int, int] = {}
        for wert in gewaehlt.values():
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

    # --- Hintergründe ----------------------------------------------------
    hintergruende = {n: int(w) for n, w in (auswahl.get("hintergrundPunkte") or {}).items() if int(w) > 0}
    bekannte = {h["name"] for h in HINTERGRUENDE}
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
    kosten = freebee_kosten(auswahl, kategorie_von)
    if kosten > FREEBEES_GESAMT:
        fehler.append(f"{kosten} Freebees ausgegeben, zur Verfügung stehen {FREEBEES_GESAMT}.")

    # --- Endwerte gegen die Obergrenze des Wertes selbst -----------------
    # Zeile 24 hebt nur den **StartMax** für Freebees auf, nicht das Maximum
    # des Wertes: ein Attribut geht bis 6, eine Fertigkeit bis 5, Arete bis 10.
    # Ohne diese Prüfung liess sich Körperkraft auf 9 kaufen (von Mark gefunden).
    maximum_von = {t["name"]: t["defaultMax"] for t in katalog}
    for name, wert in endwerte(auswahl).items():
        grenze = maximum_von.get(name)
        if grenze is not None and wert > grenze:
            fehler.append(f"{name} käme auf {wert}, mehr als {grenze} geht nicht.")

    return fehler


def endwerte(auswahl: dict[str, Any]) -> dict[str, int]:
    """Die fertigen Werte: Startwert + verteilte Punkte + Freebees.

    Hintergründe sind hier mit drin — sie liegen im selben Katalog wie
    Attribute und Fertigkeiten, nur in eigener Kategorie.
    """
    rasse = auswahl.get("rasse") or ""
    werte = dict(startwerte(rasse))
    for name, punkte in (auswahl.get("attributPunkte") or {}).items():
        werte[name] = werte.get(name, 0) + max(0, int(punkte))
    for name, wert in (auswahl.get("fertigkeitPunkte") or {}).items():
        if int(wert) > 0:
            werte[name] = werte.get(name, 0) + int(wert)
    for name, wert in (auswahl.get("hintergrundPunkte") or {}).items():
        if int(wert) > 0:
            werte[name] = werte.get(name, 0) + int(wert)
    for name, zusatz in (auswahl.get("freebeePunkte") or {}).items():
        if int(zusatz) > 0:
            werte[name] = werte.get(name, 0) + int(zusatz)
    return werte


def kapital(auswahl: dict[str, Any]) -> tuple[int, int]:
    """Vermögen und Schulden nach der Erstellung.

    Zeile 42: Kredit und Eigenkapital bringen beide 10.000¥ je Freebee-Kauf,
    aber Kredit kostet nur einen Freebee statt zwei — weil er zurückzuzahlen
    ist. Er wird deshalb zugleich als Schuld vermerkt.
    """
    kredit = max(0, int(auswahl.get("freebeeKredit") or 0)) * KAPITAL_JE_FREEBEE
    eigen = max(0, int(auswahl.get("freebeeEigenkapital") or 0)) * KAPITAL_JE_FREEBEE
    return STARTKAPITAL + kredit + eigen, kredit
