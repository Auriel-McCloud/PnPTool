"""Reine Fachlogik der Critter-Pets — ohne Datenbank, ohne WebSocket.

Mark, 11.11.2026: das Pet läuft nur zu eingeloggten Party-Mitgliedern, nie
zur Spielleitung. Verlässt es einen Bildschirm am Rand, taucht es bei einem
anderen Mitglied auf der Gegenseite wieder auf — nicht in derselben Sekunde.
"""

import random

# Welche Sprites es gibt. Der Name ist zugleich der Ordner unter
# frontend/public/pets/. Jeder Critter kann später ein eigenes bekommen.
# `baerbel` (11.11.2026) ist kein Tier, sondern ein Gegenstand: die sprechende
# Bibel/das Zauberbuch, das fliegt (frontend/src/pets/flug.ts).
# `eisdrache`/`blitzdrache` (12.11.2026): derselbe Drache, umgefärbt, spuckt
# Eis bzw. Blitze statt Feuer.
PET_ARTEN = ("drache", "eisdrache", "blitzdrache", "baerbel")

# Häufchen bleiben liegen, wenn das Pet weiterzieht — aber nicht unbegrenzt.
# Wird es mehr, verschwindet das älteste (je Art gezählt).
HAEUFCHEN_MAX = 12

# Futternapf (Mark, 12.11.2026): „Füttern“ am Tierfutter (Verbrauchsgegenstand
# mit `istTierfutter`) stellt einen Napf auf den eigenen Bildschirm. Er bleibt
# liegen, bis ein Drache vorbeikommt und ihn leer frisst — das heilt den
# Critter um 3 Schlagschaden und macht ihn dem Fütternden zutraulicher.
# Kein SPUR_ARTEN-Eintrag: ein Tablet darf keinen Napf aus dem Nichts melden.
NAPF = "napf"
NAPF_HEILUNG = 3

# Zutraulichkeit je Spieler und Pet (Kante ZUTRAULICH, Wert unsichtbar):
# Streicheln +1 höchstens alle 5 Minuten je Spieler, Füttern +5 immer.
ZUTRAULICH_STREICHELN = 1
ZUTRAULICH_FUETTERN = 5
STREICHEL_ABKLINGEN_S = 300

# Was ein Pet auf einem Bildschirm hinterlassen kann: Häufchen und
# Brandflecken vom Feuerniesen (Mark, 11.11.2026). Beides bleibt liegen,
# bis der Spieler es wegmacht (antippen bzw. sauberwischen).
# Bärbel verliert stattdessen Seiten, die zerknittert liegen bleiben; ihr
# Tentakelmonster hinterlässt Schleim (wegwischen wie Brandflecken).
# Der Eisdrache hinterlässt Raureif (`frost`), ebenfalls zum Wegwischen.
SPUR_ARTEN = ("haeufchen", "brand", "seite", "schleim", "frost")

# Spuren, die vom Element herunterfallen können (neue Lage wird gemerkt).
FALLENDE_SPUREN = ("haeufchen", "seite")

# Pause zwischen „rechts raus“ und „links rein“ beim nächsten Tablet.
UNTERWEGS_MIN_S = 3.0
UNTERWEGS_MAX_S = 12.0

# Meldet ein Tablet nie „raus“ (Browser eingefroren, Akku leer, ohne dass
# die Leitung zuging), zieht der Server das Pet nach dieser Zeit selbst weiter.
# Großzügig: er darf bis zu 5 Minuten auf einem Popup schlafen (Mark, 11.11.),
# dazu kommen Besuch und Kletterei.
HOECHSTE_VERWEILDAUER_S = 600.0


def naechster_wirt(online: list[str], aktuell: str | None, zufall: random.Random | None = None) -> str | None:
    """Auf wessen Tablet geht es als Nächstes?

    Bevorzugt jemand anderen als den bisherigen Wirt. Ist nur einer da, kommt
    das Pet eben zu ihm zurück — es läuft raus und nach der Pause wieder rein.
    """
    if not online:
        return None
    z = zufall or random
    andere = sorted(p for p in online if p != aktuell)
    return z.choice(andere) if andere else sorted(online)[0]


def gegenseite(seite: str) -> str:
    """Rechts raus heißt beim Nächsten links rein — und umgekehrt."""
    return "links" if seite == "rechts" else "rechts"


def anteil(wert: float) -> float:
    """Bildschirmposition als Anteil 0..1 — Tablets sind verschieden groß."""
    return min(1.0, max(0.0, float(wert)))


def online_mitglieder(mitglieder: list[str], online: set[str]) -> list[str]:
    return sorted(m for m in mitglieder if m in online)


# ── Wachstum der Drachen (Mark, 12.11.2026) ──────────────────────────────
# Ein Drache fängt an einem neuen Critter als Ei an, schlüpft nach 5–10× Antippen
# (jeder am Tisch darf tippen) und wächst danach mit den EP des Critters — nur
# EP seit dem Schlüpfen zählen (`petEpStart`), sonst wäre ein neuer Critter mit
# allen alten Gruppen-EP sofort ausgewachsen.
# Fähigkeiten kommen mit dem Alter: Baby läuft nur unten, frisst, macht
# Häufchen. Ab 3 EP der heutige Drache (klettern, niesen, hüpfen). Burgermenü
# ab 8 EP, Fliegen (Wolkenlauf) ab 13 EP (Mark, 12.11.2026).
WACHSENDE_ARTEN = ("drache", "eisdrache", "blitzdrache")
TIPPS_MIN = 5
TIPPS_MAX = 10
JUNG_AB_EP = 3
FAEHIGKEITEN_AB_EP = {
    "klettern": JUNG_AB_EP,
    "niesen": JUNG_AB_EP,
    "springen": JUNG_AB_EP,
    "menue": 8,
    "wolken": 13,
}
ALLE_FAEHIGKEITEN = tuple(FAEHIGKEITEN_AB_EP)

# Größere Gestalten (Mark, 13.11.2026: „immer größer, eleganter und wie
# chinesische Drachen“). Mark, 12.11.: etwa 12 Wachstumsschritte, alle 5 EP
# einer — die EP je Schritt sind die Kampagnen-Einstellung `petWachstumEp`,
# weil er den Wert erst nach dem Praxistest einschätzen kann.
# Annahme Neko: alle 3 Schritte eine sichtbar neue Gestalt (15/30/45/60 EP),
# nach 12 Schritten ist er ausgewachsen. Dazwischen je zwei Zwischenformen
# (Mark, 13.11.2026: „bitte mach Zwischenformen“) — er wird mit jedem Schritt
# ein Stück länger und eleganter, neue Merkmale kommen mit der nächsten Gestalt.
# Index = Wachstumsschritt; der Name ist zugleich der Ordner unter
# frontend/public/pets/<art>/ (gleiche Liste: docs/assets/critter-pet/drache_stufen.py::FOLGE).
WACHSTUM_EP_STANDARD = 5
STUFEN_FOLGE = (
    "jung", "jung1", "jung2",
    "halbstark", "halbstark1", "halbstark2",
    "jungdrache", "jungdrache1", "jungdrache2",
    "gross", "gross1", "gross2",
    "ehrwuerdig",
)
# Was die SL von Hand einstellen darf (CritterFenster → Wachstum).
SETZBARE_STUFEN = ("ei", "baby") + STUFEN_FOLGE


def waechst(art: str | None) -> bool:
    return art in WACHSENDE_ARTEN


def stufe(
    art: str, pet_stufe: str | None, ep_gesamt: int, ep_start: int | None, ep_je_schritt: int = WACHSTUM_EP_STANDARD
) -> tuple[str, int | None]:
    """(`ei` | `baby` | ein Name aus `STUFEN_FOLGE`, EP seit dem Schlüpfen oder None).

    Drachen ohne `petStufe` (Bestand vor dem 12.11.2026) sind fertig und können
    alles — sie werden nicht nachträglich wieder klein."""
    if not waechst(art) or not pet_stufe:
        return "jung", None
    if pet_stufe == "ei":
        return "ei", None
    gewachsen = max(0, ep_gesamt - int(ep_start or 0))
    if gewachsen < JUNG_AB_EP:
        return "baby", gewachsen
    schritte = gewachsen // max(1, int(ep_je_schritt or WACHSTUM_EP_STANDARD))
    return STUFEN_FOLGE[min(schritte, len(STUFEN_FOLGE) - 1)], gewachsen


def gewachsen_fuer(stufe_: str, ep_je_schritt: int = WACHSTUM_EP_STANDARD) -> int | None:
    """So viele EP seit dem Schlüpfen braucht diese Stufe mindestens — damit die
    SL eine Stufe von Hand setzen kann, ohne ein eigenes Feld dafür: gesetzt
    wird nur der Startwert `petEpStart`. None = Ei oder unbekannt."""
    if stufe_ == "baby":
        return 0
    if stufe_ not in STUFEN_FOLGE:
        return None
    return max(JUNG_AB_EP, STUFEN_FOLGE.index(stufe_) * max(1, int(ep_je_schritt or WACHSTUM_EP_STANDARD)))


def faehigkeiten(art: str, stufe_: str, gewachsen: int | None) -> list[str]:
    if not waechst(art) or gewachsen is None:
        return list(ALLE_FAEHIGKEITEN) if stufe_ != "ei" else []
    return [f for f, ab in FAEHIGKEITEN_AB_EP.items() if gewachsen >= ab]


def risse(tipps: int, noetig: int) -> int:
    """0–4 Risse im Ei, je nachdem, wie weit es schon ist."""
    if noetig <= 0:
        return 4
    return min(4, -(-4 * tipps // noetig))
