"""Eine Leitung pro Kampagne. Der Ring ist ein einziger Raum, kein Board-Stapel."""

import asyncio
import logging
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.raetsel.logic import fuer_draht

log = logging.getLogger(__name__)


@dataclass
class Verbindung:
    socket: WebSocket
    rolle: str


@dataclass
class Verteiler:
    _je_kampagne: dict[str, list[Verbindung]] = field(default_factory=dict)
    _schloss: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def anmelden(self, campaign_id: str, verbindung: Verbindung) -> None:
        async with self._schloss:
            self._je_kampagne.setdefault(campaign_id, []).append(verbindung)

    async def abmelden(self, campaign_id: str, socket: WebSocket) -> None:
        async with self._schloss:
            offen = self._je_kampagne.get(campaign_id)
            if not offen:
                return
            self._je_kampagne[campaign_id] = [v for v in offen if v.socket is not socket]
            if not self._je_kampagne[campaign_id]:
                del self._je_kampagne[campaign_id]

    async def rundrufen(self, campaign_id: str, zustand: dict) -> None:
        async with self._schloss:
            offen = list(self._je_kampagne.get(campaign_id, []))
        tot: list[WebSocket] = []
        for verbindung in offen:
            try:
                await verbindung.socket.send_json(
                    {"typ": "stand", "daten": fuer_draht(zustand, verbindung.rolle)}
                )
            except Exception:
                log.debug("Leitung weg", exc_info=True)
                tot.append(verbindung.socket)
        for socket in tot:
            await self.abmelden(campaign_id, socket)


verteiler = Verteiler()
