"""WebSocket-Verwaltung für die Live-Zustellung.

Hält offene Verbindungen je Kampagne und schickt eine neue Mitteilung sofort
an alle, die sie sehen dürfen. Wer nicht verbunden ist, verpasst nichts —
die Mitteilung liegt in der Datenbank und wird beim nächsten Verbinden
nachgeladen (siehe repository.list_mitteilungen).

Bewusst im Prozessspeicher: PnPTool läuft als ein Uvicorn-Prozess auf Marks
Heimserver. Für mehrere Arbeiter bräuchte es Redis o.ä. als Verteiler — das
wäre hier Aufwand ohne Nutzen.
"""

import asyncio
import logging
from dataclasses import dataclass, field

from fastapi import WebSocket

from app.mitteilungen.logic import darf_empfangen

log = logging.getLogger(__name__)


@dataclass
class Verbindung:
    """Eine offene Leitung samt Blickwinkel des Betrachters."""

    socket: WebSocket
    rolle: str
    person_id: str | None


@dataclass
class Verteiler:
    """Alle offenen Leitungen, nach Kampagne sortiert."""

    _je_kampagne: dict[str, list[Verbindung]] = field(default_factory=dict)
    # Nebenläufige Verbindungen und Sendevorgänge fassen dieselbe Liste an.
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

    async def verteilen(self, campaign_id: str, mitteilung: dict) -> int:
        """Schickt die Mitteilung an alle Berechtigten. Gibt die Zahl zurück.

        Jede Leitung wird einzeln geprüft: Eine gerichtete Mitteilung darf
        nicht bei allen aufblinken, nur weil sie am selben Tisch sitzen.

        Ein Fehler auf einer Leitung darf die übrigen nicht aufhalten —
        typischerweise ist der Browser einfach weg, ohne sich abzumelden.
        """
        async with self._schloss:
            offen = list(self._je_kampagne.get(campaign_id, []))

        umschlag = {"typ": "mitteilung", "daten": mitteilung}
        zugestellt = 0
        tot: list[WebSocket] = []

        for verbindung in offen:
            if not darf_empfangen(mitteilung, verbindung.rolle, verbindung.person_id):
                continue
            try:
                await verbindung.socket.send_json(umschlag)
                zugestellt += 1
            except Exception:
                log.debug("Leitung weg, wird entfernt", exc_info=True)
                tot.append(verbindung.socket)

        for socket in tot:
            await self.abmelden(campaign_id, socket)

        return zugestellt

    async def zurueckziehen(self, campaign_id: str, mitteilung_id: str) -> None:
        """Sagt allen Bescheid, dass eine Mitteilung zurückgezogen wurde.

        Die SL soll ein versehentlich gesendetes Popup wieder einsammeln
        können — es verschwindet dann auch auf offenen Bildschirmen.
        """
        async with self._schloss:
            offen = list(self._je_kampagne.get(campaign_id, []))

        umschlag = {"typ": "zurueckgezogen", "daten": {"id": mitteilung_id}}
        for verbindung in offen:
            try:
                await verbindung.socket.send_json(umschlag)
            except Exception:
                log.debug("Leitung weg beim Zurückziehen", exc_info=True)

    async def anzahl(self, campaign_id: str) -> int:
        async with self._schloss:
            return len(self._je_kampagne.get(campaign_id, []))


# Ein Verteiler für die ganze Anwendung.
verteiler = Verteiler()
