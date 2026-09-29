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
) -> None:
    await repository.log_gegenstandsbewegung(
        campaign_id,
        art=art,
        gegenstand_id=gegenstand_id,
        alter_besitzer_id=alter_besitzer_id,
        neuer_besitzer_id=neuer_besitzer_id,
        handel_id=handel_id,
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
) -> None:
    await repository.log_geldbewegung(
        campaign_id,
        betrag=betrag,
        art=art,
        von_person_id=von_person_id,
        an_person_id=an_person_id,
        handel_id=handel_id,
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
