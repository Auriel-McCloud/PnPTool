"""Hintergrund-Job für die Massen-KI-Anlage (05.10.2026).

Bugreport (Mark): "Mehrere auf einmal anlegen" rief die KI nacheinander
einmal pro Eintrag auf — alles in EINER eingehenden HTTP-Anfrage, die bei
9 Gegenständen leicht über eine Minute offen bleiben musste. Auf Mobilfunk
bricht der Browser eine so lange wartende Anfrage eher ab, als die Antwort
abzuwarten ("Failed to fetch", nginx loggt dazu 499 = Client hat selbst
geschlossen) — und weil die ganze Arbeit an dieser einen Anfrage hing, kam
dabei nicht einmal der erste Eintrag zustande.

Diese Tests prüfen die Entkopplung selbst (massenjobs.py), unabhängig von
den HTTP-Routen — siehe test_massenidee.py für die Routen-Ebene.
"""

import asyncio

from app.ki import massenjobs


def _run(coro):
    return asyncio.run(coro)


def test_job_meldet_fortschritt_und_wird_fertig():
    async def main():
        async def arbeit(job: massenjobs.MassenJob):
            for i in range(3):
                await asyncio.sleep(0)
                job.erstellt = i + 1
            return {"ok": True}

        job_id = massenjobs.starten(3, arbeit)
        for _ in range(20):
            stand = massenjobs.status(job_id)
            if stand and stand.fertig:
                break
            await asyncio.sleep(0.01)
        return massenjobs.status(job_id)

    stand = _run(main())
    assert stand is not None
    assert stand.fertig is True
    assert stand.erstellt == 3
    assert stand.gesamt == 3
    assert stand.ergebnis == {"ok": True}
    assert stand.fehler is None


def test_job_laeuft_weiter_auch_wenn_der_startende_aufruf_laengst_zurueck_ist():
    """Kernpunkt des Fixes: die Route, die den Job startet, muss NICHT auf
    `arbeit` warten — sie kehrt sofort zurück (wie bei einem Client, der die
    Verbindung direkt danach kappt), und die Arbeit läuft trotzdem im
    selben, dauerhaft laufenden Server-Event-Loop zu Ende."""

    async def main():
        async def arbeit(job: massenjobs.MassenJob):
            await asyncio.sleep(0.02)
            job.erstellt = 1
            return {"erledigt": True}

        async def anfrage_handler():
            # Entspricht der echten Route: startet den Job, wartet NICHT.
            return massenjobs.starten(1, arbeit)

        job_id = await anfrage_handler()  # "Anfrage" ist hier bereits fertig

        for _ in range(30):
            stand = massenjobs.status(job_id)
            if stand and stand.fertig:
                return stand
            await asyncio.sleep(0.01)
        return massenjobs.status(job_id)

    stand = _run(main())
    assert stand is not None
    assert stand.fertig is True
    assert stand.ergebnis == {"erledigt": True}


def test_unbekannte_job_id_gibt_none():
    assert massenjobs.status("existiert-nicht") is None


def test_fehlgeschlagener_job_setzt_fehlertext_und_wird_trotzdem_fertig():
    async def main():
        async def arbeit(job: massenjobs.MassenJob):
            raise ValueError("kaputt")

        job_id = massenjobs.starten(1, arbeit)
        for _ in range(20):
            stand = massenjobs.status(job_id)
            if stand and stand.fertig:
                break
            await asyncio.sleep(0.01)
        return massenjobs.status(job_id)

    stand = _run(main())
    assert stand is not None
    assert stand.fertig is True
    assert stand.fehler == "kaputt"
    assert stand.ergebnis is None
