"""Das NeotopiA-Würfelsystem — Pool aus zehnseitigen Würfeln.

Regelblatt (`docs/regeln-neotopia.md`, Zeilen 9-12):

* **1-5 Misserfolg, 6-10 Erfolg.**
* **Kritisch:** zwei Zehnen zählen wie vier Erfolge, drei wie sechs — jede
  weitere Zehn verdoppelt entsprechend.
* **Patzer:** die Hälfte der Würfel zeigt 1.

Gewürfelt wird mit `secrets` statt `random`: Der Unterschied ist am Tisch
nicht spürbar, aber ein vorhersagbarer Zufallsgenerator auf einem Server, den
Spieler erreichen, ist eine unnötige Angriffsfläche.
"""

import secrets

# Obergrenze gegen Tippfehler wie 99999. Der grösste sinnvolle Pool in
# NeotopiA liegt weit darunter (Attribut + Fähigkeit + Boni).
MAX_POOL = 100

SEITEN = 10
# Ab diesem Wert zählt ein Würfel als Erfolg ("alles über 5").
ERFOLG_AB = 6


def zaehle_erfolge(augen: list[int]) -> int:
    """Erfolge nach NeotopiA-Regeln, Zehnen kritisch gewertet.

    Zwei Zehnen zählen wie vier Erfolge, drei wie sechs — also **zwei Erfolge
    je Zehn**, sobald mindestens zwei gefallen sind. Eine einzelne Zehn bleibt
    ein einfacher Erfolg.
    """
    zehnen = sum(1 for a in augen if a == SEITEN)
    uebrige = sum(1 for a in augen if ERFOLG_AB <= a < SEITEN)

    if zehnen >= 2:
        return zehnen * 2 + uebrige
    return zehnen + uebrige


def ist_patzer(augen: list[int]) -> bool:
    """Patzer, wenn mindestens die Hälfte der Würfel eine 1 zeigt.

    Bei ungerader Anzahl wird aufgerundet: bei fünf Würfeln braucht es drei
    Einsen. Ein leerer Pool patzt nicht — es wurde ja nicht gewürfelt.
    """
    if not augen:
        return False
    einsen = sum(1 for a in augen if a == 1)
    return einsen * 2 >= len(augen)


def werte_wurf(augen: list[int]) -> dict:
    """Wertet gefallene Augen aus, ohne selbst zu würfeln.

    Getrennt vom Würfeln, damit auch ein **physischer** Wurf ausgewertet
    werden kann — Mark spielt mit echten Würfeln, das Tool rechnet nur nach.
    """
    return {
        # In Wurfreihenfolge: am Tisch will man sehen, was gefallen ist.
        "augen": list(augen),
        "erfolge": zaehle_erfolge(augen),
        "patzer": ist_patzer(augen),
    }


def wuerfle(pool: int) -> dict:
    """Würfelt einen Pool und wertet ihn aus."""
    if pool > MAX_POOL:
        raise ValueError(f"Pool zu gross (höchstens {MAX_POOL})")
    if pool <= 0:
        return werte_wurf([])
    augen = [secrets.randbelow(SEITEN) + 1 for _ in range(pool)]
    return werte_wurf(augen)
