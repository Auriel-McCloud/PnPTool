"""KI-Erzeugung von Alltagsgegenständen auf Zuruf — Marks Beispiel: ein
Spieler fragt einen Verkäufer nach Panzerklebeband, die KI schätzt einen
realistischen Preis und schlägt einen fertigen Gegenstand vor (24.09.2026,
"jetzt gleich mit umsetzen" auf Marks Wunsch vorgezogen).

**Ausdrücklich NICHT für Waffen/Rüstungen** (Marks harte Vorgabe): die KI
darf nur aus einer kleinen Whitelist harmloser Typen wählen
(ALLTAGSGEGENSTAND_TYPEN) — Waffe/Rüstung/Cyberware/Bioware/Hexware/
Fahrzeug/Drohne/Cyberdeck/Riggerkonsole stehen dort gar nicht zur Auswahl,
ein Umgehen über den Systemprompt allein reicht nicht als Schutz. Zusätzlich
kann die KI selbst 'erlaubt=false' setzen, wenn eine Anfrage erkennbar auf
Kampf-/Sicherheitsausrüstung hinausläuft (z.B. "ein scharfes Messer") — dann
wird SOFORT automatisch abgelehnt, ohne die SL zu behelligen.

**Realpreis = Schätzung aus dem Trainingswissen der KI**, keine echte
Internet-Recherche (das Backend hat keine Web-Suche angebunden) — dieselbe
Einschränkung wie beim bestehenden KI-Sortiment-Vorschlag
(ki_vorschlag.py). Für reale Alltagsgegenstände liefert das Sprachmodell
trotzdem brauchbare Größenordnungen.

**Immer SL-Freigabe** (Marks Klärungsantwort 24.09.2026, per `clarify`):
selbst ein von der KI erlaubter Vorschlag geht als Popup an die SL, der
Spieler bekommt sofort Bescheid, dass die Anfrage unterwegs ist, muss aber
nicht auf die Antwort warten (eigenes Ergebnis-Popup kommt separat per
Live-Push). Erst nach Annahme landet die Ware im Sortiment des Händlers —
der normale Kauf-Flow (Guthaben, Vertriebsart physisch/digital) greift
danach ganz normal, keine Sonderbehandlung nötig.
"""

from app.haendler import repository
from app.items.repository import create_gegenstand
from app.items.routes import _create_data
from app.items.schemas import GegenstandCreate
from app.ki.client import generiere_json

# Bewusst eine kleine, harmlose Teilmenge von items/schemas.py::GEGENSTAND_TYPEN
# — Waffe/Rüstung/Cyberware/Bioware/Hexware/Fahrzeug/Drohne/Cyberdeck/
# Riggerkonsole stehen absichtlich NICHT zur Wahl (Marks harte Vorgabe: nie
# Waffen/Rüstung automatisch erzeugen).
ALLTAGSGEGENSTAND_TYPEN = ["Verbrauchsgegenstand", "Werkzeug", "Behälter", "Sonstiges"]

_SYSTEM = (
    "Ein Spieler im Cyberpunk-Pen-and-Paper NeotopiA fragt einen Verkäufer "
    "nach einem ALLTAGSGEGENSTAND (Beispiel: Panzerklebeband, Taschenlampe, "
    "Regenschutz) — KEIN Kampf- oder Sicherheitsausrüstungsgegenstand. "
    "Schätze einen realistischen Preis in Nuyen (1 Nuyen = 1 Euro, "
    "Realweltpreis als Richtwert, du hast keinen Internetzugang — schätze "
    "nach bestem Wissen). 'typ' MUSS exakt einer der folgenden Werte sein: "
    + ", ".join(ALLTAGSGEGENSTAND_TYPEN)
    + ". Setze 'erlaubt' auf false und begründe kurz in 'ablehnungsGrund' auf "
    "Deutsch, wenn die Anfrage eindeutig auf eine Waffe, Rüstung, Kampf- "
    "oder Sicherheitsausrüstung hinausläuft (z.B. Messer, Schlagring, "
    "kugelsicherer Stoff, Reizgas) oder offensichtlich unsinnig/nicht "
    "käuflich ist — im Zweifel IMMER lieber ablehnen als riskieren."
)

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "erlaubt": {"type": "BOOLEAN"},
        "ablehnungsGrund": {"type": "STRING"},
        "name": {"type": "STRING"},
        "typ": {"type": "STRING", "enum": ALLTAGSGEGENSTAND_TYPEN},
        "beschreibung": {"type": "STRING"},
        "preis": {"type": "INTEGER"},
    },
    "required": ["erlaubt", "name", "typ", "preis"],
}


async def wunsch_erstellen(campaign_id: str, haendler_id: str, spieler_person_id: str, text: str) -> dict | None:
    """Lässt die KI den Wunsch bewerten und legt den Alltagswunsch an.

    Bei einer sofort erkennbaren Waffe/Rüstung wird SOFORT AUTO_ABGELEHNT
    gesetzt (kein Popup an die SL, kein Warten für den Spieler) — bei allem
    anderen bleibt der Wunsch OFFEN und wird per Live-Push an die SL
    geschickt (siehe routes.py::_alltagswunsch_an_sl).
    """
    haendler = await repository.hole(campaign_id, haendler_id)
    if haendler is None:
        return None

    try:
        ergebnis = await generiere_json(
            f"Verkäufer: {haendler['name']}\nWunsch des Spielers: {text}",
            _SYSTEM,
            _SCHEMA,
        )
    except Exception:
        # KI nicht erreichbar (Key fehlt, Kontingent leer, Netzwerkfehler) —
        # lieber ehrlich ablehnen als ungeprüft irgendetwas erzeugen.
        ergebnis = {
            "erlaubt": False,
            "ablehnungsGrund": "Die KI konnte gerade nicht antworten — bitte später erneut versuchen.",
        }

    typ = ergebnis.get("typ") or ""
    erlaubt = bool(ergebnis.get("erlaubt")) and typ in ALLTAGSGEGENSTAND_TYPEN
    name = (ergebnis.get("name") or text).strip()[:80]
    beschreibung = (ergebnis.get("beschreibung") or "").strip()
    preis = max(0, int(ergebnis.get("preis") or 0))

    if not erlaubt:
        grund = (ergebnis.get("ablehnungsGrund") or "").strip() or (
            "Das klingt nach Kampf- oder Sicherheitsausrüstung — das erzeugt die KI nicht automatisch."
        )
        return await repository.alltagswunsch_anlegen(
            campaign_id, haendler_id, haendler["name"], spieler_person_id, text,
            status="AUTO_ABGELEHNT", vorschlag_name=name, vorschlag_typ=typ or "Sonstiges",
            vorschlag_beschreibung=beschreibung, vorschlag_preis=preis, ablehnungs_grund=grund,
        )

    return await repository.alltagswunsch_anlegen(
        campaign_id, haendler_id, haendler["name"], spieler_person_id, text,
        status="OFFEN", vorschlag_name=name, vorschlag_typ=typ,
        vorschlag_beschreibung=beschreibung, vorschlag_preis=preis, ablehnungs_grund="",
    )


async def wunsch_beantworten(
    campaign_id: str,
    wunsch_id: str,
    angenommen: bool,
    name: str,
    beschreibung: str,
    preis: int,
    ablehnungs_grund: str,
) -> dict | None:
    """SL-Entscheidung — bei Annahme entsteht sofort ein echter Gegenstand
    (istEntwurf=false direkt: die SL hat ihn gerade selbst geprüft und
    bestätigt, ein Zwischenschritt über die Ideenschmiede wäre hier nur ein
    Umweg) und landet im Sortiment des Händlers zum bestätigten Preis — der
    normale Kauf-Flow (Guthaben, Vertriebsart) greift danach ganz normal."""
    wunsch = await repository.alltagswunsch_hole(campaign_id, wunsch_id)
    if wunsch is None or wunsch["status"] != "OFFEN":
        return None

    gegenstand_id = None
    if angenommen:
        endgueltiger_preis = preis if preis > 0 else wunsch["vorschlagPreis"]
        body = GegenstandCreate(
            name=name.strip() or wunsch["vorschlagName"],
            description=beschreibung.strip() or wunsch["vorschlagBeschreibung"],
            typ=wunsch["vorschlagTyp"] or "Sonstiges",
            preis=endgueltiger_preis,
            istEntwurf=False,
        )
        gegenstand = await create_gegenstand(campaign_id, None, _create_data(body, True, "GM", []))
        if gegenstand is None:
            return None
        gegenstand_id = gegenstand["id"]
        await repository.verkauft_hinzufuegen(campaign_id, wunsch["haendlerId"], gegenstand_id, endgueltiger_preis)

    return await repository.alltagswunsch_antwort(
        campaign_id,
        wunsch_id,
        status="ANGENOMMEN" if angenommen else "ABGELEHNT",
        ablehnungs_grund="" if angenommen else ablehnungs_grund,
        gegenstand_id=gegenstand_id,
    )
