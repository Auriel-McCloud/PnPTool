"""Cyber-, Bio- und MagWare: verbaut statt ausgerüstet.

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

CHROM_TYPEN = ("Cyberware", "Bioware", "MagWare")

# Ergebnis von pruefe_entfernung
ENTFERNEN = "ENTFERNEN"
ANTRAG = "ANTRAG"
ANTRAG_LAEUFT = "ANTRAG_LAEUFT"


def ist_chrom(gegenstand: dict) -> bool:
    """Ist das ein Implantat (Cyber-, Bio- oder MagWare)?"""
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


def kann_ablegen(gegenstand: dict) -> bool:
    """Darf die Ablage dieses Gegenstands geändert werden?

    Verbautes Chrom nicht: man legt kein Implantat in den Rucksack. Genau
    hier verschwinden die Ablage-Knöpfe in der Oberfläche.
    """
    return not (ist_chrom(gegenstand) and gegenstand.get("verbaut"))


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
