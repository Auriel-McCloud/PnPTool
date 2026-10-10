"""Plan-Autosteigerung — EP nach einem geordneten Plan ausgeben.

Kein Resteverwertung: der nächste *legale* geplante Schritt gilt, oder das
EP bleibt liegen. Illegale Plan-Einträge (unbekannt, schon am Max, Wert 0)
werden verworfen, ohne etwas anderes zu kaufen. Siehe
docs/wiki/entities/hintergrund-baukasten-feature.md.
"""

from dataclasses import dataclass, field

from app.traits import erfahrung

WILLENSKRAFT = "Willenskraft"
EP_JE_MENTOR_PUNKT = 20


def mentor_ep(punkte: int) -> int:
    """EP-Soll für den Mentor: 20 je Hintergrundpunkt."""
    return max(0, int(punkte)) * EP_JE_MENTOR_PUNKT


@dataclass(frozen=True)
class Schritt:
    name: str
    von: int
    nach: int
    kosten: int


@dataclass
class AutosteigerungErgebnis:
    werte: dict[str, int]
    restplan: list[str]
    restbudget: int
    schritte: list[Schritt] = field(default_factory=list)


def _preis(name: str, von: int, kategorie: str | None) -> int | None:
    if name == WILLENSKRAFT:
        return erfahrung.kosten_willenskraft(von)
    if not kategorie:
        return None
    return erfahrung.kosten(kategorie, von)


def fuehre_plan_aus(
    werte: dict[str, int],
    kategorien: dict[str, str],
    plan: list[str],
    budget: int,
    maxima: dict[str, int] | None = None,
) -> AutosteigerungErgebnis:
    aktuell = dict(werte)
    restplan = list(plan)
    rest = max(0, int(budget))
    deckel = maxima or {}
    schritte: list[Schritt] = []

    while restplan:
        name = restplan[0]
        von = int(aktuell.get(name, 0))
        maximum = deckel.get(name)
        if maximum is not None and von >= maximum:
            restplan.pop(0)
            continue
        if name != WILLENSKRAFT and von <= 0:
            restplan.pop(0)
            continue
        preis = _preis(name, von, kategorien.get(name))
        if preis is None:
            restplan.pop(0)
            continue
        if preis > rest:
            break
        aktuell[name] = von + 1
        rest -= preis
        schritte.append(Schritt(name=name, von=von, nach=von + 1, kosten=preis))
        restplan.pop(0)

    return AutosteigerungErgebnis(
        werte=aktuell,
        restplan=restplan,
        restbudget=rest,
        schritte=schritte,
    )
