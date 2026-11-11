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
    {"typ": "haeufchen", "petId", "x", "y", "art"}   (Anteile 0..1; art haeufchen|brand)
    {"typ": "wegmachen", "id"}
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.pets import logic, repository

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

    def als_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "art": self.art,
            "besitzerId": self.besitzer_id,
            "besitzerName": self.besitzer_name,
            "seite": self.seite,
            "ankunft": self.ankunft,
        }


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
        hier = [p.als_dict() for p in self._pets.get(campaign_id, {}).values() if p.wirt == person_id]
        await self._senden(campaign_id, person_id, {"typ": "pets", "daten": hier})

    async def _haeufchen_senden(self, campaign_id: str, person_id: str) -> None:
        liste = await repository.haeufchen_liste(campaign_id, person_id)
        await self._senden(campaign_id, person_id, {"typ": "haeufchen", "daten": liste})

    # ── Zustand mit der Datenbank abgleichen ───────────────────────────────

    async def abgleich(self, campaign_id: str) -> None:
        """Pets neu einlesen und jedem einen gültigen Wirt geben.

        Läuft bei jedem An-/Abmelden, nach SL-Änderungen und im Takt — so
        greifen neue Pets, Besitzerwechsel und Party-Änderungen ohne Neustart.
        Ein Pet ist nur unterwegs, solange sein Besitzer eingeloggt ist.
        """
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

            for pet_id, d in aus_db.items():
                if d["besitzerId"] not in online:
                    continue
                pet = pets.get(pet_id)
                if pet is None:
                    pet = Pet(id=pet_id, name=d["name"], art=d["art"], besitzer_id=d["besitzerId"],
                              besitzer_name=d["besitzerName"], mitglieder=d["mitglieder"])
                    pets[pet_id] = pet
                    self._ankommen(pet, d["besitzerId"], self.zufall.choice(["links", "rechts"]), jetzt)
                    betroffen.add(d["besitzerId"])
                    continue
                namens_aenderung = (pet.name, pet.art) != (d["name"], d["art"])
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
                    betroffen.add(pet.wirt)
                    self._losschicken(campaign_id, pet, pet.wirt, self.zufall.choice(["links", "rechts"]))
                # Weder auf einem Bildschirm noch unterwegs: wieder einsetzen.
                elif pet.wirt is None and (pet.unterwegs is None or pet.unterwegs.done()):
                    neu = logic.naechster_wirt(logic.online_mitglieder(pet.mitglieder, online), None, self.zufall)
                    if neu:
                        self._ankommen(pet, neu, self.zufall.choice(["links", "rechts"]), jetzt)
                        betroffen.add(neu)

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
            neu = logic.naechster_wirt(kandidaten, von, self.zufall)
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

    async def wegmachen(self, campaign_id: str, person_id: str, haeufchen_id: str) -> None:
        await repository.haeufchen_weg(campaign_id, person_id, haeufchen_id)
        await self._haeufchen_senden(campaign_id, person_id)

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
                except Exception:
                    log.warning("Pet-Abgleich fehlgeschlagen", exc_info=True)


motor = PetMotor()
