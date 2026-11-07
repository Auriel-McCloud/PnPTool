"""Sichtbarkeit im Gruppenchat: wer sieht welchen Namen.

Seiteneffektfrei und ohne Datenbank, damit die Regeln direkt testbar sind.

* **Spieler** sehen jeden NPC unter dem eigenen Alias bzw. „Unbekannter …“ —
  nie den echten Namen (dieselbe Regel wie im Einzelchat,
  `kontakte/security.py::alias_von`). Mitspieler erscheinen unter dem eigenen
  Alias, sonst unter dem Charakternamen.
* **Die Spielleitung** sieht überall die echten Namen.
"""

from app.kontakte.security import alias_von
from app.gruppenchat.schemas import GruppeResponse, GruppenNachrichtResponse, TeilnehmerResponse


def ist_npc(person: dict) -> bool:
    return (person.get("personType") or person.get("vonTyp") or "NPC") != "PC"


def anzeigename(
    *,
    name: str | None,
    typ: str,
    alias: str,
    rasse: str,
    persoenlicher_alias: str,
    als_gm: bool,
) -> str:
    """Der Name einer Person aus Sicht des Betrachters."""
    if als_gm:
        return (name or "").strip() or "Unbekannt"
    return alias_von(
        {
            "npcPersonType": typ,
            "npcName": name,
            "npcAlias": alias,
            "npcRasse": rasse,
            "persoenlicherAlias": persoenlicher_alias,
        }
    )


def teilnehmer_fuer(
    roh: dict, *, ich_id: str | None, aliase: dict[str, str], als_gm: bool
) -> TeilnehmerResponse:
    return TeilnehmerResponse(
        id=roh["id"],
        name=anzeigename(
            name=roh.get("name"),
            typ=roh.get("personType") or "NPC",
            alias=roh.get("alias") or "",
            rasse=roh.get("rasse") or "",
            persoenlicher_alias=aliase.get(roh["id"], ""),
            als_gm=als_gm,
        ),
        bildUrl=roh.get("bildUrl") or "",
        istNpc=ist_npc(roh),
        ich=bool(ich_id) and roh["id"] == ich_id,
    )


def gruppe_fuer(
    roh: dict, *, ich_id: str | None, aliase: dict[str, str], als_gm: bool
) -> GruppeResponse:
    return GruppeResponse(
        id=roh["id"],
        name=roh.get("name") or "",
        offen=bool(roh.get("offen", True)),
        ungelesen=int(roh.get("ungelesen") or 0),
        teilnehmer=[
            teilnehmer_fuer(t, ich_id=ich_id, aliase=aliase, als_gm=als_gm)
            for t in roh.get("teilnehmer") or []
        ],
    )


def nachricht_fuer(
    roh: dict, *, ich_id: str | None, aliase: dict[str, str], als_gm: bool
) -> GruppenNachrichtResponse:
    """Eine Nachricht aus Sicht des Betrachters.

    Spieler: rechts steht, was der eigene Charakter geschrieben hat. SL: rechts
    stehen die NPC-Nachrichten (sie schreibt ja als NPC), links die der PCs.
    """
    von_npc = (roh.get("vonTyp") or "NPC") != "PC"
    von_mir = von_npc if als_gm else (bool(ich_id) and roh.get("vonId") == ich_id)
    return GruppenNachrichtResponse(
        id=roh["id"],
        inhalt=roh.get("inhalt") or "",
        erstelltAm=roh.get("erstelltAm") or "",
        vonMir=von_mir,
        absender=""
        if (von_mir and not als_gm)
        else anzeigename(
            name=roh.get("vonName"),
            typ=roh.get("vonTyp") or "NPC",
            alias=roh.get("vonAlias") or "",
            rasse=roh.get("vonRasse") or "",
            persoenlicher_alias=aliase.get(roh.get("vonId") or "", ""),
            als_gm=als_gm,
        ),
        bildUrl=roh.get("vonBildUrl") or "",
    )
