"""Auto-Hooks ins Ereignisprotokoll.

Fachmodule rufen diese Funktionen, nicht das Repository direkt — so holt
jede Schreibstelle die aktive Sitzung auf demselben Weg und die Tests
können die Hooks mocken, ohne Neo4j.

Siehe docs/wiki/entities/ereignisprotokoll.md und docs/api/ereignisprotokoll.md.
"""

import uuid

from app.ereignisprotokoll import repository


async def _sitzung(campaign_id: str) -> str | None:
    return await repository.aktive_sitzung_id(campaign_id)


async def _event_ids(campaign_id: str) -> list[str]:
    """Events der Kampfkarte, die gerade liegt. Annahme: die Karte trägt das
    Event, nicht der Kampf selbst. Keine Karte oder kein Event → leer."""
    from app.battlemap import repository as karten
    from app.kampf import repository as kampf_repo

    kampf = await kampf_repo.hole(campaign_id)
    if not kampf or not kampf.get("battlemapId"):
        return []
    karte = await karten.holen(campaign_id, kampf["battlemapId"])
    return [str(i) for i in ((karte or {}).get("eventIds") or []) if i]


async def kampf_treffer(
    campaign_id: str,
    *,
    ziel_person_id: str,
    art: str,
    hp_art: str | None,
    hp_menge: int,
    kaestchen_schaden: int,
    angreifer_person_id: str | None,
    kampf_id: str,
    runde: int,
) -> None:
    await repository.log_kampf_eintrag(
        campaign_id,
        art=art,
        ziel_person_id=ziel_person_id,
        angreifer_person_id=angreifer_person_id,
        kampf_id=kampf_id,
        runde=runde,
        hp_art=hp_art,
        hp_menge=hp_menge,
        kaestchen_schaden=kaestchen_schaden,
        event_ids=await _event_ids(campaign_id),
        sitzung_id=await _sitzung(campaign_id),
    )


async def kampf_aktion(
    campaign_id: str,
    *,
    art: str,
    akteur_id: str | None = None,
    ziel_id: str | None = None,
    detail: str = "",
) -> None:
    """Kampfaktion ins Protokoll. Schaden bleibt bei kampf_treffer (Initiative
    als Angreifer). Hier ist der Akteur die Person, die die Aktion ausführt;
    fehlt sie, fällt es auf den Initiative-Zug zurück."""
    from app.kampf import repository as kampf_repo

    kampf = await kampf_repo.hole(campaign_id)
    if akteur_id is None and kampf:
        akteur_id = await kampf_repo.angreifer_person_id(campaign_id)
    if ziel_id and akteur_id and ziel_id != akteur_id:
        angreifer, ziel = akteur_id, ziel_id
    else:
        angreifer, ziel = None, akteur_id or ziel_id
    await repository.log_kampf_eintrag(
        campaign_id,
        art=art,
        ziel_person_id=ziel,
        angreifer_person_id=angreifer,
        kampf_id=(kampf or {}).get("id", ""),
        runde=int((kampf or {}).get("runde") or 0),
        detail=detail,
        event_ids=await _event_ids(campaign_id),
        sitzung_id=await _sitzung(campaign_id),
    )


async def verhandlungsausgang(campaign_id: str, verhandlung: dict, angenommen: bool) -> None:
    positionen = [p if isinstance(p, dict) else p.model_dump() for p in verhandlung["positionen"]]
    await repository.log_verhandlungsausgang(
        campaign_id,
        verhandlung_id=verhandlung["id"],
        art=verhandlung["art"],
        angenommen=angenommen,
        gesamtbetrag=verhandlung["gesamtbetrag"],
        positionen=positionen,
        empfaenger_person_id=verhandlung["empfaengerPersonId"],
        sitzung_id=await _sitzung(campaign_id),
    )


async def charakterentwicklung(
    campaign_id: str,
    *,
    person_id: str,
    art: str,
    alt: str = "",
    neu: str = "",
    kosten_oder_menge: int = 0,
    trait_def_id: str | None = None,
    trait_name: str | None = None,
    sl_notiz: str = "",
) -> None:
    await repository.log_charakterentwicklung(
        campaign_id,
        person_id=person_id,
        art=art,
        alt=alt,
        neu=neu,
        kosten_oder_menge=kosten_oder_menge,
        trait_def_id=trait_def_id,
        trait_name=trait_name,
        sl_notiz=sl_notiz,
        sitzung_id=await _sitzung(campaign_id),
    )


async def ki(
    campaign_id: str,
    *,
    anlass: str,
    prompt: str,
    antwort_text: str,
    uebernommen: bool,
    betrifft_id: str | None = None,
) -> None:
    """Jede KI-Ausgabe — auch Vorschauen, die niemand übernimmt."""
    await repository.log_ki_eintrag(
        campaign_id,
        anlass=anlass,
        prompt=prompt,
        antwort_text=antwort_text,
        uebernommen=uebernommen,
        betrifft_id=betrifft_id,
        sitzung_id=await _sitzung(campaign_id),
    )


async def gegenstand(
    campaign_id: str,
    *,
    art: str,
    gegenstand_id: str,
    alter_besitzer_id: str | None = None,
    neuer_besitzer_id: str | None = None,
    handel_id: str | None = None,
    detail: str = "",
) -> None:
    await repository.log_gegenstandsbewegung(
        campaign_id,
        art=art,
        gegenstand_id=gegenstand_id,
        alter_besitzer_id=alter_besitzer_id,
        neuer_besitzer_id=neuer_besitzer_id,
        handel_id=handel_id,
        detail=detail,
        sitzung_id=await _sitzung(campaign_id),
    )


async def geld(
    campaign_id: str,
    *,
    betrag: int,
    art: str,
    von_person_id: str | None = None,
    an_person_id: str | None = None,
    handel_id: str | None = None,
    detail: str = "",
) -> None:
    await repository.log_geldbewegung(
        campaign_id,
        betrag=betrag,
        art=art,
        von_person_id=von_person_id,
        an_person_id=an_person_id,
        handel_id=handel_id,
        detail=detail,
        sitzung_id=await _sitzung(campaign_id),
    )


async def handel(
    campaign_id: str,
    *,
    gegenstand_id: str,
    neuer_besitzer_id: str,
    betrag: int,
    von_person_id: str | None = None,
    alter_besitzer_id: str | None = None,
    gegenstand_art: str = "GEKAUFT",
    detail: str = "",
) -> None:
    """Kauf: eine GegenstandsBewegung + eine GeldBewegung, gemeinsame handelId."""
    hid = str(uuid.uuid4())
    await gegenstand(
        campaign_id,
        art=gegenstand_art,
        gegenstand_id=gegenstand_id,
        alter_besitzer_id=alter_besitzer_id,
        neuer_besitzer_id=neuer_besitzer_id,
        handel_id=hid,
        detail=detail,
    )
    await geld(
        campaign_id,
        betrag=betrag,
        art="HANDEL",
        von_person_id=von_person_id,
        an_person_id=neuer_besitzer_id,
        handel_id=hid,
    )


async def aufenthalt(
    campaign_id: str,
    *,
    ort_id: str,
    ort_kind: str,
    party_id: str | None = None,
) -> None:
    await repository.log_aufenthalt(
        campaign_id,
        ort_id=ort_id,
        ort_kind=ort_kind,
        party_id=party_id,
        sitzung_id=await _sitzung(campaign_id),
    )
