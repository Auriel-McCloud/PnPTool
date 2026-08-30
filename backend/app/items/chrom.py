"""Cyber- und Bioware: was sie kostet und was sie aus einem herausreisst.

Quelle: `docs/reference/Neotopia.xlsx`, Blatt *Regeln*, Zeilen 112-117.

Die Regel in einem Satz: **je mehr du je Bonuspunkt zahlst, desto weniger
Willenskraft kostet es dich dauerhaft.** Billiges Chrom aus der Hinterhofklinik
reisst doppelt so viel heraus wie der Bonus gross ist; die teuerste Arbeit nur
ein Viertel davon. Das ist das eigentliche Cyberpunk-Dilemma und der Grund,
warum ein armer Charakter nicht einfach "auch Chrom kaufen" kann.

Der Verlust senkt das **Maximum** der Willenskraft, nicht den aktuellen Stand
(siehe `traits/bogen.py`).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chromstufe:
    """Eine Qualitätsstufe: Preis je Bonuspunkt und was sie kostet."""

    preis_je_bonus: int
    #: Durch wieviel der Bonus geteilt wird. 0.5 heisst: doppelter Verlust.
    teiler: float
    name: str
    beschreibung: str


# Reihenfolge von billig und schmerzhaft zu teuer und schonend.
STUFEN: list[Chromstufe] = [
    Chromstufe(500, 0.5, "Hinterhof", "Billig eingesetzt, und der Körper zahlt doppelt."),
    Chromstufe(2_000, 1, "Straße", "Solide Ware ohne Anspruch."),
    Chromstufe(5_000, 2, "Klinik", "Ordentlich verbaut, halbwegs verträglich."),
    Chromstufe(10_000, 3, "Konzern", "Gute Arbeit, entsprechend teuer."),
    Chromstufe(20_000, 4, "Maßanfertigung", "Das Beste, was Geld kaufen kann."),
]

# Prothesen sind Pauschalen, kein Bonus je Punkt (Zeilen 113-114).
PROTHESE_PREIS = 10_000
PROTHESE_VERLUST = 2
PROTHESEN_GADGET_PREIS = 5_000

# Körperzonen vom Charakterblatt.
KOERPERZONEN = ["Kopf", "Arme", "Torso", "Beine"]


def verlust_fuer(bonus: int, preis_je_bonus: int) -> int:
    """Willenskraftverlust für einen Bonus auf der gegebenen Preisstufe.

    Immer **abgerundet** (so steht es im Blatt) und nie unter null. Ein
    unbekannter Preis fällt auf die härteste Stufe zurück — lieber zu teuer
    veranschlagt als versehentlich gratis.
    """
    if bonus <= 0:
        return 0
    stufe = next((s for s in STUFEN if s.preis_je_bonus == preis_je_bonus), STUFEN[0])
    return max(0, int(bonus / stufe.teiler))


def preis_fuer(bonus: int, preis_je_bonus: int) -> int:
    """Was der Einbau kostet: Bonus mal Preis je Punkt."""
    return max(0, bonus) * max(0, preis_je_bonus)


def stufen_uebersicht(bonus: int = 1) -> list[dict]:
    """Alle Stufen mit Preis und Verlust für einen gegebenen Bonus.

    Für die Oberfläche: sie soll die Wahl zeigen können, ohne die Formel
    nachzubauen — sonst driften Anzeige und Abrechnung auseinander.
    """
    return [
        {
            "name": s.name,
            "beschreibung": s.beschreibung,
            "preisJeBonus": s.preis_je_bonus,
            "preis": preis_fuer(bonus, s.preis_je_bonus),
            "wVerlust": verlust_fuer(bonus, s.preis_je_bonus),
        }
        for s in STUFEN
    ]
