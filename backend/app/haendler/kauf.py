"""Kauf-Kern für den Einzelkauf (`POST .../kaufen`) und den Warenkorb
(`POST .../kaufen-warenkorb`, 20.11.2026).

Zwei getrennte Schritte, damit der Warenkorb alles-oder-nichts sein kann:

1. `posten_pruefen` validiert ALLES, ohne etwas zu schreiben — jede Ware
   noch im Sortiment, kein Einzelstück doppelt, Anzahl nur bei stapelbarer
   Ware, Rassen-Feature „erster Kauf gratis“ genau einmal (erstes passendes
   Stück), Gesamtsumme gegen Kapital. Scheitert irgendwas, wird nichts
   gekauft (400/404/409 mit deutscher Meldung).
2. `posten_ausfuehren` bucht und übergibt. Scheitert eine Übergabe
   mittendrin, wird genau dieser Anteil nicht berechnet bzw. (Tutorial-
   Buchung während der Erstellung) zurückerstattet und im Ergebnis gemeldet
   — best effort, ohne echte Transaktion über mehrere Repository-Aufrufe.

Anzahl > 1 (20.11.2026): EIN Stapel im Inventar (`hatMenge=true`,
`menge = anzahl × Packungsgröße der Vorlage`), nicht N einzelne Stücke —
siehe `uebergabe.stueck_uebergeben`. Bei digitalen Läden trägt die
Bestellung die Anzahl, die Lieferung übergibt später denselben Stapel.
"""

import logging
from dataclasses import dataclass, field

from fastapi import HTTPException, status

from app.auth.dependencies import Viewer
from app.entities import repository as entities_repository
from app.entities.repository import PERSON_FIELDS
from app.ereignisprotokoll import hooks
from app.haendler import repository
from app.haendler.uebergabe import regale_raeumen, stueck_uebergeben
from app.items import repository as items_repository
from app.rassen import repository as rassen_repository
from app.rassen.gratis_kauf import trifft as erster_kauf_gratis

logger = logging.getLogger(__name__)

ANZAHL_MAX = 99


@dataclass
class KaufPosten:
    gegenstand: dict
    anzahl: int
    stueckpreis: int
    # 0 oder 1 — das Rassen-Feature macht höchstens EIN Stück gratis.
    gratis_stuecke: int = 0

    @property
    def gegenstand_id(self) -> str:
        return self.gegenstand["id"]

    @property
    def name(self) -> str:
        return self.gegenstand.get("name") or "Ware"

    @property
    def preis(self) -> int:
        return self.stueckpreis * (self.anzahl - self.gratis_stuecke)


@dataclass
class KaufPlan:
    kaeufer_id: str
    kaeufer: dict
    posten: list[KaufPosten]

    @property
    def summe(self) -> int:
        return sum(p.preis for p in self.posten)


@dataclass
class KaufErgebnis:
    # (Posten, übergebener Gegenstand, alter Besitzer) — physischer Laden
    uebergeben: list[tuple[KaufPosten, dict, str | None]] = field(default_factory=list)
    # (Posten, Bestellung) — digitaler Laden
    bestellt: list[tuple[KaufPosten, dict]] = field(default_factory=list)
    fehlgeschlagen: list[KaufPosten] = field(default_factory=list)
    kapital_neu: int = 0
    tutorial_ausgegeben: int = 0
    bezahlt: int = 0
    erstattet: int = 0

    @property
    def erfolgreich(self) -> list[KaufPosten]:
        return [p for p, _, _ in self.uebergeben] + [p for p, _ in self.bestellt]


def kaeufer_bestimmen(viewer: Viewer, kaeufer_person_id: str | None) -> str:
    """Spieler kaufen für sich selbst (kaeuferPersonId wird ignoriert — wie
    beim Messenger kann sich niemand als fremder Charakter ausgeben), die SL
    muss den Käufer nennen."""
    if viewer.role == "GM":
        if not kaeufer_person_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "kaeuferPersonId erforderlich")
        return kaeufer_person_id
    if not viewer.person_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")
    return viewer.person_id


def _benannt(name: str | None, text: str) -> str:
    return f"„{name}“: {text}" if name else text


async def posten_pruefen(
    campaign_id: str,
    haendler_id: str,
    haendler: dict,
    kaeufer_id: str,
    positionen: list[tuple[str, int]],
    *,
    warenkorb: bool = False,
) -> KaufPlan:
    """Prüft alles und liefert den Kaufplan — schreibt nichts.

    `warenkorb=False` (Einzelkauf) behält die bisherigen Meldungen/Status
    der Einzelkauf-Route bei; im Warenkorb nennt jede Meldung die Ware.
    """
    sortiment = {e["gegenstandId"]: e for e in await repository.sortiment(campaign_id, haendler_id)}

    gesehen: set[str] = set()
    for gegenstand_id, anzahl in positionen:
        eintrag = sortiment.get(gegenstand_id)
        if eintrag is None:
            if not warenkorb:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Diese Ware führt der Händler nicht (mehr)")
            weg = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                _benannt(
                    (weg or {}).get("name") or "Eine Ware",
                    "führt der Händler nicht mehr — nichts wurde gekauft.",
                ),
            )
        if gegenstand_id in gesehen:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                _benannt(eintrag.get("name"), "steht doppelt im Warenkorb — nichts wurde gekauft."),
            )
        gesehen.add(gegenstand_id)
        if anzahl < 1 or anzahl > ANZAHL_MAX:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                _benannt(eintrag.get("name"), f"Anzahl muss zwischen 1 und {ANZAHL_MAX} liegen."),
            )

    kaeufer = await entities_repository.get_node("Person", PERSON_FIELDS, campaign_id, kaeufer_id)
    if kaeufer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Käufer nicht gefunden")

    posten: list[KaufPosten] = []
    for gegenstand_id, anzahl in positionen:
        gegenstand = await items_repository.get_gegenstand(campaign_id, gegenstand_id)
        if gegenstand is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gegenstand nicht gefunden")
        name = gegenstand.get("name") if warenkorb or anzahl > 1 else None
        if anzahl > 1:
            # Einzelstücke (kein Vorlage-Nachschub) und einzigartige Vorlagen
            # gibt es nur einmal — kein Stapel.
            if not gegenstand.get("istVorlage") or gegenstand.get("einzigartig"):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    _benannt(name, "gibt es nur einmal — mehr als 1 Stück geht nur bei stapelbarer Ware."),
                )
            # tutorial-zurueck erstattet pro Stück den Stückpreis — ein
            # Stapel würde dort falsch zurückgebucht. Tutorial-Shop bleibt
            # deshalb Stück für Stück (TutorialShopPopup kennt keine Anzahl).
            if haendler.get("istTutorialShop"):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, "Im Tutorial-Shop wird Stück für Stück gekauft."
                )
        posten.append(KaufPosten(gegenstand, anzahl, repository.preis_nach_rabatt(sortiment[gegenstand_id])))

    # Rassen-Feature "gratisErsterKaufTyp" (10.10.2026, Quill-Hextech;
    # 24.10.2026 Sentinel "alle Typen"): der erste passende Kauf ist
    # kostenlos — nur einmal pro Person (`rassenFeatureGenutzt`), danach
    # normaler Preis. Bei Anzahl/Warenkorb: genau EIN Stück gratis, und zwar
    # beim ersten passenden Posten in Warenkorb-Reihenfolge. Gilt auch im
    # Tutorial-Shop (dort ist es meistens der erste Kontakt überhaupt).
    if not kaeufer.get("rassenFeatureGenutzt") and kaeufer.get("rasse"):
        rassen_katalog = {r["name"]: r for r in await rassen_repository.liste_fuer_kampagne(campaign_id)}
        feature = rassen_katalog.get(kaeufer["rasse"])
        if feature:
            for p in posten:
                if erster_kauf_gratis(feature.get("gratisErsterKaufTyp"), p.gegenstand.get("typ")):
                    p.gratis_stuecke = 1
                    break

    plan = KaufPlan(kaeufer_id=kaeufer_id, kaeufer=kaeufer, posten=posten)
    kapital = int(kaeufer.get("kapital") or 0)
    if kapital < plan.summe:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Guthaben reicht nicht — {kapital}¥ verfügbar, {plan.summe}¥ nötig",
        )
    return plan


def _anzahl_praefix(p: KaufPosten) -> str:
    return f"{p.anzahl}× " if p.anzahl > 1 else ""


async def posten_ausfuehren(
    campaign_id: str, haendler_id: str, haendler: dict, plan: KaufPlan
) -> KaufErgebnis:
    """Bucht und übergibt einen geprüften Plan.

    Scheitert ALLES, kommt 400 „Kauf fehlgeschlagen“ (Geld unangetastet bzw.
    zurückgebucht) — dasselbe Verhalten wie der Einzelkauf bisher.
    """
    kaeufer_id = plan.kaeufer_id
    kaeufer = plan.kaeufer
    kapital = int(kaeufer.get("kapital") or 0)
    summe = plan.summe
    ergebnis = KaufErgebnis(tutorial_ausgegeben=int(kaeufer.get("tutorialAusgegeben") or 0))

    # Während der Charaktererstellung zählt die Ausgabe gegen das
    # Tutorial-Budget — vorab in EINER Anweisung gebucht (Guthaben wird dort
    # atomar noch einmal geprüft), Fehlschläge werden danach erstattet.
    erstellt = not kaeufer.get("erstellungAbgeschlossen")
    if erstellt:
        gebucht = await repository.tutorial_ausgabe_buchen(campaign_id, kaeufer_id, summe)
        if gebucht is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Guthaben reicht nicht — {kapital}¥ verfügbar, {summe}¥ nötig",
            )
        ergebnis.kapital_neu = gebucht["kapital"]
        ergebnis.tutorial_ausgegeben = gebucht["ausgegeben"]

    digital = haendler.get("vertriebsart") == "DIGITAL"
    for p in plan.posten:
        try:
            if digital:
                # Digital: Kapital sofort weg, die SL liefert später
                # (POST .../bestellungen/{id}/liefern) — dieselbe Anzahl.
                if not p.gegenstand.get("istVorlage"):
                    await regale_raeumen(campaign_id, haendler_id, p.gegenstand_id)
                bestellung = await repository.bestellung_anlegen(
                    campaign_id, haendler_id, haendler["name"], kaeufer_id,
                    p.gegenstand_id, p.gegenstand["name"], p.preis, p.anzahl,
                )
                ergebnis.bestellt.append((p, bestellung))
                continue
            alter_besitzer = (
                None if p.gegenstand.get("istVorlage")
                else await items_repository.get_owner_id(campaign_id, p.gegenstand_id)
            )
            gekauft = await stueck_uebergeben(campaign_id, haendler_id, p.gegenstand_id, kaeufer_id, p.anzahl)
            if gekauft is None:
                ergebnis.fehlgeschlagen.append(p)
                continue
            ergebnis.uebergeben.append((p, gekauft, alter_besitzer))
        except HTTPException:
            ergebnis.fehlgeschlagen.append(p)
        except Exception:
            logger.exception("Shop-Kauf: Übergabe von %s fehlgeschlagen", p.gegenstand_id)
            ergebnis.fehlgeschlagen.append(p)

    erfolgreich = ergebnis.erfolgreich
    ergebnis.bezahlt = sum(p.preis for p in erfolgreich)
    ergebnis.erstattet = summe - ergebnis.bezahlt

    person_update: dict = {}
    if erstellt:
        if ergebnis.erstattet > 0:
            await repository.tutorial_ausgabe_erstatten(campaign_id, kaeufer_id, ergebnis.erstattet)
            ergebnis.kapital_neu += ergebnis.erstattet
            ergebnis.tutorial_ausgegeben -= ergebnis.erstattet
    else:
        ergebnis.kapital_neu = kapital - ergebnis.bezahlt
        if erfolgreich:
            person_update["kapital"] = ergebnis.kapital_neu
    # Feature nur verbraucht, wenn das Gratis-Stück wirklich ankam.
    if any(p.gratis_stuecke for p in erfolgreich) and not kaeufer.get("rassenFeatureGenutzt"):
        person_update["rassenFeatureGenutzt"] = True
    if person_update:
        await entities_repository.update_node("Person", PERSON_FIELDS, campaign_id, kaeufer_id, person_update)

    if not erfolgreich:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kauf fehlgeschlagen")

    # Ereignisprotokoll: der Kauf ist ab hier abgeschlossen — ein Fehler im
    # Protokoll darf ihn nicht nachträglich als gescheitert melden (sonst
    # kauft der Spieler aus Versehen doppelt).
    haendler_name = haendler.get("name")
    for p, gekauft, alter_besitzer in ergebnis.uebergeben:
        try:
            await hooks.handel(
                campaign_id,
                gegenstand_id=gekauft["id"],
                neuer_besitzer_id=kaeufer_id,
                betrag=p.preis,
                von_person_id=haendler_id,
                alter_besitzer_id=alter_besitzer,
                detail=(
                    f"{_anzahl_praefix(p)}bei {haendler_name}" if haendler_name else _anzahl_praefix(p).strip()
                ),
            )
        except Exception:
            logger.exception("Shop-Kauf: Ereignisprotokoll (Handel) fehlgeschlagen")
    for p, _bestellung in ergebnis.bestellt:
        try:
            ware = f"{_anzahl_praefix(p)}{p.gegenstand.get('name') or 'Bestellung'}"
            await hooks.geld(
                campaign_id, betrag=p.preis, art="AUSGABE", von_person_id=kaeufer_id,
                detail=f"{ware} bei {haendler_name}" if haendler_name else ware,
            )
        except Exception:
            logger.exception("Shop-Kauf: Ereignisprotokoll (Geld) fehlgeschlagen")
    return ergebnis
