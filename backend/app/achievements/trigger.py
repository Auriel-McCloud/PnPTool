"""AUTO-Trigger: live aus dem Ereignisprotokoll berechnet, kein persistenter
Vorschlags-Knoten (dasselbe Muster wie der KI-Sortiment-Vorschlag beim
Händler). Siehe docs/wiki/entities/achievements.md, Abschnitt
"Erkennungs-Pipeline" und Trigger-Katalog-Tabelle.

Jede Funktion hier beantwortet GENAU EINE auslöseArt: welche Personen
erfüllen den Trigger gerade (unabhängig davon, ob sie das Achievement schon
haben — die Filterung "schon vergeben?" passiert zentral in `vorschlaege()`).
"""

from app.achievements import repository
from app.achievements.schemas import AUSLOESE_ARTEN_MIT_ZIEL_GEGENSTAND
from app.ereignisprotokoll import repository as ereignisprotokoll_repository
from app.ki.kontext import sammle_kontext


async def _kandidaten_fuer(campaign_id: str, achievement: dict) -> list[dict]:
    """Personen, die den auslöseArt des Achievements GERADE erfüllen —
    unabhängig von bereits bestehenden Verleihungen."""
    art = achievement.get("ausloeseArt")

    if art == "ERSTER_KILL":
        kandidat = await repository.erster_kill_kandidat(campaign_id)
        return [kandidat] if kandidat else []

    if art == "MOERDER":
        return await repository.moerder_kandidaten(campaign_id)

    if art == "MEISTE_SCHADEN_GENOMMEN":
        eintrag = await ereignisprotokoll_repository.hoechster_schaden(campaign_id, "ZIEL")
        return [{"personId": eintrag["personId"], "personName": eintrag["personName"]}] if eintrag else []

    if art == "MEISTE_SCHADEN_VERTEILT":
        eintrag = await ereignisprotokoll_repository.hoechster_schaden(campaign_id, "ANGREIFER")
        return [{"personId": eintrag["personId"], "personName": eintrag["personName"]}] if eintrag else []

    if art == "ERSTER_KAUF":
        return await repository.erster_kauf_kandidaten(campaign_id)

    if art == "ERSTE_VERHANDLUNG":
        return await repository.erste_verhandlung_kandidaten(campaign_id)

    if art == "CHARAKTER_ERSTELLT":
        return await repository.frisch_erstellte_pcs(campaign_id)

    if art == "GEHEIMNISTRAEGER":
        return await repository.geheimnistraeger_kandidaten(campaign_id)

    if art == "ERSTER_BESITZ_ZIEL":
        ziel_id = achievement.get("zielGegenstandId")
        if not ziel_id:
            return []
        return await repository.erster_besitz_ziel_traeger(campaign_id, ziel_id)

    if art == "ERSTE_BESCHREIBUNG_ZIEL":
        ziel_id = achievement.get("zielGegenstandId")
        if not ziel_id:
            return []
        return await repository.beschreibung_sichtbar_fuer_pcs(campaign_id, ziel_id)

    if art == "ERSTER_CRITTER":
        return await repository.erster_critter_traeger(campaign_id)

    if art == "ERSTE_DROHNE":
        return await repository.erste_drohne_traeger(campaign_id)

    if art == "ENDBOSS_BESIEGT":
        return await repository.endboss_besiegt_kandidaten(campaign_id)

    if art == "ERSTE_SITZUNG_UEBERLEBT":
        # Prüft rückwirkend beim Vorhandensein einer zweiten Sitzung, welche
        # PCs die erste überlebt haben (siehe docs/wiki/entities/achievements.md).
        if await repository.anzahl_sitzungen(campaign_id) < 2:
            return []
        erste = await repository.erste_sitzung_id(campaign_id)
        if erste is None:
            return []
        tote = await repository.kampf_tote_in_sitzung(campaign_id, erste)
        pcs = await repository.alle_pcs(campaign_id)
        return [p for p in pcs if p["personId"] not in tote]

    return []


async def vorschlaege(campaign_id: str) -> list[dict]:
    """Alle offenen AUTO-Vorschläge: Achievement × Person, wo der Trigger
    gerade zutrifft UND diese Person es noch nicht hat (nicht abgelöst)."""
    alle_achievements = await repository.liste(campaign_id)
    ergebnis: list[dict] = []

    for achievement in alle_achievements:
        if achievement.get("art") != "AUTO" or not achievement.get("ausloeseArt"):
            continue
        kandidaten = await _kandidaten_fuer(campaign_id, achievement)
        for kandidat in kandidaten:
            person_id = kandidat.get("personId")
            if not person_id:
                continue
            if await repository.hat_bereits(campaign_id, achievement["id"], person_id):
                continue
            ergebnis.append(
                {
                    "achievementId": achievement["id"],
                    "achievementName": achievement["name"],
                    "achievementIcon": achievement.get("icon") or "",
                    "personId": person_id,
                    "personName": kandidat.get("personName") or "",
                }
            )

    return ergebnis


async def kontext_fuer_vorschlag(campaign_id: str, achievement: dict) -> str:
    """Zusatzkontext für den KI-Text — thematisch auf den Auslöser bezogen,
    nicht nur einen nackten Achievement-Namen (Marks Wunsch, siehe
    docs/wiki/entities/achievements.md, Abschnitt "KI-Text"). Bewusst knapp:
    der allgemeine Kampagnenkontext kommt ohnehin aus sammle_kontext."""
    basis = await sammle_kontext(campaign_id)
    art = achievement.get("ausloeseArt") or ""
    hinweis = {
        "ERSTER_KILL": "Dies ist der allererste Kill der gesamten Kampagne.",
        "MOERDER": "Diese Person hat soeben ihren ersten Kill erzielt.",
        "MEISTE_SCHADEN_GENOMMEN": "Diese Person hat den bisher höchsten Einzelschaden erlitten.",
        "MEISTE_SCHADEN_VERTEILT": "Diese Person hat den bisher höchsten Einzelschaden ausgeteilt.",
        "ERSTER_KAUF": "Dies ist der erste eigenständige Einkauf dieses Charakters.",
        "ERSTE_VERHANDLUNG": "Dies ist die erste Verhandlung dieses Charakters.",
        "CHARAKTER_ERSTELLT": "Der Charakter hat soeben die Erstellung abgeschlossen.",
        "GEHEIMNISTRAEGER": "Diese Person wurde als einzige in ein Geheimnis eingeweiht.",
        "ERSTER_BESITZ_ZIEL": "Diese Person hält zum ersten Mal den Zielgegenstand in Händen.",
        "ERSTE_BESCHREIBUNG_ZIEL": "Diese Person hat soeben herausgefunden, was es mit dem Gegenstand auf sich hat.",
        "ERSTER_CRITTER": "Diese Person hat soeben ihr erstes Haustier bekommen.",
        "ERSTE_DROHNE": "Diese Person besitzt nun ihre erste Drohne.",
        "ENDBOSS_BESIEGT": "Diese Person hat den Endgegner besiegt.",
        "ERSTE_SITZUNG_UEBERLEBT": "Diese Person hat die erste Sitzung der Kampagne überlebt.",
    }.get(art, "")
    teile = [t for t in (basis, hinweis) if t]
    return "\n\n".join(teile)
