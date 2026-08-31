"""Cyber- und Bioware: was sie kostet und was sie aus einem herausreisst.

Quelle: `docs/reference/Neotopia.xlsx`, Blatt *Regeln*, Zeilen 112-117.

Die Regel in einem Satz: **je mehr du je Bonuspunkt zahlst, desto weniger
Willenskraft kostet es dich dauerhaft.** Billiges Chrom aus der Hinterhofklinik
reisst doppelt so viel heraus wie der Bonus gross ist; die teuerste Arbeit nur
ein Viertel davon. Das ist das eigentliche Cyberpunk-Dilemma und der Grund,
warum ein armer Charakter nicht einfach "auch Chrom kaufen" kann.

**Gerundet wird erst am Ende** (Marks Ergänzung vom 31.08.2026): die Brüche der
einzelnen Stücke werden summiert, dann abgerundet, mindestens aber ein Punkt.
Ohne das hätte jedes teure Implantat für sich aufgerundet und die teure Arbeit
hätte sich nicht gelohnt.

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


def verlust_genau(bonus: int, preis_je_bonus: int) -> float:
    """Der **ungerundete** Verlust eines einzelnen Stücks.

    Ungerundet gespeichert, weil sich die Brüche über mehrere Stücke hinweg
    aufsummieren (siehe `verlust_gesamt`). Würde jedes Stück für sich
    gerundet, käme bei drei teuren Implantaten dreimal dieselbe Aufrundung
    zusammen — und teures Chrom hätte sich nicht gelohnt.

    Ein unbekannter Preis fällt auf die härteste Stufe zurück: lieber zu teuer
    veranschlagt als versehentlich gratis.
    """
    if bonus <= 0:
        return 0.0
    stufe = next((s for s in STUFEN if s.preis_je_bonus == preis_je_bonus), STUFEN[0])
    return max(0.0, bonus / stufe.teiler)


def verlust_gesamt(einzelverluste: list[float]) -> int:
    """Was alles eingebaute Chrom zusammen kostet.

    Marks Regel (31.08.2026): **erst summieren, dann abrunden — aber mindestens
    einen Punkt.** Ein einzelnes teures Implantat mit 0,67 kostet also 1; zwei
    davon kosten zusammen 1,33, also weiterhin 1. So zahlt sich teure Arbeit
    wirklich aus, statt bei jedem Stück erneut aufgerundet zu werden.

    Der Mindestpunkt greift nur, wenn überhaupt etwas anfällt: ein bewusst mit
    0 eingetragenes Implantat (rein kosmetisch) bleibt kostenlos.
    """
    summe = sum(max(0.0, w) for w in einzelverluste)
    if summe <= 0:
        return 0
    return max(1, int(summe))


def verlust_fuer(bonus: int, preis_je_bonus: int) -> int:
    """Was ein Stück **allein** kostet — für die Anzeige beim Anlegen.

    Dieselbe Regel wie bei mehreren, nur mit einem Posten: mindestens 1.
    """
    return verlust_gesamt([verlust_genau(bonus, preis_je_bonus)])


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
            # Ungerundet mitgeliefert, damit die Oberfläche zeigen kann, was
            # sich mit weiteren Implantaten aufsummiert.
            "wVerlustGenau": round(verlust_genau(bonus, s.preis_je_bonus), 2),
        }
        for s in STUFEN
    ]
