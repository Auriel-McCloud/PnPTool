"""Wählt den aktiven KI-Anbieter (Gemini oder Mistral) — eine Stelle statt
überall `if settings.ki_provider == ...` zu wiederholen.

`routes.py` importiert nur `generiere_json` / `generiere_text` von hier und
weiß nichts davon, welcher Anbieter gerade läuft. Drei Ebenen, von niedrig
nach hoch priorisiert:

1. `KI_PROVIDER` in der .env — Server-Standard, gilt für alle Kampagnen.
2. Kampagnen-Einstellung `kiProvider` (siehe campaigns/repository.py) — SL
   kann eine Kampagne bewusst auf einen anderen Anbieter stellen, ohne den
   Server umzustellen. Wird hier selbst nachgeladen, wenn `campaign_id`
   mitgegeben wird — die Aufrufstellen müssen die Einstellung nicht einzeln
   holen.
3. `provider`-Parameter je Aufruf — nur die Beratung nutzt das (Dropdown im
   Popup), für den direkten A/B-Vergleich innerhalb eines Gesprächs, ohne
   die Kampagnen-Einstellung dafür zu verändern.
"""

from app.config import settings
from app.ki import gemini, mistral

_GUELTIGE_PROVIDER = {"gemini", "mistral"}


class KiFehler(Exception):
    """Lesbare Fehlermeldung, unabhängig vom Anbieter dahinter."""


async def _kampagnen_provider(campaign_id: str | None) -> str | None:
    if not campaign_id:
        return None
    # Spät importiert: vermeidet einen Modul-Ladezyklus, falls campaigns
    # irgendwann selbst mal (transitiv) von ki importiert.
    from app.campaigns.repository import get_einstellungen

    einstellungen = await get_einstellungen(campaign_id)
    return einstellungen.get("kiProvider") or None


def _aufloesen(provider: str | None, kampagnen_provider: str | None) -> str:
    """Ebene 3 > Ebene 2 > Ebene 1. Ungültige/leere Werte fallen durch."""
    for kandidat in (provider, kampagnen_provider, settings.ki_provider):
        if kandidat and kandidat.lower() in _GUELTIGE_PROVIDER:
            return kandidat.lower()
    return settings.ki_provider.lower()


async def generiere_json(
    prompt: str,
    system: str = "",
    schema: dict | None = None,
    *,
    campaign_id: str | None = None,
) -> dict:
    provider = _aufloesen(None, await _kampagnen_provider(campaign_id))
    try:
        if provider == "mistral":
            return await mistral.generiere_json(prompt, system, schema)
        if provider == "gemini":
            return await gemini.generiere_json(prompt, system, schema)
        raise KiFehler(f"Unbekannter KI_PROVIDER '{provider}' (erwartet: gemini, mistral)")
    except (gemini.GeminiFehler, mistral.MistralFehler) as e:
        raise KiFehler(str(e)) from e


async def generiere_text(
    nachrichten: list[dict],
    system: str = "",
    *,
    provider: str | None = None,
    campaign_id: str | None = None,
) -> str:
    """Freier Chat-Text (Beratung). Dieselbe Provider-Wahl wie generiere_json,
    zusätzlich mit `provider` überschreibbar — der Beratungs-Dropdown nutzt
    das für einen Aufruf, ohne die Kampagnen-Einstellung zu ändern."""
    aktiv = _aufloesen(provider, await _kampagnen_provider(campaign_id))
    try:
        if aktiv == "mistral":
            return await mistral.generiere_text(nachrichten, system)
        if aktiv == "gemini":
            return await gemini.generiere_text(nachrichten, system)
        raise KiFehler(f"Unbekannter KI_PROVIDER '{aktiv}' (erwartet: gemini, mistral)")
    except (gemini.GeminiFehler, mistral.MistralFehler) as e:
        raise KiFehler(str(e)) from e
