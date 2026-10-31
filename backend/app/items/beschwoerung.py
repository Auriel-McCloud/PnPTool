"""Beschwörungs-Ki-Tama: Probe-Formel und Beschwörungswert.

Mark, 29.10.2026, Idee direkt im Anschluss ans Ki-Tama-Feature: "Wir könnten
Beschwörungen-Ki-Tamas machen, hinter denen gewisse Critter stecken, die man
im Kampf beschwören kann." Siehe docs/wiki/concepts/augments-ausruestung.md,
Abschnitt "Ideen für später: Beschwörungs-Materia" für die volle Herleitung.

Rechnet rein (keine Datenbankzugriffe) — dieselbe Motivation wie
kampf/ruestung.py/items/augments.py: die Formel steht an einer Stelle und
ist ohne DB testbar.
"""


def beschwoerungsstufe(ausruestungsfertigkeiten: dict[str, int], ki_tama_fertigkeiten: dict[str, bool]) -> int:
    """Der Beschwörungswert ist KEIN eigenes Feld — er ist einfach die
    höchste als Ki-Tama markierte ausruestungsfertigkeiten-Stufe auf diesem
    Gegenstand. 0, wenn keine Fertigkeit als Ki-Tama markiert ist (dann ist
    es kein nutzbares Beschwörungs-Ki-Tama, auch wenn `beschworenerCritterId`
    gesetzt sein sollte).
    """
    markiert = [int(wert) for name, wert in ausruestungsfertigkeiten.items() if ki_tama_fertigkeiten.get(name)]
    return max(markiert, default=0)


def benoetigte_erfolge(stufe: int, schwierigkeit: int) -> int:
    """Beschwörungswert ÷ 2, aufgerundet, plus SL-Schwierigkeitsgrad, aber
    MINDESTENS 1 — Mark, 30.10.2026: "es ist stufe ÷ 2 Erfolge, aber
    mindestens +1, mit der Option +1 und +2 beim Item hinzuzufügen"
    (= `beschwoerungsSchwierigkeit`, von der SL beim Anlegen gewählt).

    ENTSCHIEDEN (30.10.2026): "das ist ja wie Magie... also muss er
    Intelligenz + den Wert der Beschwörung würfeln." Stufe 1→1, 2→1, 3→2,
    4→2, 5→3, 6→3 — bewusst NICHT "Wert − 2, Minimum 1" (verworfen: die
    Erfolgsschwelle muss mit dem Pool mitwachsen, sonst sind niedrige Stufen
    alle gleich trivial). Der Schwierigkeitsgrad kommt additiv oben drauf,
    negative Werte zählen als 0 — eine Beschwörung ist nie gratis (0
    Erfolge), auch nicht bei Stufe 0.
    """
    stufe = max(0, stufe)
    schwierigkeit = max(0, schwierigkeit)
    return max(1, -(-stufe // 2) + schwierigkeit)


def ruf_entscheidung(ausgang: str, schon_gerufen: bool, erfolge: int, benoetigt: int) -> str:
    """Was ein gemeldeter Beschwörungs-Ausgang mit dem einen Ruf pro Kampf macht.

    Mark, 01.11.2026: jedes Ki-Tama nur einmal pro Kampf, auch auf Stufe 1.
    Ein Fehlwurf verbraucht den Ruf nicht, ein Patzer schon. „0 Erfolge“ ist
    kein Patzer — der Ausgang muss explizit gemeldet werden.

    Rückgabe:
    - ``blockiert``: dieser Kampf hat den Ruf schon verbraucht
    - ``offen``: Fehlwurf, Ruf bleibt, kein Critter
    - ``verbraucht``: Patzer, Ruf weg, kein Critter
    - ``zu-wenig``: als Erfolg gemeldet, Schwelle nicht erreicht — zählt als Fehlwurf
    - ``gerufen``: genug Erfolge, Ruf weg, Critter kommt
    """
    if schon_gerufen:
        return "blockiert"
    if ausgang == "patzer":
        return "verbraucht"
    if ausgang == "nein":
        return "offen"
    if erfolge < benoetigt:
        return "zu-wenig"
    return "gerufen"
