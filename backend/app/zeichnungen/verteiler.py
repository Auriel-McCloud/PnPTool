"""WebSocket-Verwaltung fürs Live-Mitzeichnen, eine Leitungsgruppe pro Board.

Dasselbe Muster wie app/mitteilungen/verteiler.py, aber nach zeichnung_id
statt campaign_id sortiert (mehrere Boards pro Kampagne, jedes mit eigenem
Publikum) und ohne Rückecho an den Absender selbst — der hat seinen eigenen
Stand schon lokal.

Bewusst im Prozessspeicher, gleiche Begründung wie bei den Mitteilungen: ein
Uvicorn-Prozess auf Marks Heimserver, kein Redis-Verteiler nötig.
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
    _je_zeichnung: dict[str, list[Verbindung]] = field(default_factory=dict)
    _schloss: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def anmelden(self, zeichnung_id: str, verbindung: Verbindung) -> None:
        async with self._schloss:
            self._je_zeichnung.setdefault(zeichnung_id, []).append(verbindung)

    async def abmelden(self, zeichnung_id: str, socket: WebSocket) -> None:
        async with self._schloss:
            offen = self._je_zeichnung.get(zeichnung_id)
            if not offen:
                return
            self._je_zeichnung[zeichnung_id] = [v for v in offen if v.socket is not socket]
            if not self._je_zeichnung[zeichnung_id]:
                del self._je_zeichnung[zeichnung_id]

    async def rundrufen(self, zeichnung_id: str, pfade: list[dict], ausser: WebSocket) -> None:
        """Schickt den neuen Gesamtstand an alle außer dem Absender.

        Der Absender hat seinen eigenen Stand schon lokal — ein Rückecho
        würde dort nur unnötig neu rendern (und bei einem laufenden eigenen
        Strich den Zeichenvorgang stören).
        """
        async with self._schloss:
            offen = list(self._je_zeichnung.get(zeichnung_id, []))

        umschlag = {"typ": "pfade", "daten": {"pfade": pfade}}
        tot: list[WebSocket] = []
        for verbindung in offen:
            if verbindung.socket is ausser:
                continue
            try:
                await verbindung.socket.send_json(umschlag)
            except Exception:
                log.debug("Leitung weg, wird entfernt", exc_info=True)
                tot.append(verbindung.socket)

        for socket in tot:
            await self.abmelden(zeichnung_id, socket)

    async def anzahl(self, zeichnung_id: str) -> int:
        async with self._schloss:
            return len(self._je_zeichnung.get(zeichnung_id, []))


verteiler = Verteiler()
