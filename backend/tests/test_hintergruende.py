"""Narrativer Hintergrund-Katalog: Seed ohne Mentor/Kontakte."""

import asyncio
import uuid

from app.db.neo4j_driver import get_driver
from app.hintergruende import repository as hintergruende_repository
from app.hintergruende.seed import NARRATIVE_SEED, SYSTEM_HINTERGRUENDE, SYSTEM_SCHLUESSEL
from app.traits.erstellung import pruefe, regelwerk


def _run(coro):
    return asyncio.run(coro)


async def _kampagne_anlegen() -> str:
    cid = f"test-hintergruende-{uuid.uuid4()}"
    driver = get_driver()
    async with driver.session() as session:
        await session.run("CREATE (c:Campaign {id: $cid, name: 'Hintergruende-Test'})", cid=cid)
    return cid


async def _aufraeumen(cid: str) -> None:
    driver = get_driver()
    async with driver.session() as session:
        await session.run("MATCH (n {campaignId: $cid}) DETACH DELETE n", cid=cid)


async def _trait_def_existiert(name: str) -> bool:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (t:TraitDef {id: $id}) RETURN t.id AS id",
            id=f"neotopia:Hintergrund:{name}",
        )
        return await result.single() is not None


def test_seed_laesst_systemhintergruende_weg():
    namen = {eintrag["name"] for eintrag in NARRATIVE_SEED}
    assert "Mentor" not in namen
    assert "Kontakte" not in namen
    assert "Schulden" not in namen
    assert "Straßenruf" in namen
    assert "Ressourcen" in namen


def test_systemschluessel_sind_mentor_kontakte_schulden():
    assert SYSTEM_SCHLUESSEL == ("MENTOR", "KONTAKTE", "SCHULDEN")


def test_system_hintergruende_decken_alle_systemschluessel_ab():
    """Jeder SYSTEM_SCHLUESSEL braucht genau einen Metadaten-Eintrag mit
    Name, Beschreibung und einer gültigen Einstellung zum Umschalten."""
    schluessel = {eintrag["schluessel"] for eintrag in SYSTEM_HINTERGRUENDE}
    assert schluessel == set(SYSTEM_SCHLUESSEL)
    for eintrag in SYSTEM_HINTERGRUENDE:
        assert eintrag["name"]
        assert eintrag["beschreibung"]
        assert eintrag["einstellung"].endswith("Aktiv")


# --- Baukasten-Sync-Fix (13.10.2026, Marks Bugreport) --------------------
# Vorher liefen HintergruendeVerwaltung.tsx (Baukasten, diese Datei) und die
# Charaktererstellung (traits/erstellung.py::HINTERGRUENDE) komplett
# auseinander: ein im Menü angelegter/gelöschter Hintergrund tauchte in der
# Erstellung nie auf bzw. verschwand nie. Diese Tests decken den
# tatsächlichen Datenfluss ab: Baukasten-CRUD → pool_fuer_erstellung() →
# regelwerk()/pruefe().


def test_pool_fuer_erstellung_enthaelt_narrativen_katalog_und_aktive_mechanik():
    async def run():
        cid = await _kampagne_anlegen()
        try:
            angelegt = await hintergruende_repository.anlegen(cid, {"name": "Yakuza-Kontakt"})
            pool = await hintergruende_repository.pool_fuer_erstellung(cid, {})
            namen = {h["name"] for h in pool}
            # Narrativer Seed plus der frisch angelegte Eintrag ...
            assert "Yakuza-Kontakt" in namen
            assert "Ressourcen" in namen
            # ... plus die aktiven Mechanik-Hintergründe, aber nicht Schulden
            # (das ist kein Pool-Eintrag, siehe regelwerk()-Docstring).
            assert "Mentor" in namen
            assert "Kontakte" in namen
            assert "Schulden" not in namen

            # Deaktivierter Mentor fliegt aus dem Pool, Kontakte bleibt.
            pool_ohne_mentor = await hintergruende_repository.pool_fuer_erstellung(
                cid, {"mentorAktiv": False}
            )
            namen_ohne_mentor = {h["name"] for h in pool_ohne_mentor}
            assert "Mentor" not in namen_ohne_mentor
            assert "Kontakte" in namen_ohne_mentor

            # Löschen aus dem Baukasten nimmt den Eintrag aus dem Pool —
            # das war der eigentliche Bugreport.
            await hintergruende_repository.loeschen(cid, angelegt["id"])
            pool_danach = await hintergruende_repository.pool_fuer_erstellung(cid, {})
            assert "Yakuza-Kontakt" not in {h["name"] for h in pool_danach}
        finally:
            await _aufraeumen(cid)

    _run(run())


def test_anlegen_sichert_sofort_den_traitdef_fuer_set_ratings_bulk():
    """Ohne diesen TraitDef verschwinden Punkte auf einem frisch im
    Baukasten angelegten Hintergrund beim Einreichen der Erstellung
    stillschweigend (set_ratings_bulk matcht per Name gegen TraitDef)."""

    async def run():
        cid = await _kampagne_anlegen()
        try:
            name = f"Exotischer Hintergrund {uuid.uuid4().hex[:8]}"
            assert not await _trait_def_existiert(name)
            await hintergruende_repository.anlegen(cid, {"name": name})
            assert await _trait_def_existiert(name)
        finally:
            await _aufraeumen(cid)

    _run(run())


def test_regelwerk_nutzt_den_uebergebenen_pool_statt_der_fest_verdrahteten_liste():
    pool = [{"name": "Hausmacht", "beschreibung": "Ein eigenes Revier."}]
    ergebnis = regelwerk(hintergrund_pool=pool)
    assert ergebnis["hintergruende"] == pool


def test_regelwerk_faellt_ohne_pool_auf_die_alte_liste_zurueck():
    ergebnis = regelwerk()
    namen = {h["name"] for h in ergebnis["hintergruende"]}
    assert "Kontakte" in namen  # alte fest verdrahtete HINTERGRUENDE-Liste


def test_pruefe_lehnt_unbekannten_hintergrund_mit_eigenem_pool_ab():
    from tests.test_erstellung import KATALOG, grundgeruest

    pool = [{"name": "Hausmacht", "beschreibung": "x"}]
    auswahl = grundgeruest(hintergrundPunkte={"Ressourcen": 3})
    fehler = pruefe(auswahl, KATALOG, hintergrund_pool=pool)
    assert any("Ressourcen" in f for f in fehler)

    auswahl_gueltig = grundgeruest(hintergrundPunkte={"Hausmacht": 3})
    fehler_gueltig = pruefe(auswahl_gueltig, KATALOG, hintergrund_pool=pool)
    assert not any("Unbekannter Hintergrund" in f for f in fehler_gueltig)
