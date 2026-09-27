"""Charaktererstellungs-Berater — Karl-Klammer-artige Live-Warnungen.

Mark, 27.09.2026: seit Hexkraft/NeuroWeaving ein fixer Sockel sind (siehe
erstellung.py::MAGIE_FIXWERT), kann ein Magier/NeuroWeaver seine GESAMTEN
Fertigkeitsslots trotzdem noch in Sphären/NeuroWeaving-Fertigkeiten stecken
und mit 0 in jeder Alltagsfertigkeit dastehen — ein Chrom-Charakter kann das
nicht, weil er keinen so dichten Alternativ-Pool hat. Statt das hart zu
verbieten ("wer soweit kommt hat's verdient", CLAUDE.md) gibt es einen
Assistenten, der bei offensichtlichen Lücken auf sie hinweist — SICHTBAR,
NIEMALS BLOCKIEREND (Mark: "nur anzeigen, nie blockieren").

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
SOZIALE_FERTIGKEITEN = {
    "Anführen",
    "Ausflüchte",
    "Darbietung",
    "Einschüchtern",
    "Etiketten",
    "Menschenkenntnis",
    "Überzeugen",
    "Szenenkenntnis",
}
WISSENS_FERTIGKEITEN = {
    "Diebeshandwerk",
    "Handwerk",
    "Heimlichkeit",
    "Maker (Hardware)",
    "Ermitteln",
    "Finanzen",
    "Geisteswissenschaften",
    "Medizin",
    "Naturwissenschaften",
    "Okkultismus",
    "Politik",
    "Technologie",
    "Matrix",
    "Tierkunde",
}

# Ab dieser Summe (Sphären ODER NeuroWeaving-Fertigkeiten, ohne den fixen
# Hexkraft/NeuroWeaving-Sockel selbst) warnt der Berater vor Überladung.
# Mark, 27.09.2026: "6 ist ok" für den fixen Sockel (siehe MAGIE_FIXWERT in
# erstellung.py) — dieser Schwellenwert hier ist der ZUSÄTZLICHE Vorschlag
# aus dem ursprünglichen Gespräch (Punkt 5), unabhängig vom Sockel-Fix.
MAGIE_SUMME_WARNSCHWELLE = 10


def _attribut_summen(werte: dict[str, int], attribut_kategorien: dict[str, list[str]]) -> dict[str, int]:
    return {
        kategorie: sum(werte.get(name, 0) for name in namen)
        for kategorie, namen in attribut_kategorien.items()
    }


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
    Frontend/Tests) und `text` (der eigentliche Spruch). Leere Liste heißt
    nicht "perfekt ausbalanciert", nur "nichts Auffälliges gefunden".
    """
    hinweise: list[dict[str, str]] = []

    kampf_summe = sum(werte.get(n, 0) for n in KAMPF_FERTIGKEITEN)
    if kampf_summe == 0:
        hinweise.append({
            "code": "KEIN_KAMPFWERT",
            "text": "Komplett wehrlos, wenn's kracht. Mit dem Wert hast du wohl noch "
            "nicht mal einen Bud-Spencer-Film gesehen.",
        })

    if werte.get("Wahrnehmung", 0) == 0:
        hinweise.append({
            "code": "KEINE_WAHRNEHMUNG",
            "text": "0 auf Wahrnehmung? Du merkst nicht mal, wenn dir wer die "
            "Cyberware klaut.",
        })

    sozial_summe = sum(werte.get(n, 0) for n in SOZIALE_FERTIGKEITEN)
    if sozial_summe == 0:
        hinweise.append({
            "code": "KEIN_SOZIALWERT",
            "text": "Kein einziger sozialer Wert. Viel Spaß, das mit Fäusten zu "
            "verhandeln.",
        })

    wissen_summe = sum(werte.get(n, 0) for n in WISSENS_FERTIGKEITEN)
    if wissen_summe == 0:
        hinweise.append({
            "code": "KEIN_WISSENSWERT",
            "text": "Nichts an Wissen oder Technik. Frag lieber nicht, wie ein "
            "Kühlschrank von innen aussieht.",
        })

    if attribut_kategorien:
        summen = _attribut_summen(werte, attribut_kategorien)
        vorhandene = {k: s for k, s in summen.items() if s > 0}
        if len(vorhandene) >= 2:
            hoch = max(vorhandene.values())
            niedrig = min(vorhandene.values())
            # Deutlich schiefe Verteilung, nicht jede kleine Differenz.
            if hoch >= niedrig + 5:
                hinweise.append({
                    "code": "ATTRIBUTE_SCHIEF",
                    "text": "Sehr einseitig unterwegs — auf der einen Seite stark, "
                    "auf der anderen kaum vorhanden. Sehr schwach, aber schlau, was?",
                })

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
