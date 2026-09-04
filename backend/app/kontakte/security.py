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


def _alias_von(roh: dict) -> str:
    """Anzeigename: persönlicher Alias → NPC-Standard → aus der Rasse."""
    npc_standard = (roh.get("npcAlias") or "").strip() or standard_alias(roh.get("npcRasse"))
    # `alias` ist der auf der KENNT-Kante gesetzte persönliche Alias; ältere
    # Datensätze führen ihn unter `persoenlicherAlias`.
    persoenlich = (roh.get("persoenlicherAlias") or roh.get("alias") or "").strip()
    return effektiver_alias(npc_standard, persoenlich)


def kontakt_fuer_viewer(roh: dict, viewer: Viewer) -> KontaktResponse:
    """Baut die sichere Kontaktantwort für einen Spieler.

    Der echte Name wird **weggelassen**, solange er nicht freigegeben ist.
    Die Beschreibung erscheint erst ab GESPROCHEN — vorher weiss der
    Charakter nur, wie jemand aussieht, nicht wer er ist.
    """
    stufe = roh.get("stufe") or "GESEHEN"
    name_bekannt = bool(roh.get("echterNameBekannt"))

    return KontaktResponse(
        id=roh["id"],
        npcId=roh["npcId"],
        alias=_alias_von(roh),
        # Nur nach ausdrücklicher Freigabe durch die Spielleitung.
        echterName=roh.get("npcName") if name_bekannt else None,
        persoenlicherAlias=(roh.get("persoenlicherAlias") or roh.get("alias") or ""),
        bildUrl=roh.get("npcBildUrl") or "",
        # Ab GESPROCHEN kennt man mehr als das blosse Aussehen.
        beschreibung=(roh.get("npcDescription") or "") if ist_mindestens_stufe(stufe, "GESPROCHEN") else "",
        stufe=stufe,
        echterNameBekannt=name_bekannt,
        kontaktAnfrageStatus=roh.get("kontaktAnfrageStatus") or "KEINE",
        persoenlicheNotizen=roh.get("persoenlicheNotizen") or "",
        chatOffen=ist_mindestens_stufe(stufe, "KONTAKT_AUSGETAUSCHT"),
        ungelesen=int(roh.get("ungelesen") or 0),
    )


def kontakt_fuer_gm(roh: dict) -> KontaktGmResponse:
    """Die Spielleitung sieht alles — sie hat den NPC angelegt."""
    stufe = roh.get("stufe") or "GESEHEN"
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
        chatOffen=ist_mindestens_stufe(stufe, "KONTAKT_AUSGETAUSCHT"),
        ungelesen=int(roh.get("ungelesen") or 0),
    )


def darf_kontakt_sehen(roh: dict, viewer: Viewer) -> bool:
    """Gehört dieses Kontaktwissen dem Betrachter?

    Fail-closed: ohne eigene Person sieht ein Spieler nichts.
    """
    if viewer.role == "GM":
        return True
    if not viewer.person_id:
        return False
    return roh.get("pcId") == viewer.person_id
