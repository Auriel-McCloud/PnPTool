"""WebSocket-Verteiler für eine Battlemap, eine Leitungsgruppe pro Karte.

Wie zeichnungen/verteiler.py: voller Stand, kein Diff, kein Rückecho.
"""

import asyncio
import logging
from dataclasses import dataclass, field

from fastapi import WebSocket

log = logging.getLogger(__name__)


@dataclass
class Verbindung:
    socket: WebSocket
    rolle: str
    person_id: str | None


@dataclass
class Verteiler:
    _je_karte: dict[str, list[Verbindung]] = field(default_factory=dict)
    _schloss: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def anmelden(self, karte_id: str, verbindung: Verbindung) -> None:
        async with self._schloss:
            self._je_karte.setdefault(karte_id, []).append(verbindung)

    async def abmelden(self, karte_id: str, socket: WebSocket) -> None:
        async with self._schloss:
            offen = self._je_karte.get(karte_id)
            if not offen:
                return
            self._je_karte[karte_id] = [v for v in offen if v.socket is not socket]
            if not self._je_karte[karte_id]:
                del self._je_karte[karte_id]

    async def rundrufen(self, karte_id: str, umschlag: dict, ausser: WebSocket | None = None) -> None:
        async with self._schloss:
            offen = list(self._je_karte.get(karte_id, []))
        tot: list[WebSocket] = []
        for verbindung in offen:
            if ausser is not None and verbindung.socket is ausser:
                continue
            try:
                await verbindung.socket.send_json(umschlag)
            except Exception:
                log.debug("Leitung weg, wird entfernt", exc_info=True)
                tot.append(verbindung.socket)
        for socket in tot:
            await self.abmelden(karte_id, socket)

    async def rundrufen_je(self, karte_id: str, bauen) -> None:
        """Jeder Verbindung ihr eigenes Paket. bauen(verbindung) -> Umschlag."""
        async with self._schloss:
            offen = list(self._je_karte.get(karte_id, []))
        tot: list[WebSocket] = []
        for verbindung in offen:
            try:
                await verbindung.socket.send_json(bauen(verbindung))
            except Exception:
                log.debug("Leitung weg, wird entfernt", exc_info=True)
                tot.append(verbindung.socket)
        for socket in tot:
            await self.abmelden(karte_id, socket)


verteiler = Verteiler()
