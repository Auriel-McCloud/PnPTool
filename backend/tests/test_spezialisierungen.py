"""Fertigkeiten-Spezialisierung: Vergabe-Schwellen, Auto-Grant-Hook, CRUD.

Echte Neo4j-Integration wie test_achievements.py/test_hintergruende.py:
reine asyncio.run()-Aufrufe gegen Repository-Funktionen, keine HTTP-Schicht
(dieses Projekt nutzt bisher kein FastAPI-TestClient, siehe
test_tutorial_shop_rassen_features.py).
"""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.spezialisierungen import repository as spezialisierungen_repository
from app.traits import repository as traits_repository


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-spezialisierung-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Spezialisierung-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)
        await session.run("MATCH (c:Campaign {id: $cid}) DETACH DELETE c", cid=cid)


async def _person_anlegen(cid: str, name: str, **extra) -> str:
    pid = str(uuid.uuid4())
    driver = get_driver()
    felder = {"personType": "PC", "sichtbarkeit": "GM", "sichtbarFuer": [], **extra}
    props = ", ".join(f"{k}: ${k}" for k in felder)
    async with driver.session() as session:
        await session.run(
            f"""
            MATCH (c:Campaign {{id: $cid}})
            CREATE (p:Person {{id: $pid, campaignId: $cid, name: $name, {props}}})
            CREATE (c)-[:HAT_ENTITAET]->(p)
            """,
            cid=cid, pid=pid, name=name, **felder,
        )
    return pid


async def _trait_def_id(name: str, kategorie: str = "Fertigkeit") -> str:
    """Reale TraitDef-ID aus dem beim Serverstart geseedeten Katalog
    (seed_traits läuft beim App-Import, siehe app/main.py::lifespan —
    im Testlauf wird dasselbe Neo4j benutzt, der Katalog existiert also)."""
    return f"neotopia:{kategorie}:{name}"


# ===========================================================================
# Reine Funktion: Schwellen-Logik
# ===========================================================================


class TestAutomatischeSlotAnzahl:
    def test_kein_slot_unter_vier(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(0, 3) == 0

    def test_ein_slot_bei_erreichen_von_vier(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(3, 4) == 1

    def test_kein_slot_von_vier_auf_fuenf(self):
        """Nicht kumulativ dazwischen — 5 ist keine eigene Schwelle."""
        assert spezialisierungen_repository.automatische_slot_anzahl(4, 5) == 0

    def test_ein_weiterer_slot_bei_erreichen_von_sechs(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(5, 6) == 1

    def test_beide_slots_bei_sprung_von_drei_direkt_auf_sechs(self):
        """GM setzt den Wert von Hand / Charakter startet schon auf 6 —
        beide überschrittenen Schwellen (4 und 6) zählen auf einen Schlag."""
        assert spezialisierungen_repository.automatische_slot_anzahl(3, 6) == 2

    def test_kein_slot_beim_sinken(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(6, 3) == 0

    def test_kein_slot_bei_unveraendertem_wert(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(4, 4) == 0

    def test_null_crossing_oberhalb_von_sechs_bleibt_zwei(self):
        """Auch ein Sprung weit über 6 hinaus (z.B. 0 -> 10 bei Hexkraft-
        artigen Werten) vergibt nur die zwei definierten Slots, keinen dritten."""
        assert spezialisierungen_repository.automatische_slot_anzahl(0, 10) == 2


class TestSchwellenFuer:
    def test_fertigkeit_bekommt_vier_sechs(self):
        assert spezialisierungen_repository.schwellen_fuer("Fertigkeit") == (4, 6)

    def test_neuroweaving_bekommt_vier_sechs(self):
        assert spezialisierungen_repository.schwellen_fuer("NeuroWeaving") == (4, 6)

    def test_sphaere_bekommt_zwei_vier_sechs(self):
        assert spezialisierungen_repository.schwellen_fuer("Sphäre") == (2, 4, 6)


class TestAutomatischeSlotAnzahlSphaere:
    """Dieselbe Logik wie TestAutomatischeSlotAnzahl, aber mit den
    Sphären-eigenen Schwellen (2/4/6) durchgereicht."""

    SCHWELLEN = spezialisierungen_repository.SPHAERE_SCHWELLEN

    def test_kein_slot_unter_zwei(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(0, 1, self.SCHWELLEN) == 0

    def test_erster_slot_bei_zwei(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(1, 2, self.SCHWELLEN) == 1

    def test_kein_slot_von_zwei_auf_drei(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(2, 3, self.SCHWELLEN) == 0

    def test_zweiter_slot_bei_vier(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(3, 4, self.SCHWELLEN) == 1

    def test_dritter_slot_bei_sechs(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(5, 6, self.SCHWELLEN) == 1

    def test_alle_drei_slots_bei_sprung_von_null_auf_sechs(self):
        assert spezialisierungen_repository.automatische_slot_anzahl(0, 6, self.SCHWELLEN) == 3


# ===========================================================================
# Auto-Grant-Hook: set_rating / steigere / set_ratings_bulk
# ===========================================================================


def test_set_rating_vergibt_slot_bei_schwelle_vier():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")

            await traits_repository.set_rating(cid, pid, trait_id, 3, None)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []

            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            slots = await spezialisierungen_repository.fuer_person(cid, pid)
            assert len(slots) == 1
            assert slots[0]["quelle"] == "automatisch"
            assert slots[0]["text"] == ""
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_set_rating_vergibt_zweiten_slot_bei_schwelle_sechs_nicht_bei_fuenf():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")

            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            await traits_repository.set_rating(cid, pid, trait_id, 5, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1

            await traits_repository.set_rating(cid, pid, trait_id, 6, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 2
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_steigere_vergibt_slot_genau_wie_set_rating():
    """EP-Steigerungs-Pfad (traits/routes.py::steigere_wert) — eigene
    Repository-Funktion, muss denselben Hook feuern."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")

            await traits_repository.steigere(cid, pid, trait_id, 1)
            await traits_repository.steigere(cid, pid, trait_id, 2)
            await traits_repository.steigere(cid, pid, trait_id, 3)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []

            await traits_repository.steigere(cid, pid, trait_id, 4)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_set_ratings_bulk_vergibt_slot_bei_charaktererstellung_direkt_auf_vier():
    """Charaktererstellung: ein Fertigkeitspaket kann direkt eine 4 anlegen
    (kein vorheriger HAS_TRAIT-Knoten existiert) — alt muss dann als 0
    gelten, nicht als Fehler."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Frisch Erstellt")
            await traits_repository.set_ratings_bulk(cid, pid, {"Schusswaffen": 4, "Fahren": 2})
            slots = await spezialisierungen_repository.fuer_person(cid, pid)
            trait_id = await _trait_def_id("Schusswaffen")
            assert len(slots) == 1
            assert slots[0]["traitDefId"] == trait_id
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_set_ratings_bulk_resubmission_vergibt_nicht_doppelt():
    """SL reicht die Erstellung erneut ein (Korrektur) — derselbe Endwert
    darf keinen zweiten Slot auslösen."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Frisch Erstellt")
            await traits_repository.set_ratings_bulk(cid, pid, {"Schusswaffen": 4})
            await traits_repository.set_ratings_bulk(cid, pid, {"Schusswaffen": 4})
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_sinken_entfernt_vergebenen_slot_nicht():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")
            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            await traits_repository.set_rating(cid, pid, trait_id, 2, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_attribut_bekommt_niemals_eine_spezialisierung():
    """Attribute sind explizit ausgeschlossen (Marks Vorgabe) — auch beim
    Überschreiten von 4/6 passiert hier nichts."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Körperkraft", "AttributKörperlich")
            await traits_repository.set_rating(cid, pid, trait_id, 6, None)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_sphaere_bekommt_slots_bei_zwei_vier_sechs():
    """Sphären-Spezialisierung (23.10.2026): eigene Schwellen 2/4/6 statt
    4/6, macht also DREI Slots statt zwei möglich."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Magierin")
            trait_id = await _trait_def_id("Kräfte", "Sphäre")

            await traits_repository.set_rating(cid, pid, trait_id, 1, None)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []

            await traits_repository.set_rating(cid, pid, trait_id, 2, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1

            await traits_repository.set_rating(cid, pid, trait_id, 3, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 1

            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 2

            await traits_repository.set_rating(cid, pid, trait_id, 5, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 2

            await traits_repository.set_rating(cid, pid, trait_id, 6, None)
            assert len(await spezialisierungen_repository.fuer_person(cid, pid)) == 3
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_neuroweaving_wert_selbst_bekommt_keine_spezialisierung():
    """NeuroWeavingWert (der Grundwert, mechanisch wie Hexkraft behandelt)
    ist kein Slot-Kandidat — nur die sechs NeuroWeaving-FERTIGKEITEN
    darunter sind es (siehe nächster Test)."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Weaver")
            trait_id = await _trait_def_id("NeuroWeaving", "NeuroWeavingWert")
            await traits_repository.set_rating(cid, pid, trait_id, 6, None)
            assert await spezialisierungen_repository.fuer_person(cid, pid) == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_neuroweaving_fertigkeit_bekommt_spezialisierung():
    """Die NeuroWeaving-Fertigkeiten (z.B. Brute Force) zählen laut
    erstellung.py mechanisch als Fertigkeit — Slot-Vergabe greift genauso."""

    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Weaver")
            trait_id = await _trait_def_id("Brute Force", "NeuroWeaving")
            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            slots = await spezialisierungen_repository.fuer_person(cid, pid)
            assert len(slots) == 1
        finally:
            await _aufraeumen(cid)

    _run(lauf())


# ===========================================================================
# CRUD: benennen (Zweiphasen-Namensrecht) und gekaufte Slots
# ===========================================================================


def test_gekaufter_slot_kommt_zusaetzlich_zum_automatischen_und_traegt_eigene_quelle():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")
            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            await spezialisierungen_repository.gekauft_anlegen(cid, pid, trait_id)

            slots = await spezialisierungen_repository.fuer_person(cid, pid)
            assert len(slots) == 2
            quellen = sorted(s["quelle"] for s in slots)
            assert quellen == ["automatisch", "gekauft"]
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_benennen_setzt_text_und_benanntvonspieler_flag():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            trait_id = await _trait_def_id("Schusswaffen")
            await traits_repository.set_rating(cid, pid, trait_id, 4, None)
            [slot] = await spezialisierungen_repository.fuer_person(cid, pid)

            aktualisiert = await spezialisierungen_repository.benennen(
                cid, pid, slot["id"], "Pistolen", als_spieler=True
            )
            assert aktualisiert is not None
            assert aktualisiert["text"] == "Pistolen"
            assert aktualisiert["benanntVonSpieler"] is True
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_benennen_unbekannter_slot_gibt_none():
    async def lauf():
        cid = await _kampagne_anlegen()
        try:
            pid = await _person_anlegen(cid, "Ryu")
            ergebnis = await spezialisierungen_repository.benennen(
                cid, pid, "nicht-vorhanden", "x", als_spieler=True
            )
            assert ergebnis is None
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_vorschlaege_landen_im_traitkatalog():
    """TRAIT_VORSCHLAEGE (seed.py) muss über list_catalog()/TraitDefResponse
    beim Client ankommen — ohne das zeigt das Popup nie Vorschlag-Chips."""

    async def lauf():
        katalog = await traits_repository.list_catalog("neotopia")
        schusswaffen = next(t for t in katalog if t["name"] == "Schusswaffen")
        assert "Pistolen" in schusswaffen["vorschlaege"]
        # Eine Fertigkeit ohne eigene Vorschläge liefert eine leere Liste,
        # nicht None/fehlendes Feld — sonst crasht die Pydantic-Validierung.
        unbekannt = next(t for t in katalog if t["name"] == "Diebeshandwerk")
        assert unbekannt["vorschlaege"] == []
    _run(lauf())


# ===========================================================================
# GM-Oberfläche (22.10.2026, Folge-Feature): Vorschlagstexte live bearbeiten
# ===========================================================================


def test_set_vorschlaege_ersetzt_die_liste():
    """repository.set_vorschlaege ersetzt die komplette Liste (kein Patch
    einzelner Einträge) und gibt die aktualisierte TraitDef zurück."""

    async def lauf():
        trait_id = await _trait_def_id("Diebeshandwerk")
        try:
            vorher = await traits_repository.set_vorschlaege(trait_id, "neotopia", ["Schlösser"])
            assert vorher is not None
            assert vorher["vorschlaege"] == ["Schlösser"]

            nachher = await traits_repository.set_vorschlaege(
                trait_id, "neotopia", ["Tresore", "Sicherheitssysteme"]
            )
            assert nachher["vorschlaege"] == ["Tresore", "Sicherheitssysteme"]

            katalog = await traits_repository.list_catalog("neotopia")
            eintrag = next(t for t in katalog if t["id"] == trait_id)
            assert eintrag["vorschlaege"] == ["Tresore", "Sicherheitssysteme"]
        finally:
            # Seed-Standard wiederherstellen, damit andere Tests (und der
            # nächste Serverstart) nicht auf dieser Teständerung sitzen
            # bleiben — Diebeshandwerk hat laut TRAIT_VORSCHLAEGE keine.
            await traits_repository.set_vorschlaege(trait_id, "neotopia", [])

    _run(lauf())


def test_set_vorschlaege_unbekannte_trait_def_gibt_none():
    async def lauf():
        ergebnis = await traits_repository.set_vorschlaege("neotopia:Fertigkeit:Nicht-Vorhanden", "neotopia", ["x"])
        assert ergebnis is None

    _run(lauf())


def test_set_trait_vorschlaege_route_gm_erfolg():
    """Route-Ebene: GM setzt Vorschläge über die echte Route-Funktion
    (direkter Aufruf, kein TestClient — siehe Moduldocstring dieser Datei
    und test_verbindung_bearbeiten.py für dasselbe Muster im Projekt)."""

    async def lauf():
        from app.traits import routes as traits_routes
        from app.traits.schemas import TraitVorschlaegeUpdate

        cid = await _kampagne_anlegen()
        trait_id = await _trait_def_id("Fahren")
        try:
            antwort = await traits_routes.set_trait_vorschlaege(
                cid, trait_id, TraitVorschlaegeUpdate(vorschlaege=["Motorräder", "  ", "Offroad"])
            )
            # Direkter Funktionsaufruf statt HTTP (siehe Docstring oben):
            # response_model greift nur auf dem echten HTTP-Pfad, hier kommt
            # das rohe Repository-Dict zurück, kein TraitDefResponse-Objekt.
            # Leere/reine Whitespace-Einträge werden herausgefiltert.
            assert antwort["vorschlaege"] == ["Motorräder", "Offroad"]

            katalog = await traits_repository.list_catalog("neotopia")
            eintrag = next(t for t in katalog if t["id"] == trait_id)
            assert eintrag["vorschlaege"] == ["Motorräder", "Offroad"]
        finally:
            await traits_repository.set_vorschlaege(trait_id, "neotopia", [])
            await _aufraeumen(cid)

    _run(lauf())


def test_set_trait_vorschlaege_route_lehnt_attribut_ab():
    """Attribute kennen keine Spezialisierungs-Slots — die Route muss das
    VOR dem Schreiben prüfen (400), nicht erst beim Lesen scheitern."""

    async def lauf():
        from fastapi import HTTPException
        import pytest

        from app.traits import routes as traits_routes
        from app.traits.schemas import TraitVorschlaegeUpdate

        cid = await _kampagne_anlegen()
        trait_id = await _trait_def_id("Körperkraft", "AttributKörperlich")
        try:
            with pytest.raises(HTTPException) as fehler:
                await traits_routes.set_trait_vorschlaege(
                    cid, trait_id, TraitVorschlaegeUpdate(vorschlaege=["Sollte nie ankommen"])
                )
            assert fehler.value.status_code == 400

            # Darf auch nicht als Nebenwirkung doch geschrieben worden sein.
            katalog = await traits_repository.list_catalog("neotopia")
            eintrag = next(t for t in katalog if t["id"] == trait_id)
            assert eintrag["vorschlaege"] == []
        finally:
            await _aufraeumen(cid)

    _run(lauf())


def test_set_trait_vorschlaege_route_erlaubt_sphaere():
    """Sphären kamen am 23.10.2026 dazu — die Route darf sie nicht mehr
    ablehnen, Vorschlagstexte für Sphären-Spezialisierungen sind jetzt
    genauso pflegbar wie für Fertigkeiten."""

    async def lauf():
        from app.traits import routes as traits_routes
        from app.traits.schemas import TraitVorschlaegeUpdate

        cid = await _kampagne_anlegen()
        trait_id = await _trait_def_id("Kräfte", "Sphäre")
        try:
            antwort = await traits_routes.set_trait_vorschlaege(
                cid, trait_id, TraitVorschlaegeUpdate(vorschlaege=["Blitzmagie"])
            )
            assert antwort["vorschlaege"] == ["Blitzmagie"]
        finally:
            await traits_repository.set_vorschlaege(trait_id, "neotopia", [])
            await _aufraeumen(cid)

    _run(lauf())


def test_set_trait_vorschlaege_route_unbekannte_kampagne_ist_404():
    async def lauf():
        from fastapi import HTTPException
        import pytest

        from app.traits import routes as traits_routes
        from app.traits.schemas import TraitVorschlaegeUpdate

        trait_id = await _trait_def_id("Fahren")
        with pytest.raises(HTTPException) as fehler:
            await traits_routes.set_trait_vorschlaege(
                "kampagne-existiert-nicht", trait_id, TraitVorschlaegeUpdate(vorschlaege=["x"])
            )
        assert fehler.value.status_code == 404

    _run(lauf())


def test_route_require_campaign_gm_ist_als_abhaengigkeit_eingehaengt():
    """Strukturelle Gegenprobe zu test_zugriffsschutz.py: diese Route muss
    GM-only sein — nicht erneut per HTTP-403-Test geprüft (dieses Projekt
    nutzt keinen TestClient), sondern wie dort über den Abhängigkeitsbaum."""

    async def check():
        from app.auth.dependencies import require_campaign_gm
        from app.main import app

        gefunden = False
        offen = list(app.routes)
        while offen:
            eintrag = offen.pop()
            unter = getattr(eintrag, "original_router", None)
            if unter is not None:
                offen.extend(unter.routes)
                continue
            if getattr(eintrag, "path", None) == "/api/campaigns/{campaign_id}/traits/{trait_def_id}/vorschlaege":
                gefunden = True

                def wachen(dependant):
                    gefunden_set = set()
                    if dependant.call is not None:
                        gefunden_set.add(dependant.call)
                    for u in dependant.dependencies:
                        gefunden_set |= wachen(u)
                    return gefunden_set

                assert require_campaign_gm in wachen(eintrag.dependant)
        assert gefunden, "Route wurde nicht gefunden — Pfad geändert?"

    _run(check())
