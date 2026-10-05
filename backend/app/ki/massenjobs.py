"""In-Prozess-Jobverwaltung für die Massen-KI-Anlage (05.10.2026).

Hintergrund (Marks Bugreport): "Mehrere auf einmal anlegen" ruft pro Eintrag
einmal die KI auf, alles bisher synchron in EINER eingehenden HTTP-Anfrage.
Bei 9 Gegenständen dauert das locker über eine Minute — auf Mobilfunk killt
das Handy/der Browser die Verbindung oft, bevor die Antwort da ist
("Failed to fetch"), und nginx loggt dazu 499 (Client hat selbst
abgebrochen). Die Anfrage kam dabei nie über den allerersten Schritt hinaus:
kein einziger Gegenstand wurde angelegt, weil die ganze Arbeit an der
eingehenden Verbindung hing und mit ihr wegfiel.

Jetzt startet die Route nur noch den Job und antwortet sofort mit einer
Job-ID; die eigentliche Erzeugung läuft in einem eigenen asyncio-Task weiter,
komplett unabhängig davon ob der ursprüngliche Request-Client noch zuhört.
Das Frontend fragt den Fortschritt per Polling ab (siehe BeratungPopup.tsx).

Bewusst im Prozessspeicher, kein Neo4j-Knoten: PnPTool läuft als EIN
Uvicorn-Prozess auf Marks Heimserver (dasselbe Argument wie
mitteilungen/verteiler.py für die WebSocket-Verbindungsliste). Ein
Prozessneustart (Deploy, --reload bei einer Codeänderung) verliert den
Job-Fortschritt aus der Statusabfrage — aber NICHT die Arbeit selbst: jeder
Eintrag wird im Job-Loop einzeln und sofort in Neo4j angelegt (istEntwurf),
nicht erst am Ende gesammelt. Ein verlorener Job zeigt sich höchstens als
"nicht gefunden" beim nächsten Poll, nie als verlorene Arbeit.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Awaitable, Callable

log = logging.getLogger(__name__)


@dataclass
class MassenJob:
    gesamt: int
    erstellt: int = 0
    fertig: bool = False
    ergebnis: object | None = None
    fehler: str | None = None


_JOBS: dict[str, MassenJob] = {}
# Referenzen auf laufende Tasks halten — sonst darf der Garbage Collector
# eine "fire and forget"-Task jederzeit vorzeitig einsammeln (bekannte
# asyncio-Falle, siehe https://docs.python.org/3/library/asyncio-task.html
# unter "Important: Save a reference to the result of this function").
_TASKS: set[asyncio.Task] = set()


def starten(gesamt: int, arbeit: Callable[[MassenJob], Awaitable[object]]) -> str:
    """Startet `arbeit(job)` entkoppelt vom aufrufenden Request, gibt die Job-ID zurück.

    `arbeit` bekommt den Job zum Mitschreiben des Fortschritts (job.erstellt)
    und muss am Ende das Ergebnis zurückgeben (landet in job.ergebnis).
    """
    job_id = str(uuid.uuid4())
    job = MassenJob(gesamt=gesamt)
    _JOBS[job_id] = job

    async def _lauf() -> None:
        try:
            job.ergebnis = await arbeit(job)
        except Exception as e:  # noqa: BLE001 — soll dem Polling als Text ankommen
            log.exception("Massen-Anlage-Job %s fehlgeschlagen", job_id)
            job.fehler = str(e) or "Massen-Anlage fehlgeschlagen"
        finally:
            job.fertig = True

    task = asyncio.create_task(_lauf())
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)
    return job_id


def status(job_id: str) -> MassenJob | None:
    return _JOBS.get(job_id)
