"""Wo läuft welches Pet gerade herum? — Server-Zustand und Live-Leitungen.

Mark, 11.11.2026: serverseitig getrackt. Ein Tablet meldet „rechts raus“,
der Server wählt das nächste eingeloggte Party-Mitglied und schickt das Pet
dort nach einer kleinen Pause auf der Gegenseite wieder rein.

Bewusst im Prozessspeicher wie der Mitteilungs-Verteiler: ein Uvicorn-Prozess.
Nach einem Neustart fängt jedes Pet einfach wieder beim Besitzer an.

Protokoll (voller Zustand je Bildschirm, keine Diffs):
  Server → Tablet
    {"typ": "pets", "daten": [{id, name, art, besitzerId, besitzerName, seite, ankunft}]}
        — alle Pets, die GERADE auf diesem Bildschirm sind.
    {"typ": "haeufchen", "daten": [{id, petId, x, y, art}]}
        — alle Spuren (Häufchen, Brandflecken) auf diesem Bildschirm.
  Tablet → Server
    {"typ": "raus", "petId", "seite": "links"|"rechts"}
    {"typ": "haeufchen", "petId", "x", "y", "art"}   (Anteile 0..1; art haeufchen|brand|seite)
    {"typ": "wegmachen", "id"}
    {"typ": "verschieben", "id", "x", "y"}   (Häufchen ist von seinem Element gefallen)
    {"typ": "gelesen", "petId"}   (Bärbels Lesung zugeklappt)
    {"typ": "tippen", "petId"}    (aufs Ei getippt — jeder am Tisch darf)
    {"typ": "streicheln", "petId"}   (Zutraulichkeit +1, höchstens alle 5 Minuten)
    {"typ": "wegmachen", "id", "petId"}  — beim Napf: dieses Pet hat ihn leer gefressen
  Server → Tablet zusätzlich
    {"typ": "vorlesen", "petId", "stelle", "zitat"}
        — Bärbel soll sich aufschlagen. Steht auch am Pet-Dict (`lesung`),
          damit ein Neuverbinden die ungelesene Stelle nicht verliert.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.pets import logic, repository, vorlesen

log = logging.getLogger(__name__)

TAKT_S = 20.0


@dataclass
class Pet:
    id: str
    name: str
    art: str
    besitzer_id: str
    besitzer_name: str
    mitglieder: list[str]
    wirt: str | None = None
    seite: str = "links"
    seit: float = 0.0
    # Zählt jede Ankunft hoch — das Tablet erkennt daran einen neuen Auftritt.
    ankunft: int = 0
    unterwegs: asyncio.Task | None = None
    # Wachstum (12.11.2026): ei | baby | jung, freigeschaltete Fähigkeiten, Risse im Ei.
    stufe: str = "jung"
    kann: list[str] = field(default_factory=lambda: list(logic.ALLE_FAEHIGKEITEN))
    risse: int = 0
    # Drachenperle (13.11.2026): wo sie liegt (aus der DB), wer sie geworfen hat,
    # wem er sie gerade zurückbringt, und welche Tablets er schon abgesucht hat.
    perle_ort: str | None = None
    perle_von: str | None = None
    bringt_zu: str | None = None
    gesucht: set[str] = field(default_factory=set)
    # Feuerball: wann er zuletzt einen aufs Nachbar-Tablet geschossen hat.
    feuerball_zuletzt: float = -1e9

    def perle_modus(self) -> str | None:
        """Was das Tablet über die Perle wissen muss — nie, WO sie liegt."""
        if self.bringt_zu:
            return "zurueck" if self.wirt == self.bringt_zu else "bringt"
        if self.perle_ort is None:
            return None
        if self.perle_ort != self.wirt:
            return "sucht"
        return "gefunden" if self.perle_von else "spiel"

    def als_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "art": self.art,
            "besitzerId": self.besitzer_id,
            "besitzerName": self.besitzer_name,
            "seite": self.seite,
            "ankunft": self.ankunft,
            "stufe": self.stufe,
            "kann": self.kann,
            "risse": self.risse,
            "perle": self.perle_modus(),
        }

    def wachstum_uebernehmen(self, d: dict) -> bool:
        """Stufe/Fähigkeiten/Risse aus der DB. True = hat sich etwas geändert."""
        neu = (d.get("stufe", "jung"), list(d.get("kann", logic.ALLE_FAEHIGKEITEN)), int(d.get("risse", 0)))
        alt = (self.stufe, self.kann, self.risse)
        self.stufe, self.kann, self.risse = neu
        return neu != alt


@dataclass
class PetMotor:
    _leitungen: dict[str, dict[str, list[WebSocket]]] = field(default_factory=dict)
    _pets: dict[str, dict[str, Pet]] = field(default_factory=dict)
    _schloss: asyncio.Lock = field(default_factory=asyncio.Lock)
    _takt: asyncio.Task | None = None
    zufall: random.Random = field(default_factory=random.Random)
    # In Tests auf 0 setzen, damit niemand Sekunden wartet.
    pause_min: float = logic.UNTERWEGS_MIN_S
    pause_max: float = logic.UNTERWEGS_MAX_S
    # Lesung: nur Anwesenheit zählt, nicht die Wanduhr (Mark: „nicht permanent“).
    lesen_min: float = vorlesen.LESEN_MIN_S
    lesen_max: float = vorlesen.LESEN_MAX_S
    _spuren_weg: dict[str, bool] = field(default_factory=dict)
    # Feuerbälle, die gerade auf ein anderes Tablet fliegen (Aufgaben festhalten).
    feuerball_flug: float = logic.FEUERBALL_FLUG_S
    _einschlaege: set[asyncio.Task] = field(default_factory=set)
    _lesen: dict[str, dict[str, "Lesen"]] = field(default_factory=dict)

    # ── Leitungen ──────────────────────────────────────────────────────────

    def online(self, campaign_id: str) -> set[str]:
        return {p for p, socks in self._leitungen.get(campaign_id, {}).items() if socks}

    async def anmelden(self, campaign_id: str, person_id: str, socket: WebSocket) -> None:
        async with self._schloss:
            self._leitungen.setdefault(campaign_id, {}).setdefault(person_id, []).append(socket)
        await self._haeufchen_senden(campaign_id, person_id)
        await self.abgleich(campaign_id)
        # Wer neu dazukommt, bekommt seinen Stand auch, wenn sich nichts geändert hat.
        await self._pets_senden(campaign_id, person_id)
        self._takt_starten()

    async def abmelden(self, campaign_id: str, person_id: str, socket: WebSocket) -> None:
        async with self._schloss:
            je_person = self._leitungen.get(campaign_id, {})
            je_person[person_id] = [s for s in je_person.get(person_id, []) if s is not socket]
            if not je_person.get(person_id):
                je_person.pop(person_id, None)
            if not je_person:
                self._leitungen.pop(campaign_id, None)
        await self.abgleich(campaign_id)

    async def _senden(self, campaign_id: str, person_id: str, umschlag: dict) -> None:
        for socket in list(self._leitungen.get(campaign_id, {}).get(person_id, [])):
            try:
                await socket.send_json(umschlag)
            except Exception:
                log.debug("Pet-Leitung weg", exc_info=True)

    async def _pets_senden(self, campaign_id: str, person_id: str) -> None:
        hier = [self._als_dict(campaign_id, p) for p in self._pets.get(campaign_id, {}).values() if p.wirt == person_id]
        await self._senden(campaign_id, person_id, {"typ": "pets", "daten": hier})

    async def _haeufchen_senden(self, campaign_id: str, person_id: str) -> None:
        # Kampf oder abgedreht: Spuren ausblenden, nicht löschen (Mark, 11.11.).
        if await repository.pets_pausiert(campaign_id):
            await self._senden(campaign_id, person_id, {"typ": "haeufchen", "daten": []})
            return
        liste = await repository.haeufchen_liste(campaign_id, person_id)
        await self._senden(campaign_id, person_id, {"typ": "haeufchen", "daten": liste})

    async def _spuren_nach_pause(self, campaign_id: str, pausiert: bool) -> None:
        vorher = self._spuren_weg.get(campaign_id)
        self._spuren_weg[campaign_id] = pausiert
        if vorher is None or vorher == pausiert:
            return
        for person_id in list(self.online(campaign_id)):
            await self._haeufchen_senden(campaign_id, person_id)

    # ── Zustand mit der Datenbank abgleichen ───────────────────────────────

    async def abgleich(self, campaign_id: str) -> None:
        """Pets neu einlesen und jedem einen gültigen Wirt geben.

        Läuft bei jedem An-/Abmelden, nach SL-Änderungen und im Takt — so
        greifen neue Pets, Besitzerwechsel und Party-Änderungen ohne Neustart.
        Ein Pet ist nur unterwegs, solange sein Besitzer eingeloggt ist.
        """
        # Abgedreht oder Kampf: alle Pets verschwinden (und kommen danach beim
        # Besitzer wieder) — wie ein Pet, das es gerade nicht gibt.
        pausiert = await repository.pets_pausiert(campaign_id)
        await self._spuren_nach_pause(campaign_id, pausiert)
        if pausiert:
            aus_db: dict[str, dict] = {}
        else:
            aus_db = {d["id"]: d for d in await repository.pets_der_kampagne(campaign_id)}
        betroffen: set[str] = set()
        async with self._schloss:
            online = self.online(campaign_id)
            pets = self._pets.setdefault(campaign_id, {})
            jetzt = time.monotonic()

            for pet_id in list(pets):
                d = aus_db.get(pet_id)
                if d is None or d["besitzerId"] not in online:
                    alt = pets.pop(pet_id)
                    if alt.unterwegs:
                        alt.unterwegs.cancel()
                    if alt.wirt:
                        betroffen.add(alt.wirt)
                    # Pause behält die ungelesene Lesung; weggeworfenes Buch nicht.
                    if not pausiert and d is None:
                        self._lesen.get(campaign_id, {}).pop(pet_id, None)

            for pet_id, d in aus_db.items():
                if d["besitzerId"] not in online:
                    continue
                pet = pets.get(pet_id)
                if pet is None:
                    pet = Pet(id=pet_id, name=d["name"], art=d["art"], besitzer_id=d["besitzerId"],
                              besitzer_name=d["besitzerName"], mitglieder=d["mitglieder"])
                    pet.wachstum_uebernehmen(d)
                    pets[pet_id] = pet
                    self._ankommen(pet, d["besitzerId"], self.zufall.choice(["links", "rechts"]), jetzt)
                    betroffen.add(d["besitzerId"])
                    continue
                namens_aenderung = (pet.name, pet.art) != (d["name"], d["art"])
                namens_aenderung = pet.wachstum_uebernehmen(d) or namens_aenderung
                pet.name, pet.art, pet.mitglieder = d["name"], d["art"], d["mitglieder"]
                pet.besitzer_id, pet.besitzer_name = d["besitzerId"], d["besitzerName"]
                if pet.wirt and namens_aenderung:
                    betroffen.add(pet.wirt)
                # Wirt weg (ausgeloggt, Party verlassen)? Dann zieht es um.
                if pet.wirt and pet.wirt not in logic.online_mitglieder(pet.mitglieder, online):
                    betroffen.add(pet.wirt)
                    neu = logic.naechster_wirt(logic.online_mitglieder(pet.mitglieder, online), pet.wirt, self.zufall)
                    pet.wirt = None
                    if neu:
                        self._ankommen(pet, neu, self.zufall.choice(["links", "rechts"]), jetzt)
                        betroffen.add(neu)
                # Ein Tablet, das sich nie meldet, hält das Pet nicht ewig fest.
                elif pet.wirt and jetzt - pet.seit > logic.HOECHSTE_VERWEILDAUER_S:
                    # Beim Besitzer wartet eine Lesung: bleiben. Woanders nicht —
                    # dann muss sie ja gerade heim. Ein Ei bleibt beim Besitzer liegen.
                    if pet.stufe == "ei" or (self._hat_lesung(campaign_id, pet.id) and pet.wirt == pet.besitzer_id):
                        pet.seit = jetzt
                    else:
                        betroffen.add(pet.wirt)
                        self._losschicken(campaign_id, pet, pet.wirt, self.zufall.choice(["links", "rechts"]))
                # Weder auf einem Bildschirm noch unterwegs: wieder einsetzen.
                elif pet.wirt is None and (pet.unterwegs is None or pet.unterwegs.done()):
                    neu = self._ziel(campaign_id, pet, logic.online_mitglieder(pet.mitglieder, online), None)
                    if neu:
                        self._ankommen(pet, neu, self.zufall.choice(["links", "rechts"]), jetzt)
                        betroffen.add(neu)

        # Erst die Perlen (neue Pets wissen sonst nicht, dass ihre irgendwo liegt).
        await self._perlen_abgleich(campaign_id, None if pausiert else set(aus_db))
        for person_id in betroffen:
            await self._pets_senden(campaign_id, person_id)

    def _ankommen(self, pet: Pet, wirt: str, seite: str, jetzt: float) -> None:
        pet.wirt = wirt
        pet.seite = seite
        pet.seit = jetzt
        pet.ankunft += 1

    def _losschicken(self, campaign_id: str, pet: Pet, von: str, raus_seite: str) -> None:
        """Pet verlässt `von`; nach einer Pause taucht es woanders auf. Unter dem Schloss aufrufen."""
        pet.wirt = None
        if pet.unterwegs:
            pet.unterwegs.cancel()
        pause = self.zufall.uniform(self.pause_min, self.pause_max)
        pet.unterwegs = asyncio.create_task(self._ankunft_nach(campaign_id, pet.id, von, raus_seite, pause))

    async def _ankunft_nach(self, campaign_id: str, pet_id: str, von: str, raus_seite: str, pause: float) -> None:
        await asyncio.sleep(pause)
        async with self._schloss:
            pet = self._pets.get(campaign_id, {}).get(pet_id)
            if pet is None or pet.wirt is not None:
                return
            pet.unterwegs = None
            kandidaten = logic.online_mitglieder(pet.mitglieder, self.online(campaign_id))
            neu = self._ziel(campaign_id, pet, kandidaten, von)
            if neu is None:
                return
            self._ankommen(pet, neu, logic.gegenseite(raus_seite), time.monotonic())
        await self._pets_senden(campaign_id, neu)

    # ── Meldungen vom Tablet ───────────────────────────────────────────────

    async def raus(self, campaign_id: str, person_id: str, pet_id: str, seite: str) -> None:
        async with self._schloss:
            pet = self._pets.get(campaign_id, {}).get(pet_id)
            # Nur wer das Pet gerade hat, darf es losschicken.
            if pet is None or pet.wirt != person_id:
                return
            self._losschicken(campaign_id, pet, person_id, "rechts" if seite == "rechts" else "links")
        await self._pets_senden(campaign_id, person_id)

    async def haeufchen(self, campaign_id: str, person_id: str, pet_id: str, x: float, y: float,
                        art: str = "haeufchen") -> None:
        pet = self._pets.get(campaign_id, {}).get(pet_id)
        if pet is None or pet.wirt != person_id or art not in logic.SPUR_ARTEN:
            return
        await repository.haeufchen_anlegen(campaign_id, person_id, pet_id, logic.anteil(x), logic.anteil(y), art)
        await self._haeufchen_senden(campaign_id, person_id)

    async def tippen(self, campaign_id: str, person_id: str, pet_id: str) -> None:
        """Aufs Ei getippt (jeder, auf dessen Bildschirm es liegt). Neuer Riss
        oder geschlüpft — der neue Stand geht an diesen Bildschirm."""
        pet = self._pets.get(campaign_id, {}).get(pet_id)
        if pet is None or pet.wirt != person_id or pet.stufe != "ei":
            return
        await repository.ei_tippen(campaign_id, pet_id)
        await self.abgleich(campaign_id)
        await self._pets_senden(campaign_id, person_id)

    async def verschieben(self, campaign_id: str, person_id: str, haeufchen_id: str, x: float, y: float) -> None:
        await repository.haeufchen_verschieben(campaign_id, person_id, haeufchen_id, logic.anteil(x), logic.anteil(y))
        await self._haeufchen_senden(campaign_id, person_id)

    async def wegmachen(self, campaign_id: str, person_id: str, haeufchen_id: str, pet_id: str | None = None) -> None:
        spur = await repository.haeufchen_lesen(campaign_id, person_id, haeufchen_id)
        if spur and spur["art"] == logic.NAPF:
            # Ein Napf verschwindet nur, wenn ein Drache auf diesem Bildschirm ihn
            # leer frisst — nicht durch Antippen.
            pet = self._pets.get(campaign_id, {}).get(pet_id or "")
            if pet is None or pet.wirt != person_id or not logic.ist_drache(pet.art) or pet.stufe == "ei":
                return
            await repository.haeufchen_weg(campaign_id, person_id, haeufchen_id)
            await repository.critter_heilen(campaign_id, pet.id, logic.NAPF_HEILUNG)
            # Der Napf steht auf dem Bildschirm dessen, der gefüttert hat.
            await repository.zutraulichkeit_erhoehen(campaign_id, person_id, pet.id, logic.ZUTRAULICH_FUETTERN)
        elif spur and spur["art"] == logic.PERLE:
            # Die Perle steckt nur ihr Drache wieder ein, und nur, wo er gerade ist —
            # Antippen lässt sie hüpfen, nicht verschwinden.
            p = await repository.perle_lesen(campaign_id, haeufchen_id)
            pet = self._pets.get(campaign_id, {}).get(p["petId"]) if p else None
            if pet is None or pet.wirt != person_id:
                return
            await repository.perle_weg(campaign_id, haeufchen_id)
            await self._haeufchen_senden(campaign_id, person_id)
            # Sofort abgleichen: sonst hielte er sie bis zum nächsten Takt für
            # verloren und liefe auf dem nächsten Tablet suchend herum.
            await self._perlen_abgleich(campaign_id)
            return
        else:
            await repository.haeufchen_weg(campaign_id, person_id, haeufchen_id)
        await self._haeufchen_senden(campaign_id, person_id)

    async def sauber(self, campaign_id: str) -> int:
        """SL-Knopf (Mark, 13.11.2026): alle Spuren der Kampagne weg, jedes
        verbundene Tablet bekommt sofort seine (leere) Liste. Näpfe bleiben."""
        n = await repository.spuren_alle_weg(campaign_id)
        for person_id in list(self.online(campaign_id)):
            await self._haeufchen_senden(campaign_id, person_id)
        await self._perlen_abgleich(campaign_id)
        return n

    # ── Drachenperle (Mark, 13.11.2026) ────────────────────────────────────

    async def _perlen_abgleich(self, campaign_id: str, bekannt: set[str] | None = None) -> None:
        """Wo liegen die Perlen? Aus der DB, damit ein Neustart nichts vergisst.
        Wessen Stand sich ändert, dessen Tablet bekommt ihn neu.

        `bekannt` = alle Pets der Kampagne (nur beim großen Abgleich): Perlen,
        deren Drache es nicht mehr gibt, verschwinden."""
        liegen = await repository.perlen(campaign_id)
        online = self.online(campaign_id)
        pets = self._pets.get(campaign_id, {})
        neu_senden: set[str] = set()
        for pet_id, p in list(liegen.items()):
            pet = pets.get(pet_id)
            verwaist = (bekannt is not None and pet_id not in bekannt) or (pet is not None and logic.PERLE not in pet.kann)
            if verwaist:
                # Drache weg oder (SL hat die Stufe zurückgestellt) zu jung für die Perle.
                await repository.perle_weg(campaign_id, p["id"])
                neu_senden.add(p["personId"])
                del liegen[pet_id]
                continue
            if pet is None:
                continue  # Besitzer nicht da — sie bleibt liegen, bis der Drache wiederkommt
            kreis = logic.online_mitglieder(pet.mitglieder, online)
            if kreis and p["personId"] not in kreis:
                # Das Tablet, auf dem sie liegt, ist aus: dort fände er sie nie.
                # Sie kullert auf ein anderes weiter, das an ist.
                ziel = logic.perle_ziel(kreis, p["personId"], self.zufall)
                await repository.perle_umlegen(campaign_id, p["id"], ziel, self.zufall.uniform(0.2, 0.8), p["von"])
                p["personId"] = ziel
                pet.gesucht.clear()
                neu_senden.add(ziel)
        for person_id in neu_senden & online:
            await self._haeufchen_senden(campaign_id, person_id)
        betroffen: set[str] = set()
        for pet in self._pets.get(campaign_id, {}).values():
            vorher = pet.perle_modus()
            p = liegen.get(pet.id)
            pet.perle_ort, pet.perle_von = (p["personId"], p["von"]) if p else (None, None)
            if pet.perle_ort is None:
                pet.gesucht.clear()
            if pet.wirt and pet.perle_modus() != vorher:
                betroffen.add(pet.wirt)
        for person_id in betroffen:
            await self._pets_senden(campaign_id, person_id)

    async def perle(self, campaign_id: str, person_id: str, pet_id: str, x: float) -> None:
        """Der Drache holt seine Perle heraus oder legt die zurückgebrachte ab —
        nur auf dem Tablet, auf dem er gerade ist, und nur, wenn sie nicht
        schon irgendwo liegt."""
        pet = self._pets.get(campaign_id, {}).get(pet_id)
        if pet is None or pet.wirt != person_id or logic.PERLE not in pet.kann:
            return
        if pet.perle_ort is not None and not pet.bringt_zu:
            return
        pet.bringt_zu = None
        pet.gesucht.clear()
        await repository.perle_legen(campaign_id, person_id, pet_id, logic.anteil(x))
        await self._haeufchen_senden(campaign_id, person_id)
        await self._perlen_abgleich(campaign_id)
        await self._pets_senden(campaign_id, person_id)

    async def perle_wurf(self, campaign_id: str, person_id: str, perle_id: str) -> None:
        """Jemand hat die Perle aus seinem Bildschirm geworfen: sie landet auf
        einem zufälligen anderen Tablet der Party. Wirft sie dem Drachen weg,
        wer ihn gerade bei sich hat, bringt er sie genau dem zurück; wer sie nur
        weiterwirft, ändert daran nichts."""
        p = await repository.perle_lesen(campaign_id, perle_id)
        if p is None or p["personId"] != person_id:
            return
        pet = self._pets.get(campaign_id, {}).get(p["petId"])
        online = self.online(campaign_id)
        kreis = logic.online_mitglieder(pet.mitglieder, online) if pet else sorted(online)
        ziel = logic.perle_ziel(kreis, person_id, self.zufall)
        von = person_id if (pet and pet.wirt == person_id) or not p["von"] else p["von"]
        await repository.perle_umlegen(campaign_id, perle_id, ziel, self.zufall.uniform(0.2, 0.8), von)
        if pet:
            pet.gesucht.clear()
        for wer in {person_id, ziel}:
            await self._haeufchen_senden(campaign_id, wer)
        await self._perlen_abgleich(campaign_id)

    async def perle_gefunden(self, campaign_id: str, person_id: str, pet_id: str, perle_id: str) -> None:
        """Der Drache hebt die Perle auf dem Tablet auf, auf dem er sie gefunden
        hat, und bringt sie dem Werfer zurück (ist der weg: dem Besitzer)."""
        pet = self._pets.get(campaign_id, {}).get(pet_id)
        p = await repository.perle_lesen(campaign_id, perle_id)
        if pet is None or pet.wirt != person_id or p is None or p["personId"] != person_id or p["petId"] != pet_id:
            return
        kreis = logic.online_mitglieder(pet.mitglieder, self.online(campaign_id))
        pet.bringt_zu = next((w for w in (p["von"], pet.besitzer_id, person_id) if w in kreis), person_id)
        await repository.perle_weg(campaign_id, perle_id)
        await self._haeufchen_senden(campaign_id, person_id)
        await self._perlen_abgleich(campaign_id)
        await self._pets_senden(campaign_id, person_id)

    # ── Feuerball (Mark, 13.11.2026) ───────────────────────────────────────

    async def feuerball(self, campaign_id: str, person_id: str, pet_id: str, seite: str) -> None:
        """Der Feuerball ist über den Rand hinausgeflogen: er kommt auf einem
        anderen Tablet der Party herein (Gegenseite) und schlägt dort ein.
        Ist sonst niemand da, verpufft er."""
        pet = self._pets.get(campaign_id, {}).get(pet_id)
        jetzt = time.monotonic()
        if pet is None or pet.wirt != person_id or logic.FEUERBALL not in pet.kann:
            return
        if jetzt - pet.feuerball_zuletzt < logic.FEUERBALL_ABKLINGEN_S or await repository.pets_pausiert(campaign_id):
            return
        kreis = logic.online_mitglieder(pet.mitglieder, self.online(campaign_id))
        ziel = logic.perle_ziel(kreis, person_id, self.zufall)
        if ziel == person_id:
            return
        pet.feuerball_zuletzt = jetzt
        x, y = self.zufall.uniform(0.25, 0.75), self.zufall.uniform(0.45, 0.9)
        await self._senden(campaign_id, ziel, {
            "typ": "feuerball", "art": pet.art, "x": x, "y": y,
            "seite": logic.gegenseite("rechts" if seite == "rechts" else "links"),
            "ms": int(logic.FEUERBALL_FLUG_S * 1000),
        })
        aufgabe = asyncio.create_task(self._feuerball_einschlag(campaign_id, ziel, pet_id, pet.art, x, y))
        self._einschlaege.add(aufgabe)
        aufgabe.add_done_callback(self._einschlaege.discard)

    async def _feuerball_einschlag(self, campaign_id: str, ziel: str, pet_id: str, art: str, x: float, y: float) -> None:
        await asyncio.sleep(self.feuerball_flug)
        await repository.haeufchen_anlegen(campaign_id, ziel, pet_id, logic.anteil(x), logic.anteil(y),
                                           logic.feuerball_spur(art))
        await self._haeufchen_senden(campaign_id, ziel)

    async def napf_hinstellen(self, campaign_id: str, person_id: str) -> None:
        """Futternapf unten auf den eigenen Bildschirm, irgendwo in der Mitte."""
        x = self.zufall.uniform(0.15, 0.85)
        await repository.haeufchen_anlegen(campaign_id, person_id, "", x, 1.0, logic.NAPF)
        await self._haeufchen_senden(campaign_id, person_id)

    async def streicheln(self, campaign_id: str, person_id: str, pet_id: str) -> None:
        """Zutraulichkeit +1 — nur wer das Pet gerade auf dem Schirm hat."""
        pet = self._pets.get(campaign_id, {}).get(pet_id)
        if pet is None or pet.wirt != person_id or pet.stufe == "ei":
            return
        await repository.zutraulichkeit_erhoehen(campaign_id, person_id, pet_id, logic.ZUTRAULICH_STREICHELN,
                                                 logic.STREICHEL_ABKLINGEN_S)

    # ── Takt ───────────────────────────────────────────────────────────────

    def _takt_starten(self) -> None:
        if self._takt is None or self._takt.done():
            self._takt = asyncio.create_task(self._takt_schleife())

    async def _takt_schleife(self) -> None:
        while self._leitungen:
            await asyncio.sleep(TAKT_S)
            for campaign_id in list(self._leitungen):
                try:
                    await self.abgleich(campaign_id)
                    await self.lesen_takt(campaign_id, TAKT_S)
                except Exception:
                    log.warning("Pet-Abgleich fehlgeschlagen", exc_info=True)


@dataclass
class Lesen:
    """Ungelesene Stelle überlebt die Kampfpause (das Pet selbst wird dann verworfen)."""
    anwesenheit_s: float = 0.0
    warten_s: float = 0.0
    text: dict | None = None


def _petmotor_lesen_warte(self) -> float:
    if self.lesen_max <= self.lesen_min:
        return self.lesen_min
    return self.zufall.uniform(self.lesen_min, self.lesen_max)


def _petmotor_lesen(self, campaign_id: str, pet_id: str) -> bool:
    st = self._lesen.get(campaign_id, {}).get(pet_id)
    return bool(st and st.text)


def _petmotor_als_dict(self, campaign_id: str, pet: Pet) -> dict:
    d = pet.als_dict()
    st = self._lesen.get(campaign_id, {}).get(pet.id)
    if st and st.text:
        # Bibelverse nur beim Besitzer (Mark, 12.11.2026: „Für die Bibelzitate
        # soll Bärbel immer zu ihrem Besitzer zurückkehren“). Woanders weiß das
        # Tablet nur: sie will heim und fliegt bald raus.
        if pet.wirt == pet.besitzer_id:
            d["lesung"] = st.text
        else:
            d["heim"] = True
    return d


def _petmotor_ziel(self, campaign_id: str, pet: Pet, kandidaten: list[str], von: str | None) -> str | None:
    """Nächstes Tablet. Wartet eine Lesung, geht es direkt zum Besitzer; ein
    Ei wandert nicht, es liegt beim Besitzer."""
    if (pet.stufe == "ei" or self._hat_lesung(campaign_id, pet.id)) and pet.besitzer_id in kandidaten:
        return pet.besitzer_id
    # Drachenperle: mit der gefundenen Perle direkt zum Werfer; sonst suchen —
    # ohne zu wissen, wo sie liegt: ein Tablet nach dem anderen, keins doppelt.
    if pet.bringt_zu:
        if pet.bringt_zu not in kandidaten:
            pet.bringt_zu = pet.besitzer_id if pet.besitzer_id in kandidaten else None
        if pet.bringt_zu:
            return pet.bringt_zu
    if pet.perle_ort is not None:
        if von:
            pet.gesucht.add(von)
        return logic.such_ziel(kandidaten, von, pet.gesucht, self.zufall)
    return logic.naechster_wirt(kandidaten, von, self.zufall)


async def _petmotor_lesen_takt(self, campaign_id: str, sekunden: float) -> None:
    """15 Minuten Anwesenheit, nicht Wanduhr. Im Kampf steht die Uhr."""
    if sekunden <= 0 or await repository.pets_pausiert(campaign_id):
        return
    if not self.online(campaign_id):
        return
    for pet in list(self._pets.get(campaign_id, {}).values()):
        if pet.art != "baerbel" or not pet.wirt:
            continue
        je = self._lesen.setdefault(campaign_id, {})
        st = je.get(pet.id)
        if st is None:
            st = Lesen(warten_s=self._lesen_warte())
            je[pet.id] = st
        if st.text:
            continue
        st.anwesenheit_s += sekunden
        if st.anwesenheit_s < st.warten_s:
            continue
        # Ohne Besitzer keine Bibelstelle — die Zeit läuft weiter auf.
        if pet.besitzer_id not in self.online(campaign_id):
            continue
        st.text = await vorlesen.erzeugen(campaign_id, pet.besitzer_id, list(self.online(campaign_id)))
        st.anwesenheit_s = 0.0
        st.warten_s = self._lesen_warte()
        if pet.wirt == pet.besitzer_id:
            await self._senden(campaign_id, pet.wirt, {"typ": "vorlesen", "petId": pet.id, **st.text})
        # Sonst bekommt das fremde Tablet nur `heim` und lässt sie rausfliegen;
        # beim Besitzer kommt die Lesung mit der Ankunft (`lesung` im Pet).
        await self._pets_senden(campaign_id, pet.wirt)


async def _petmotor_gelesen(self, campaign_id: str, person_id: str, pet_id: str) -> None:
    pet = self._pets.get(campaign_id, {}).get(pet_id)
    if pet is None or pet.wirt != person_id:
        return
    st = self._lesen.get(campaign_id, {}).get(pet_id)
    if st:
        st.text = None
        st.anwesenheit_s = 0.0
    await self._pets_senden(campaign_id, person_id)


PetMotor._lesen_warte = _petmotor_lesen_warte
PetMotor._hat_lesung = _petmotor_lesen
PetMotor._als_dict = _petmotor_als_dict
PetMotor._ziel = _petmotor_ziel
PetMotor.lesen_takt = _petmotor_lesen_takt
PetMotor.gelesen = _petmotor_gelesen


motor = PetMotor()
