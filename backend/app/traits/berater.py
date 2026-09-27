"""Charaktererstellungs-Berater — Karl-Klammer-artige Live-Warnungen.

Mark, 27.09.2026: seit Hexkraft/NeuroWeaving ein fixer Sockel sind (siehe
erstellung.py::MAGIE_FIXWERT), kann ein Magier/NeuroWeaver seine GESAMTEN
Fertigkeitsslots trotzdem noch in Sphären/NeuroWeaving-Fertigkeiten stecken
und mit 0 in jeder Alltagsfertigkeit dastehen — ein Chrom-Charakter kann das
nicht, weil er keinen so dichten Alternativ-Pool hat. Statt das hart zu
verbieten ("wer soweit kommt hat's verdient", CLAUDE.md) gibt es einen
Assistenten, der bei offensichtlichen Lücken auf sie hinweist — SICHTBAR,
NIEMALS BLOCKIEREND (Mark: "nur anzeigen, nie blockieren").

27.09.2026, zweite Rückmeldung: die erste Fassung hatte 6 Warn-Codes und
brachte damit zu viele Popups — dazu fehlte ausgerechnet die eigentlich
gewünschte Sphären/Götter-Warnung, weil ihre Schwelle (10) zu hoch lag.
Auf Marks Wunsch reduziert auf GENAU DREI Warnungen, in fester Priorität
(wichtigstes zuerst, siehe `_PRIORITAET` und die Sortierung am Ende von
`berate()`): 1. Magie-Überladung (>6 Punkte Sphären/Götter/NeuroWeaving),
2. keine Wahrnehmung, 3. kein Kampfwert. Sozial/Wissen/schiefe Attribute
sind bewusst raus ("bin mir nichtmal sicher ob ich die überhaupt drinnen
haben will").

Bewusst ohne KI-Aufruf: das hier sind Reaktionen auf klar messbare Zahlen
(Wert X = 0, Kategorie Y unausgeglichen), keine kreative Textarbeit. Läuft
rein lokal bei jedem Klick, kostet nichts, hängt nicht an einem externen
API-Status. Die *Sprüche* sind fest formuliert (kein Sprachmodell) — der
Witz kommt aus der Textwahl, nicht aus KI-Generierung.
"""

from typing import Any

# Fertigkeiten-Gruppierung NUR für diese Warnlogik — ändert nichts an der
# Katalog-Kategorie "Fertigkeit" selbst (siehe traits/seed.py). Mark,
# 27.09.2026, per Rückfrage bestätigt.
KAMPF_FERTIGKEITEN = {
    "Handgemenge",
    "Nahkampf",
    "Schusswaffen",
    "Sportlichkeit",
    "Überleben",
    "Fahren",
    "Riggen",
}

# Ab dieser Summe (Sphären ODER NeuroWeaving-Fertigkeiten, ohne den fixen
# Hexkraft/NeuroWeaving-Sockel selbst) warnt der Berater vor Überladung.
# Mark, 27.09.2026 (zweite Rückmeldung): "6 Punkte" ist der eigentlich
# gewünschte Schwellenwert aus dem ursprünglichen Gespräch — die erste
# Fassung hatte hier fälschlich 10 stehen, wodurch die Warnung in der
# Praxis nie auftauchte.
MAGIE_SUMME_WARNSCHWELLE = 6

# Priorität der drei verbliebenen Warnungen, niedrigste Zahl zuerst gezeigt
# (Mark: "1. Sphären, 2. Wahrnehmung, 3. Kämpfen" — in dieser Reihenfolge,
# nicht in der Reihenfolge, in der sie berechnet werden).
_PRIORITAET = {"MAGIE_UEBERLADEN": 0, "KEINE_WAHRNEHMUNG": 1, "KEIN_KAMPFWERT": 2}


def berate(
    werte: dict[str, int],
    weg: str,
    attribut_kategorien: dict[str, list[str]] | None = None,
) -> list[dict[str, str]]:
    """Prüft die aktuellen Werte einer LAUFENDEN Erstellung auf Lücken.

    `werte` ist der aktuelle Zwischenstand (Trait-Name → Wert) — noch nicht
    unbedingt vollständig oder eingereicht, das hier läuft live während der
    Fertigkeiten-/Attributverteilung, nicht erst beim Abschluss.

    Gibt eine Liste von Hinweisen zurück, jeder mit `code` (stabil, fürs
    Frontend/Tests) und `text` (der eigentliche Spruch) — sortiert nach
    Priorität (Magie-Überladung zuerst, dann Wahrnehmung, dann Kampf).
    Leere Liste heißt nicht "perfekt ausbalanciert", nur "nichts
    Auffälliges gefunden". `attribut_kategorien` wird aktuell nicht mehr
    ausgewertet (Parameter bleibt für Aufrufer-Kompatibilität bestehen).
    """
    hinweise: list[dict[str, str]] = []

    if weg in ("MAGIER", "NEUROWEAVER"):
        zusatz_kategorie = "Sphäre" if weg == "MAGIER" else "NeuroWeaving"
        zusatz_namen = _kategorie_traits(zusatz_kategorie)
        zusatz_summe = sum(werte.get(n, 0) for n in zusatz_namen)
        if zusatz_summe > MAGIE_SUMME_WARNSCHWELLE:
            begriff = "Sphären" if weg == "MAGIER" else "NeuroWeaving-Fertigkeiten"
            hinweise.append({
                "code": "MAGIE_UEBERLADEN",
                "text": f"Du hast schon {zusatz_summe} Punkte in {begriff} versenkt — "
                f"empfohlen sind nicht mehr als {MAGIE_SUMME_WARNSCHWELLE}.",
            })

    if werte.get("Wahrnehmung", 0) == 0:
        hinweise.append({
            "code": "KEINE_WAHRNEHMUNG",
            "text": "0 auf Wahrnehmung? Du merkst nicht mal, wenn dir wer die "
            "Cyberware klaut.",
        })

    kampf_summe = sum(werte.get(n, 0) for n in KAMPF_FERTIGKEITEN)
    if kampf_summe == 0:
        hinweise.append({
            "code": "KEIN_KAMPFWERT",
            "text": "Komplett wehrlos, wenn's kracht. Mit dem Wert hast du wohl noch "
            "nicht mal einen Bud-Spencer-Film gesehen.",
        })

    hinweise.sort(key=lambda h: _PRIORITAET.get(h["code"], 99))
    return hinweise


# Kleine, feste Liste statt eines DB-Zugriffs — die Berater-Prüfung läuft oft
# (bei jedem Klick), ein Katalog-Query dafür wäre unnötig. Deckt sich mit
# traits/seed.py::NEOTOPIA_TRAITS, dort ist es die Quelle der Wahrheit.
_SPHAEREN_NAMEN = [
    "Korrespondenz", "Entropie", "Kräfte", "Leben", "Materie",
    "Gedanken", "Ursprung", "Geister", "Zeit",
]
_NEUROWEAVING_FERTIGKEITEN_NAMEN = [
    "Brute Force", "Schleichen", "Daten Verarbeiten", "Kompilieren",
    "Electronic Warfare", "Matrix-Navigation",
]


def _kategorie_traits(kategorie: str) -> list[str]:
    if kategorie == "Sphäre":
        return _SPHAEREN_NAMEN
    if kategorie == "NeuroWeaving":
        return _NEUROWEAVING_FERTIGKEITEN_NAMEN
    return []


# --- Statistik für den KI-Abschlusskommentar (27.09.2026) ---------------
# Getrennt von berate() (das produziert feste, kostenlose Sprüche) — hier
# geht es um rohe Zahlen, die die KI selbst pointiert einordnet. Nur EIN
# Aufruf pro Charakter, per explizitem Knopf (siehe traits/routes.py::
# erstellung_kommentar, ErstellungsKommentar.tsx) — Mark ist kostenbewusst
# beim LLM-Verbrauch, deshalb hier bewusst kein Auto-Trigger.
_ALLE_MAGIE_NAMEN = {"Hexkraft", "NeuroWeaving", *_SPHAEREN_NAMEN, *_NEUROWEAVING_FERTIGKEITEN_NAMEN}


def kommentar_daten(
    werte: dict[str, int],
    weg: str,
    attribut_kategorien: list[dict[str, Any]],
    magie_flavor: str = "MAGIER",
) -> dict[str, Any]:
    """Fasst den aktuellen Erstellungsstand für den KI-Kommentar zusammen.

    `attribut_kategorien` im Format von erstellung.regelwerk()["attributKategorien"]
    (Liste aus {"name": ..., "attribute": [...]}) — lesbare Namen statt
    Kategorie-Ids, damit sie direkt in den Prompt können.
    """
    attribut_summen = {
        k["name"]: sum(werte.get(n, 0) for n in k["attribute"]) for k in attribut_kategorien
    }
    alle_attribut_namen = {n for k in attribut_kategorien for n in k["attribute"]}

    fertigkeiten = {
        n: w
        for n, w in werte.items()
        if w > 0 and n not in alle_attribut_namen and n not in _ALLE_MAGIE_NAMEN
    }
    top_fertigkeiten = ", ".join(f"{n} {w}" for n, w in sorted(fertigkeiten.items(), key=lambda kv: -kv[1])[:5])

    magie_label: str | None = None
    magie_wert: int | None = None
    if weg == "MAGIER":
        magie_label = "Glauben" if magie_flavor == "HAERETIKER" else "Hexkraft"
        magie_wert = werte.get("Hexkraft", 0)
    elif weg == "NEUROWEAVER":
        magie_label = "NeuroWeaving-Wert"
        magie_wert = werte.get("NeuroWeaving", 0)

    weg_anzeige = {
        "KEINER": "Weg des Chroms",
        "MAGIER": "Häretiker" if magie_flavor == "HAERETIKER" else "Magier",
        "NEUROWEAVER": "NeuroWeaver",
    }.get(weg, weg)

    return {
        "weg_anzeige": weg_anzeige,
        "attribut_summen": attribut_summen,
        "top_fertigkeiten": top_fertigkeiten,
        "magie_label": magie_label,
        "magie_wert": magie_wert,
        "warnungen": [h["text"] for h in berate(werte, weg, {k["name"]: k["attribute"] for k in attribut_kategorien})],
    }
