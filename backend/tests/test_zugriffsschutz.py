"""Prüft strukturell, dass Spieler nichts verändern können.

Hintergrund: die Kampagnen-Router hingen früher pauschal an
require_campaign_gm. Damit Spieler lesen können, wurde das auf
require_campaign_zugang gelockert — jede schreibende Route muss seither
require_campaign_gm einzeln verlangen. Wird das bei einer neuen Route
vergessen, wäre sie für Spieler offen.

Der Test schaut dafür in den Abhängigkeitsbaum der App statt HTTP-Aufrufe zu
machen: kein Datenbankbedarf, und er erwischt auch Routen, an die beim
Schreiben von Testfällen niemand gedacht hat.
"""

from app.auth.dependencies import require_campaign_gm, require_gm
from app.main import app

SCHREIBEND = {"POST", "PUT", "PATCH", "DELETE"}

# Anmeldung läuft naturgemäß ohne bestehende Sitzung; die übrigen sind
# Selbstverwaltung des Spielers für den eigenen Zugang.
OHNE_GM_ERLAUBT = {
    "/api/spieler/login",
    # Passwort für sich selbst setzen — prüft über require_spieler, dass es
    # der eigene Zugang ist, und ändert nur dieses eine Feld.
    "/api/spieler/passwort",
    "/api/spieler/abmelden",
    "/api/auth/gm/login",
    "/api/auth/gm/logout",
    # Kampagne anlegen hängt an require_gm, nicht an einer Kampagne
    "/api/campaigns",
    # Einzige Schreibroute, die auch Spieler nutzen dürfen: den eigenen Kram
    # umlegen. Sie prüft die Besitzverhältnisse selbst (siehe items/routes.py)
    # und darf ausschließlich das Ablage-Feld ändern.
    "/api/campaigns/{campaign_id}/gegenstaende/{item_id}/ablage",
    # Ebenso: Schaden abhaken und Willenskraft verbrauchen gehoert zum
    # Spielen. Prueft die Person selbst und laesst nur Zustandsfelder zu.
    "/api/campaigns/{campaign_id}/personen/{person_id}/zustand",
    # Den eigenen Charakter erstellen. Prueft die Person selbst, laesst sich
    # nur einmal aufrufen (danach 409) und laeuft vollstaendig durch
    # traits/erstellung.pruefe — regelwidrige Verteilungen werden abgelehnt.
    "/api/campaigns/{campaign_id}/personen/{person_id}/erstellung",
    # Eigene Erfahrung ausgeben. Prueft die Person selbst; der Preis wird
    # serverseitig berechnet, nicht uebernommen, und gegen den vorhandenen
    # Punktestand geprueft. Erfahrung *vergeben* bleibt der Spielleitung
    # (eigene Route .../erfahrung mit require_campaign_gm).
    "/api/campaigns/{campaign_id}/personen/{person_id}/steigern",
}


def _abhaengigkeiten(dependant) -> set:
    """Alle Prüf-Funktionen einer Route, auch verschachtelte."""
    gefunden = set()
    if dependant.call is not None:
        gefunden.add(dependant.call)
    for unter in dependant.dependencies:
        gefunden |= _abhaengigkeiten(unter)
    return gefunden


def alle_routen():
    """Sämtliche Routen der App.

    Diese FastAPI-Fassung hängt Router verzögert ein: in app.routes stehen
    dann _IncludedRouter-Platzhalter statt der Routen selbst. Deshalb wird
    über original_router abgestiegen, statt sich auf eine flache Liste zu
    verlassen — sonst prüfte der Test unbemerkt fast nichts.
    """
    offen = list(app.routes)
    while offen:
        eintrag = offen.pop()
        unter = getattr(eintrag, "original_router", None)
        if unter is not None:
            offen.extend(unter.routes)
        elif hasattr(eintrag, "dependant"):
            yield eintrag


def schreibende_routen():
    for route in alle_routen():
        if getattr(route, "methods", set()) & SCHREIBEND:
            yield route


def test_jede_schreibende_route_verlangt_die_spielleitung():
    offen = []
    for route in schreibende_routen():
        if route.path in OHNE_GM_ERLAUBT:
            continue
        wachen = _abhaengigkeiten(route.dependant)
        if require_campaign_gm not in wachen and require_gm not in wachen:
            offen.append(f"{sorted(getattr(route, 'methods'))} {route.path}")
    assert not offen, "Schreibende Routen ohne Spielleitungs-Prüfung: " + ", ".join(offen)


def test_ausnahmeliste_enthaelt_nur_existierende_routen():
    """Verhindert, dass die Liste Routen deckt, die es längst nicht mehr gibt."""
    vorhanden = {r.path for r in alle_routen()}
    verwaist = OHNE_GM_ERLAUBT - vorhanden
    assert not verwaist, f"Ausnahmen für nicht mehr existierende Routen: {verwaist}"


def test_leseseite_ist_fuer_spieler_erreichbar():
    """Gegenprobe: die Kampagnen-Leserouten dürfen NICHT an der
    Spielleitung hängen, sonst wäre der Spielerzugang wirkungslos."""
    from app.auth.dependencies import require_campaign_zugang

    geprueft = 0
    for route in alle_routen():
        if "GET" not in getattr(route, "methods", set()):
            continue
        if not route.path.startswith("/api/campaigns/{campaign_id}"):
            continue
        if "/spieler" in route.path:  # Spielerverwaltung ist Sache der Spielleitung
            continue
        wachen = _abhaengigkeiten(route.dependant)
        assert require_campaign_gm not in wachen, f"{route.path} bleibt für Spieler gesperrt"
        assert require_campaign_zugang in wachen, f"{route.path} prüft den Kampagnenzugang nicht"
        geprueft += 1
    assert geprueft > 0, "keine Leserouten gefunden — Test greift ins Leere"
