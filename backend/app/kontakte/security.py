"""Sicherheitsschicht für Kontakte: was darf wer sehen.

**Die eine Stelle**, an der ein Rohdatensatz aus Neo4j in eine Antwort für
einen Betrachter wird. Der echte NPC-Name verlässt den Server nur hier — und
nur, wenn `echterNameBekannt` gesetzt ist.

Grundsatz wie in `entities/visibility.py`: serverseitig schneiden, nicht im
Browser verstecken. Im Netzwerkverkehr stünde der Name sonst trotzdem.
"""

from app.auth.dependencies import Viewer
from app.kontakte.logic import effektiver_alias, ist_mindestens_stufe, standard_alias
from app.kontakte.schemas import KontaktGmResponse, KontaktResponse


def ist_spielerkontakt(roh: dict) -> bool:
    """Ist das Gegenüber ein Spielercharakter (PC ↔ PC-Chat)?"""
    return roh.get("npcPersonType") == "PC"


def _alias_von(roh: dict) -> str:
    """Anzeigename: persönlicher Alias → NPC-Standard → aus der Rasse.

    Bei einem Spielerkontakt gilt: persönlicher Alias → Name des Charakters
    (wer Kontakt austauscht, kennt den Namen).
    """
    if ist_spielerkontakt(roh):
        eigener = (roh.get("persoenlicherAlias") or roh.get("alias") or "").strip()
        return eigener or (roh.get("npcName") or "").strip() or "Unbekannt"
    npc_standard = (roh.get("npcAlias") or "").strip() or standard_alias(roh.get("npcRasse"))
    # `alias` ist der auf der KENNT-Kante gesetzte persönliche Alias; ältere
    # Datensätze führen ihn unter `persoenlicherAlias`.
    persoenlich = (roh.get("persoenlicherAlias") or roh.get("alias") or "").strip()
    return effektiver_alias(npc_standard, persoenlich)


# Öffentlicher Name für Routen, die den Anzeigenamen brauchen (Chat-Kopf, Absender).
alias_von = _alias_von


def chat_ist_offen(roh: dict) -> bool:
    """Ist der Einzelchat offen? Eine Regel für Liste, Lesen und Senden.

    `chatOffen` ist getrennt von `stufe`, damit die SL den Chat einzeln
    öffnen/schließen kann. Nur ein nie gesetztes Feld fällt auf den
    Kontaktaustausch zurück.
    """
    offen = roh.get("chatOffen")
    if offen is None:
        return ist_mindestens_stufe(roh.get("stufe") or "GESEHEN", "KONTAKT_AUSGETAUSCHT")
    return bool(offen)


def kontakt_fuer_viewer(roh: dict, viewer: Viewer) -> KontaktResponse:
    """Baut die sichere Kontaktantwort für einen Spieler.

    Der echte Name wird **weggelassen**, solange er nicht freigegeben ist.
    Die Beschreibung erscheint erst ab GESPROCHEN — vorher weiss der
    Charakter nur, wie jemand aussieht, nicht wer er ist.
    """
    stufe = roh.get("stufe") or "GESEHEN"
    name_bekannt = bool(roh.get("echterNameBekannt"))
    # chatOffen: explizit gesetzt ODER implizit durch Kontaktaustausch.
    # Das Feld ist getrennt von stufe, damit die SL den Chat einzeln
    # öffnen/schließen kann — aber Kontaktaustausch öffnet ihn automatisch.
    chat_offen = roh.get("chatOffen")
    if chat_offen is None:
        chat_offen = ist_mindestens_stufe(stufe, "KONTAKT_AUSGETAUSCHT")

    return KontaktResponse(
        id=roh["id"],
        npcId=roh["npcId"],
        alias=_alias_von(roh),
        # Nur nach ausdrücklicher Freigabe durch die Spielleitung.
        echterName=roh.get("npcName") if name_bekannt else None,
        persoenlicherAlias=(roh.get("persoenlicherAlias") or roh.get("alias") or ""),
        bildUrl=roh.get("npcBildUrl") or "",
        # Ab GESPROCHEN kennt man mehr als das blosse Aussehen.
        # Beschreibung/Hintergrund eines Mitspielers bleibt privat.
        beschreibung=""
        if ist_spielerkontakt(roh)
        else (roh.get("npcDescription") or "") if ist_mindestens_stufe(stufe, "GESPROCHEN") else "",
        stufe=stufe,
        echterNameBekannt=name_bekannt,
        kontaktAnfrageStatus=roh.get("kontaktAnfrageStatus") or "KEINE",
        persoenlicheNotizen=roh.get("persoenlicheNotizen") or "",
        chatOffen=bool(chat_offen),
        nurLesen=bool(roh.get("nurLesen")),
        ungelesen=int(roh.get("ungelesen") or 0),
        istBlankoKontakt=bool(roh.get("npcIstBlankoKontakt")),
        istMentor=bool(roh.get("npcIstMentor")),
    )


def kontakt_fuer_gm(roh: dict) -> KontaktGmResponse:
    """Die Spielleitung sieht alles — sie hat den NPC angelegt."""
    stufe = roh.get("stufe") or "GESEHEN"
    # chatOffen: explizit gesetzt ODER implizit durch Kontaktaustausch
    chat_offen = roh.get("chatOffen")
    if chat_offen is None:
        chat_offen = ist_mindestens_stufe(stufe, "KONTAKT_AUSGETAUSCHT")
    return KontaktGmResponse(
        id=roh["id"],
        npcId=roh["npcId"],
        pcId=roh.get("pcId") or "",
        pcName=roh.get("pcName") or "",
        npcName=roh.get("npcName") or "",
        alias=_alias_von(roh),
        echterName=roh.get("npcName"),
        persoenlicherAlias=(roh.get("persoenlicherAlias") or roh.get("alias") or ""),
        bildUrl=roh.get("npcBildUrl") or "",
        beschreibung=roh.get("npcDescription") or "",
        stufe=stufe,
        echterNameBekannt=bool(roh.get("echterNameBekannt")),
        kontaktAnfrageStatus=roh.get("kontaktAnfrageStatus") or "KEINE",
        persoenlicheNotizen=roh.get("persoenlicheNotizen") or "",
        chatOffen=bool(chat_offen),
        nurLesen=bool(roh.get("nurLesen")),
        ungelesen=int(roh.get("ungelesen") or 0),
        istBlankoKontakt=bool(roh.get("npcIstBlankoKontakt")),
        istMentor=bool(roh.get("npcIstMentor")),
    )


def darf_kontakt_sehen(roh: dict, viewer: Viewer) -> bool:
    """Gehört dieses Kontaktwissen dem Betrachter?

    Fail-closed: ohne eigene Person sieht ein Spieler nichts.

    Spielerkontakte (PC ↔ PC) sind privat: auch die Spielleitung bekommt sie
    nicht zu sehen — kein Mitlesen, keine Meldung. (Die Daten liegen
    unverschlüsselt in der Datenbank, falls ein Eingriff je nötig wird.)
    """
    if ist_spielerkontakt(roh):
        return bool(viewer.person_id) and viewer.role != "GM" and roh.get("pcId") == viewer.person_id
    if viewer.role == "GM":
        return True
    if not viewer.person_id:
        return False
    return roh.get("pcId") == viewer.person_id
