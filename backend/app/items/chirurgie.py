"""Cyber-, Bio- und Hexware: verbaut statt ausgerüstet.

Marks Korrektur vom 04.09.2026:

    "Das ist keine 'Ausrüstung' die funktioniert nicht wenn die ausgerüstet
    ist, die muss 'eingesetzt oder ein operiert werden' wenn die verbaut ist
    kann der Spieler die nicht mehr entfernen außer bei speziellen Events
    (er besucht einen Arzt oder ein Spieler hat die Medizin skills um das zu
    tun...) aber das sind keine Gegenstände die er nach dem sie Mal eigebaut
    wurden wieder ablegen kann, da sollten dann auch die Buttons dazu
    verschwinden. Stattdessen gibt es dann chirurgisch entfernen."

Vorher lag Chrom im selben Topf wie eine Jacke (`ablage=AUSGERUESTET`, per
Knopf ablegbar). Das neue Feld `verbaut` trennt beides:

* **nicht verbaut** — liegt im Rucksack, ist ein ganz normaler Gegenstand
  (kaufen, weitergeben, wegwerfen). Wirkt nicht.
* **verbaut** — sitzt im Körper. Wirkt. Lässt sich nur per Operation
  entfernen, nicht ablegen.
"""

CHROM_TYPEN = ("Cyberware", "Bioware", "Hexware")

# Ergebnis von pruefe_entfernung
ENTFERNEN = "ENTFERNEN"
ANTRAG = "ANTRAG"
ANTRAG_LAEUFT = "ANTRAG_LAEUFT"


def ist_chrom(gegenstand: dict) -> bool:
    """Ist das ein Implantat (Cyber-, Bio- oder Hexware)?"""
    return gegenstand.get("typ") in CHROM_TYPEN


def ist_wirksam(gegenstand: dict) -> bool:
    """Wirkt dieser Gegenstand gerade?

    Chrom wirkt, sobald es **verbaut** ist — die Ablage spielt dann keine
    Rolle mehr, es steckt ja im Körper. Alles andere wirkt, solange es
    **ausgerüstet** ist.
    """
    if ist_chrom(gegenstand):
        return bool(gegenstand.get("verbaut"))
    return gegenstand.get("ablage") == "AUSGERUESTET"


def kann_ablegen(gegenstand: dict, ist_gm: bool = False) -> bool:
    """Darf die Ablage dieses Gegenstands geändert werden?

    Verbautes Chrom nicht — für NIEMANDEN, auch nicht die SL: man legt kein
    Implantat in den Rucksack, der Weg heraus führt ausschliesslich über
    `.../chirurgie`. Genau hier verschwinden die Ablage-Knöpfe in der
    Oberfläche.

    Natürliche Rüstung (`istNatuerlich`, Rassen-/Kreatur-Feature wie Dug'Rahs
    Chitinpanzer, 11.10.2026 Verfeinerung) spiegelt dasselbe Muster, aber mit
    einer Ausnahme: für den Spieler ebenfalls gesperrt (sie ist Teil des
    Körpers, kein Kleidungsstück), die Spielleitung darf sie im Einzelfall
    trotzdem ablegen (Mark: Sonderfälle am Tisch — Verwandlung, Ritual,
    Korrektur). Deshalb braucht nur dieser Zweig die Rolle des Aufrufers.
    """
    if ist_chrom(gegenstand) and gegenstand.get("verbaut"):
        return False
    if gegenstand.get("istNatuerlich") and not ist_gm:
        return False
    return True


def kann_einsetzen(gegenstand: dict) -> bool:
    """Kann dieses Stück eingebaut werden?"""
    return ist_chrom(gegenstand) and not gegenstand.get("verbaut")


def kann_entfernen(gegenstand: dict) -> bool:
    """Kann dieses Stück herausoperiert werden?"""
    return ist_chrom(gegenstand) and bool(gegenstand.get("verbaut"))


def pruefe_entfernung(rolle: str, beantragt: bool) -> str:
    """Wer darf eine Entfernung auslösen?

    Mark: *"SL, aber ein Spieler kann 'Entfernung beantragen' (du
    bestätigst)"*. Die Spielleitung operiert, der Spieler fragt nur an —
    das Chrom sitzt schliesslich in einer Welt mit Ärzten, nicht in einem
    Menü.
    """
    if rolle == "GM":
        return ENTFERNEN
    return ANTRAG_LAEUFT if beantragt else ANTRAG
