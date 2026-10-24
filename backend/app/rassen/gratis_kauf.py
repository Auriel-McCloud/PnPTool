"""Ob der erste Shop-Kauf dieser Rasse kostenlos ist.

`gratisErsterKaufTyp` ist entweder ein Gegenstandstyp (z.B. "Hexware")
oder der Sentinel ALLE_TYPEN. Der Sentinel trifft jeden Typ — das
Einmal-Flag sitzt am Käufer (`rassenFeatureGenutzt`), nicht hier.
Ein Kauf verbraucht das Feature, der nächste kostet wieder den normalen Preis.

Frontend-Pendant: `frontend/src/rassen/gratisKauf.ts` (derselbe String).
"""

ALLE_TYPEN = "alle Typen"


def trifft(feature_typ: str | None, gegenstand_typ: str | None) -> bool:
    if not feature_typ:
        return False
    if feature_typ == ALLE_TYPEN:
        return True
    return bool(gegenstand_typ) and gegenstand_typ == feature_typ
