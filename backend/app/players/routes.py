from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_claims, require_campaign_gm
from app.auth.security import create_access_token
from app.entities.repository import PERSON_FIELDS, create_node, get_node, update_node
from app.entities import repository as entities_repository
from app.items.routes import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, UPLOAD_DIR
from app.entities.schemas import PersonCreate
from app.ki.bildgenerierung import BildgenerierungFehler, generiere_bild
from app.ki.routes import BildGenerierenInput, _bild_prompt_vorschlagen
from app.players import repository
from app.players.schemas import (
    CharakterWaehlenRequest,
    CharakterZuordnenRequest,
    LoginRequest,
    PasswortRequest,
    SpielerAnlegenRequest,
    SpielerMeResponse,
    SpielerResponse,
    VorgefertigterCharakter,
)

# Anmeldung laeuft ohne bestehende Sitzung.
login_router = APIRouter(prefix="/api/spieler", tags=["players"])
# Verwaltung durch die Spielleitung.
gm_router = APIRouter(
    prefix="/api/campaigns/{campaign_id}/spieler",
    tags=["players"],
    dependencies=[Depends(require_campaign_gm)],
)

SESSION_COOKIE = "pnptool_session"


def _antwort(spieler: dict) -> SpielerMeResponse:
    return SpielerMeResponse(
        spielerId=spieler["id"],
        benutzername=spieler["benutzername"],
        campaignId=spieler["campaignId"],
        campaignName=spieler["campaignName"],
        personId=spieler["personId"],
        personName=spieler["personName"],
        hatPasswort=bool(spieler.get("passwortHash")),
        personBildUrl=spieler.get("personBildUrl"),
    )


async def require_spieler(claims: dict = Depends(get_current_claims)) -> dict:
    if claims.get("role") != "PLAYER":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "player role required")
    spieler = await repository.get_spieler(claims["sub"])
    if spieler is None:
        # Zugang inzwischen geloescht - fuer den Aufrufer dasselbe wie
        # "nicht angemeldet", er soll sich neu anmelden.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Zugang existiert nicht mehr")
    return spieler


@login_router.post("/login", response_model=SpielerMeResponse)
async def login(body: LoginRequest, response: Response):
    """Anmeldung mit Benutzername, Passwort nur falls gesetzt.

    Gross- und Kleinschreibung spielt keine Rolle. Ist kein Passwort
    hinterlegt, genuegt der Name - in einer privaten Runde soll sich niemand
    erst eines ausdenken muessen.
    """
    spieler = await repository.finde_spieler(body.benutzername)
    if spieler is None or not repository.pruefe_passwort(body.passwort, spieler.get("passwortHash")):
        # Dieselbe Meldung fuer "gibt es nicht" und "falsches Passwort" -
        # sonst liesse sich herausfinden, welche Namen vergeben sind.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Benutzername oder Passwort stimmt nicht")

    token = create_access_token({"role": "PLAYER", "sub": spieler["id"], "name": spieler["benutzername"]})
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return _antwort(spieler)


@login_router.get("/me", response_model=SpielerMeResponse)
async def spieler_me(spieler: dict = Depends(require_spieler)):
    return _antwort(spieler)


@login_router.get("/vorgefertigte", response_model=list[VorgefertigterCharakter])
async def vorgefertigte_liste(spieler: dict = Depends(require_spieler)):
    """Vorgebaute PCs zur Auswahl im Ersteinstiegs-Fenster.

    Nur sinnvoll, solange der Spieler noch keinen eigenen Charakter hat —
    die Route liefert trotzdem immer die aktuelle Liste, die Sperre gegen
    einen zweiten Charakter sitzt in `charakter_waehlen`.
    """
    return await repository.verfuegbare_pcs(spieler["campaignId"])


@login_router.post("/charakter-waehlen", response_model=SpielerMeResponse)
async def charakter_waehlen(body: CharakterWaehlenRequest, spieler: dict = Depends(require_spieler)):
    """Wählt einen vorgebauten, noch freien PC fix für diesen Spieler.

    Atomar geprüft in `repository.charakter_waehlen` — zwei Spieler, die
    gleichzeitig denselben Charakter antippen, können ihn nicht beide
    bekommen. 409 sowohl wenn der Spieler bereits einen Charakter hat als
    auch wenn der gewählte PC inzwischen vergeben oder nicht mehr frei ist;
    beides braucht dieselbe Reaktion beim Spieler ("neu laden, nochmal
    wählen"), eine feinere Unterscheidung wäre hier kein echter Zugewinn.
    """
    if spieler.get("personId"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Du hast bereits einen Charakter.")

    erfolg = await repository.charakter_waehlen(spieler["id"], spieler["campaignId"], body.personId)
    if not erfolg:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Dieser Charakter ist gerade nicht mehr frei — bitte die Liste neu laden.",
        )

    frisch = await repository.get_spieler(spieler["id"])
    assert frisch is not None
    return _antwort(frisch)


@login_router.post("/charakter-neu", response_model=SpielerMeResponse)
async def charakter_neu_bauen(spieler: dict = Depends(require_spieler)):
    """Legt einen frischen, leeren PC an und ordnet ihn sofort dem Spieler zu —
    Startpunkt für die selbstständige Charaktererstellung im Ersteinstiegs-
    Fenster. Der Name ist ein Platzhalter; die Erstellung lässt ihn den
    echten Namen selbst vergeben (siehe traits/routes.py::ErstellungInput).
    """
    if spieler.get("personId"):
        raise HTTPException(status.HTTP_409_CONFLICT, "Du hast bereits einen Charakter.")

    campaign_id = spieler["campaignId"]
    neue_person = await create_node(
        "Person",
        PERSON_FIELDS,
        campaign_id,
        PersonCreate(name="Neuer Charakter", personType="PC").model_dump(),
    )
    erfolg = await repository.charakter_waehlen(spieler["id"], campaign_id, neue_person["id"])
    if not erfolg:
        # Kann eigentlich nur bei einem zwischenzeitlich doch gesetzten
        # eigenen Charakter passieren (Doppelklick) — der frische, noch
        # ungebundene PC bliebe sonst als Leiche stehen.
        await entities_repository.delete_node("Person", campaign_id, neue_person["id"])
        raise HTTPException(status.HTTP_409_CONFLICT, "Du hast bereits einen Charakter.")

    frisch = await repository.get_spieler(spieler["id"])
    assert frisch is not None
    return _antwort(frisch)


@login_router.post("/passwort", response_model=SpielerMeResponse)
async def passwort_setzen(body: PasswortRequest, spieler: dict = Depends(require_spieler)):
    """Der Spieler vergibt sich selbst ein Passwort - oder entfernt es wieder."""
    await repository.setze_passwort(spieler["id"], body.passwort)
    frisch = await repository.get_spieler(spieler["id"])
    assert frisch is not None
    return _antwort(frisch)


@login_router.post("/mein-bild", response_model=SpielerMeResponse)
async def eigenes_charakterportrait_hochladen(
    file: UploadFile = File(...), spieler: dict = Depends(require_spieler)
):
    """Charakterportrait für den eigenen zugeordneten Charakter.

    Anders als bei allen anderen Bild-Uploads im Projekt bewusst KEIN
    `require_campaign_gm` — Mark, 22.09.2026: Spieler haben aktuell keine
    Möglichkeit, selbst ein Bild für ihren Charakter zu setzen. Schreibt
    direkt auf den zugeordneten `Person`-Knoten (dasselbe `bildUrl`-Feld wie
    beim SL-Upload in entities/routes.py), nur MVP-Wege (Datei/Kamera) — ein
    Zeichentool ist separat in CLAUDE.md offen notiert; KI-Bildgenerierung
    gibt es jetzt über `/mein-bild-ki-prompt` + `/mein-bild-ki` unten.
    """
    if not spieler.get("personId"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dir ist noch kein Charakter zugeordnet")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nur Bilddateien (PNG/JPEG/WEBP/GIF) erlaubt")

    inhalt = await file.read()
    if len(inhalt) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Datei zu groß (max. 8 MB)")

    campaign_id = spieler["campaignId"]
    person_id = spieler["personId"]
    if await get_node("Person", PERSON_FIELDS, campaign_id, person_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charakter nicht gefunden")

    import mimetypes
    import uuid

    ordner = UPLOAD_DIR / campaign_id
    ordner.mkdir(parents=True, exist_ok=True)
    endung = mimetypes.guess_extension(file.content_type) or ""
    name = f"portrait-{uuid.uuid4()}{endung}"
    (ordner / name).write_bytes(inhalt)

    await update_node("Person", PERSON_FIELDS, campaign_id, person_id, {"bildUrl": f"/uploads/{campaign_id}/{name}"})

    frisch = await repository.get_spieler(spieler["id"])
    assert frisch is not None
    return _antwort(frisch)


@login_router.delete("/mein-bild", response_model=SpielerMeResponse)
async def eigenes_charakterportrait_entfernen(spieler: dict = Depends(require_spieler)):
    """Entfernt das Charakterportrait wieder — Gegenstück zum Upload oben.

    Setzt `bildUrl` nur zurück (gleiches Muster wie `EntitaetsBild.tsx::
    entfernen`, PATCH mit leerem String), löscht die Datei aber nicht vom
    Datenträger — genau wie beim SL-Upload bleibt sie verwaist liegen statt
    Nebenwirkungen auf andere Referenzen zu riskieren.
    """
    if not spieler.get("personId"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dir ist noch kein Charakter zugeordnet")

    campaign_id = spieler["campaignId"]
    person_id = spieler["personId"]
    if await get_node("Person", PERSON_FIELDS, campaign_id, person_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charakter nicht gefunden")

    await update_node("Person", PERSON_FIELDS, campaign_id, person_id, {"bildUrl": ""})

    frisch = await repository.get_spieler(spieler["id"])
    assert frisch is not None
    return _antwort(frisch)


class MeinBildPromptAntwort(BaseModel):
    prompt: str


@login_router.post("/mein-bild-ki-prompt", response_model=MeinBildPromptAntwort)
async def eigenes_charakterportrait_ki_prompt(spieler: dict = Depends(require_spieler)):
    """Prompt-Vorschlag für das eigene Charakterportrait (Schritt 1 des
    KI-Bild-Popups) — nutzt dieselbe Logik wie der SL-Weg in ki/routes.py,
    hier aber ohne require_campaign_gm (Spieler dürfen ihr eigenes Portrait
    generieren, siehe Begründung beim Datei-Upload oben)."""
    if not spieler.get("personId"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dir ist noch kein Charakter zugeordnet")

    campaign_id = spieler["campaignId"]
    person = await get_node("Person", PERSON_FIELDS, campaign_id, spieler["personId"])
    if person is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Charakter nicht gefunden")

    prompt = await _bild_prompt_vorschlagen(
        campaign_id, "Person", person.get("name", ""), person.get("beschreibung", "") or ""
    )
    if not prompt:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Die KI hat keinen Prompt-Vorschlag geliefert.")
    return MeinBildPromptAntwort(prompt=prompt)


@login_router.post("/mein-bild-ki")
async def eigenes_charakterportrait_ki_generieren(
    body: BildGenerierenInput, spieler: dict = Depends(require_spieler)
):
    """Generiert eine Bildvorschau für das eigene Charakterportrait (Schritt
    2) — speichert NICHTS. Übernehmen läuft über dieselbe Upload-Route wie
    ein manuell hochgeladenes Bild (`/mein-bild`, POST mit multipart/form-data),
    das Frontend baut daraus eine Datei und schickt sie dorthin."""
    if not spieler.get("personId"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dir ist noch kein Charakter zugeordnet")

    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Der Prompt darf nicht leer sein.")

    try:
        inhalt, content_type = await generiere_bild(body.provider, prompt)
    except BildgenerierungFehler as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))

    return Response(content=inhalt, media_type=content_type)


@login_router.post("/abmelden")
async def abmelden(response: Response):
    """Meldet ab. Der Zugang bleibt bestehen - er gehoert dauerhaft zu diesem
    Spieler, anders als die frueheren Beitrittssitzungen."""
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@gm_router.get("", response_model=list[SpielerResponse])
async def spieler_liste(campaign_id: str):
    return await repository.list_spieler(campaign_id)


@gm_router.post("", response_model=SpielerResponse)
async def spieler_anlegen(campaign_id: str, body: SpielerAnlegenRequest):
    if body.personId:
        person = await get_node("Person", PERSON_FIELDS, campaign_id, body.personId)
        if person is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Person nicht gefunden")

    neu = await repository.create_spieler(campaign_id, body.benutzername, body.personId, body.passwort)
    if neu is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Diesen Benutzernamen gibt es schon")

    for s in await repository.list_spieler(campaign_id):
        if s["id"] == neu["id"]:
            return s
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Anlegen fehlgeschlagen")


@gm_router.post("/{spieler_id}/charakter", response_model=list[SpielerResponse])
async def charakter_zuordnen(campaign_id: str, spieler_id: str, body: CharakterZuordnenRequest):
    if not await repository.setze_charakter(campaign_id, spieler_id, body.personId):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spieler nicht gefunden")
    return await repository.list_spieler(campaign_id)


@gm_router.delete("/{spieler_id}", status_code=status.HTTP_204_NO_CONTENT)
async def spieler_entfernen(campaign_id: str, spieler_id: str):
    if not await repository.delete_spieler(campaign_id, spieler_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Spieler nicht gefunden")
