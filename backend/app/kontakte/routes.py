"""HTTP-Routen für Kontakte und Messenger.

Der Messenger ist eine **optionale Kampagnenfunktion** (`messengerAktiv`,
Standard aus). Ist sie aus, antworten alle Routen mit 403 — eine
D&D-Kampagne bekommt keinen Cyberpunk-Chat.

Berechtigungen:

* Ein Spieler sieht **nur seine eigenen** Kontakte und schreibt nur in
  eigenen Chats.
* Die Spielleitung sieht alles, entscheidet über Kontaktanfragen und schreibt
  **als der NPC** — nie als "Spielleitung" (Spec: SL-Nachrichten haben keinen
  sichtbaren Absender).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import Viewer, get_viewer, require_campaign_gm, require_campaign_zugang
from app.campaigns.repository import get_einstellungen
from app.kontakte import repository
from app.kontakte.logic import (
    effektiver_alias,
    erreichbare_npcs,
    ist_mindestens_stufe,
    kann_kontakt_anfragen,
    standard_alias,
)
from app.kontakte.schemas import (
    AliasUpdate,
    AnfrageEntscheidung,
    ChatResponse,
    KontaktCreate,
    KontaktGmResponse,
    KontaktGmUpdate,
    KontaktResponse,
    NachrichtCreate,
    NachrichtResponse,
    NotizenUpdate,
)
from app.kontakte.security import darf_kontakt_sehen, kontakt_fuer_gm, kontakt_fuer_viewer


async def require_messenger_active(
    campaign_id: str, viewer: Viewer = Depends(get_viewer)
) -> Viewer:
    """Sperrt alles, solange der Messenger in dieser Kampagne aus ist.

    Bewusst als eigene Dependency statt als Prüfung in jeder Route: so kann
    keine neue Route sie vergessen.
    """
    einstellungen = await get_einstellungen(campaign_id)
    if not einstellungen.get("messengerAktiv"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Der Messenger ist in dieser Kampagne nicht aktiviert",
        )
    return viewer


router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/kontakte",
    tags=["kontakte"],
    dependencies=[Depends(require_campaign_zugang), Depends(require_messenger_active)],
)


async def _eigener_pc(viewer: Viewer) -> str:
    """Die eigene Person — ohne sie gibt es keine Kontakte."""
    if not viewer.person_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kein eigener Charakter")
    return viewer.person_id


async def _kontakt_oder_404(campaign_id: str, kontakt_id: str, viewer: Viewer) -> dict:
    """Holt einen Kontakt und prüft, ob der Betrachter ihn sehen darf.

    404 statt 403: ein Spieler soll nicht erfahren, dass es das
    Kontaktwissen eines anderen überhaupt gibt.
    """
    roh = await repository.hole(campaign_id, kontakt_id)
    if roh is None or not darf_kontakt_sehen(roh, viewer):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kontakt nicht gefunden")
    return roh


@router.get("", response_model=list[KontaktResponse])
async def meine_kontakte(campaign_id: str, viewer: Viewer = Depends(get_viewer)):
    """Das eigene Kontaktverzeichnis."""
    pc_id = await _eigener_pc(viewer)
    roh = await repository.liste_fuer_pc(campaign_id, pc_id)
    return [kontakt_fuer_viewer(r, viewer) for r in roh]


@router.get("/uebersicht", response_model=list[KontaktGmResponse],
            dependencies=[Depends(require_campaign_gm)])
async def alle_kontakte(campaign_id: str):
    """Wer kennt wen — nur für die Spielleitung."""
    return [kontakt_fuer_gm(r) for r in await repository.liste_fuer_gm(campaign_id)]


@router.get("/anfragen", response_model=list[KontaktGmResponse],
            dependencies=[Depends(require_campaign_gm)])
async def anfragen(campaign_id: str):
    """Offene Kontaktanfragen, über die entschieden werden muss."""
    return [kontakt_fuer_gm(r) for r in await repository.offene_anfragen(campaign_id)]


@router.post("", response_model=KontaktGmResponse, dependencies=[Depends(require_campaign_gm)])
async def kontakt_anlegen(campaign_id: str, body: KontaktCreate):
    """Die Spielleitung legt Kontaktwissen von Hand an."""
    roh = await repository.anlegen(campaign_id, body.pcId, body.npcId, body.stufe)
    if roh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PC oder NPC nicht gefunden")
    return kontakt_fuer_gm(roh)


@router.patch("/{kontakt_id}", response_model=KontaktGmResponse,
              dependencies=[Depends(require_campaign_gm)])
async def kontakt_aendern(campaign_id: str, kontakt_id: str, body: KontaktGmUpdate):
    """Stufe, Namenskenntnis oder Alias ändern — Sache der Spielleitung."""
    roh = await repository.aendern(campaign_id, kontakt_id, body.model_dump())
    if roh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kontakt nicht gefunden")
    return kontakt_fuer_gm(roh)


@router.delete("/{kontakt_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_campaign_gm)])
async def kontakt_loeschen(campaign_id: str, kontakt_id: str):
    if not await repository.loeschen(campaign_id, kontakt_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kontakt nicht gefunden")


@router.put("/{kontakt_id}/alias", response_model=KontaktResponse)
async def alias_setzen(
    campaign_id: str, kontakt_id: str, body: AliasUpdate, viewer: Viewer = Depends(get_viewer)
):
    """Den eigenen Alias für diesen NPC setzen ("der Schläger vom Hafen").

    **Vom Spieler aufrufbar**: es ist sein eigener Merkzettel. Der
    NPC-Standard bleibt der Spielleitung vorbehalten, weil er alle Kontakte
    ohne eigenen Alias betrifft.
    """
    await _kontakt_oder_404(campaign_id, kontakt_id, viewer)
    roh = await repository.aendern(campaign_id, kontakt_id, {"alias": body.alias})
    return kontakt_fuer_viewer(roh, viewer)


@router.put("/{kontakt_id}/notizen", response_model=KontaktResponse)
async def notizen_setzen(
    campaign_id: str, kontakt_id: str, body: NotizenUpdate, viewer: Viewer = Depends(get_viewer)
):
    """Persönliche Notizen zu diesem Kontakt — nur für einen selbst."""
    await _kontakt_oder_404(campaign_id, kontakt_id, viewer)
    roh = await repository.aendern(campaign_id, kontakt_id, {"persoenlicheNotizen": body.inhalt})
    return kontakt_fuer_viewer(roh, viewer)


@router.post("/{kontakt_id}/anfrage", response_model=KontaktResponse)
async def kontakt_anfragen(campaign_id: str, kontakt_id: str, viewer: Viewer = Depends(get_viewer)):
    """Eine Kontaktanfrage stellen — erst nach einem Gespräch, und nur einmal.

    **Vom Spieler aufrufbar**: die Anfrage ist seine Handlung. Sie setzt nur
    ein Kennzeichen; entschieden wird an `/anfrage/entscheiden`, und das
    verlangt die Spielleitung.
    """
    roh = await _kontakt_oder_404(campaign_id, kontakt_id, viewer)
    if not kann_kontakt_anfragen(roh.get("stufe"), roh.get("kontaktAnfrageStatus")):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Eine Anfrage ist erst nach einem Gespräch möglich — und nur einmal",
        )
    aktualisiert = await repository.aendern(
        campaign_id, kontakt_id, {"kontaktAnfrageStatus": "OFFEN"}
    )
    return kontakt_fuer_viewer(aktualisiert, viewer)


@router.post("/{kontakt_id}/anfrage/entscheiden", response_model=KontaktGmResponse,
             dependencies=[Depends(require_campaign_gm)])
async def anfrage_entscheiden(campaign_id: str, kontakt_id: str, body: AnfrageEntscheidung):
    """Die Spielleitung antwortet als der NPC.

    Annahme schaltet den Einzelchat frei (Stufe KONTAKT_AUSGETAUSCHT).
    """
    roh = await repository.hole(campaign_id, kontakt_id)
    if roh is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kontakt nicht gefunden")

    aenderung: dict = {"kontaktAnfrageStatus": "ANGENOMMEN" if body.annehmen else "ABGELEHNT"}
    if body.annehmen:
        aenderung["stufe"] = "KONTAKT_AUSGETAUSCHT"

    return kontakt_fuer_gm(await repository.aendern(campaign_id, kontakt_id, aenderung))


@router.post("/erkennen", response_model=list[KontaktGmResponse],
             dependencies=[Depends(require_campaign_gm)])
async def automatisch_erkennen(campaign_id: str):
    """Legt fehlendes GESEHEN-Wissen aus sichtbaren Graphwegen an.

    Höchstens sieben Kanten, und **niemals hochstufen**: ein bestehendes
    GESPROCHEN bleibt unangetastet (Spec).
    """
    nodes, edges = await repository.graph_daten(campaign_id)
    pcs = [n for n in nodes if n.get("kind") == "Person" and n.get("personType") == "PC"]

    neu: list[dict] = []
    for pc in pcs:
        gefunden = erreichbare_npcs(
            pc["id"], nodes, edges, viewer_role="PLAYER", viewer_person_id=pc["id"]
        )
        for npc_id in gefunden:
            # anlegen() ist ein MERGE mit ON CREATE — vorhandenes Wissen
            # bleibt unverändert.
            roh = await repository.anlegen(campaign_id, pc["id"], npc_id, "GESEHEN")
            if roh:
                neu.append(roh)

    return [kontakt_fuer_gm(r) for r in neu]


# ------------------------------------------------------------------- Messenger


def _nachricht_fuer(roh: dict, betrachter_id: str, alias: str) -> NachrichtResponse:
    """Eine Nachricht aus Sicht des Betrachters.

    Der Absender ist beim Spieler **immer der Alias des NPC** — nie
    "Spielleitung", auch wenn die SL getippt hat.
    """
    von_mir = roh.get("vonId") == betrachter_id
    return NachrichtResponse(
        id=roh["id"],
        inhalt=roh.get("inhalt") or "",
        erstelltAm=roh.get("erstelltAm") or "",
        vonMir=von_mir,
        absender="" if von_mir else alias,
        gelesen=bool(roh.get("gelesenAm")),
    )


@router.get("/{kontakt_id}/chat", response_model=ChatResponse)
async def chat_lesen(campaign_id: str, kontakt_id: str, viewer: Viewer = Depends(get_viewer)):
    """Der Nachrichtenverlauf eines Kontakts."""
    roh = await _kontakt_oder_404(campaign_id, kontakt_id, viewer)
    offen = ist_mindestens_stufe(roh.get("stufe"), "KONTAKT_AUSGETAUSCHT")
    alias = effektiver_alias(
        (roh.get("npcAlias") or "").strip() or standard_alias(roh.get("npcRasse")),
        roh.get("persoenlicherAlias"),
    )

    verlauf: list[NachrichtResponse] = []
    if offen:
        # Beim Öffnen gilt die Post als gelesen — sonst bliebe der Zähler
        # ewig stehen.
        if viewer.role != "GM":
            await repository.markiere_gelesen(campaign_id, roh["pcId"], roh["npcId"])
        betrachter = viewer.person_id if viewer.role != "GM" else roh["npcId"]
        verlauf = [
            _nachricht_fuer(n, betrachter or "", alias)
            for n in await repository.nachrichten(campaign_id, roh["pcId"], roh["npcId"])
        ]

    return ChatResponse(
        kontaktId=roh["id"],
        npcId=roh["npcId"],
        alias=alias,
        chatOffen=offen,
        nachrichten=verlauf,
    )


@router.post("/{kontakt_id}/chat", response_model=NachrichtResponse)
async def nachricht_senden(
    campaign_id: str, kontakt_id: str, body: NachrichtCreate, viewer: Viewer = Depends(get_viewer)
):
    """Eine Nachricht schreiben.

    **Vom Spieler aufrufbar** — das ist der Zweck des Messengers. Die SL
    schreibt hier als der NPC; ihr Name taucht nirgends auf.
    """
    roh = await _kontakt_oder_404(campaign_id, kontakt_id, viewer)

    if not ist_mindestens_stufe(roh.get("stufe"), "KONTAKT_AUSGETAUSCHT"):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Der Chat ist erst nach einer angenommenen Kontaktanfrage offen",
        )

    if viewer.role == "GM":
        von_id, an_id = roh["npcId"], roh["pcId"]
    else:
        von_id, an_id = roh["pcId"], roh["npcId"]

    gesendet = await repository.sende(campaign_id, von_id, an_id, body.inhalt, viewer.role)
    alias = effektiver_alias(
        (roh.get("npcAlias") or "").strip() or standard_alias(roh.get("npcRasse")),
        roh.get("persoenlicherAlias"),
    )
    return _nachricht_fuer(gesendet, von_id, alias)
