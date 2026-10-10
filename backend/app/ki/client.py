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

# Für generiere_text (nur die Beratung): wenn der aufgelöste Provider
# fehlschlägt (z.B. Gemini dauerhaft überlastet, siehe gemini.py), automatisch
# den jeweils anderen probieren, bevor der Nutzer eine Fehlermeldung sieht.
# Mark (07.10.2026): "schreib bitte oben... ob die Nachricht von Gemini oder
# Mistral kommt" — darum gibt generiere_text zurück, WELCHER Anbieter die
# Antwort tatsächlich geliefert hat, nicht nur den Text.
_FALLBACK_PROVIDER = {"gemini": "mistral", "mistral": "gemini"}


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
    """Wie generiere_text: schlägt der aufgelöste Provider fehl (z.B. Gemini
    503 "high demand"), wird automatisch einmal der jeweils andere Anbieter
    versucht, bevor der Aufrufer eine Fehlermeldung sieht (10.10.2026, Mark:
    Shop-"Mit KI anlegen" blieb bei überlastetem Gemini wirkungslos stehen,
    obwohl Mistral für dieselbe Kampagne funktioniert hätte). Anders als
    generiere_text muss der Aufrufer hier nicht wissen, WELCHER Anbieter
    geantwortet hat — reiner Resilienz-Fallback, kein sichtbarer A/B-Vergleich."""
    aktiv = _aufloesen(None, await _kampagnen_provider(campaign_id))
    if aktiv not in _GUELTIGE_PROVIDER:
        raise KiFehler(f"Unbekannter KI_PROVIDER '{aktiv}' (erwartet: gemini, mistral)")

    reihenfolge = [aktiv, _FALLBACK_PROVIDER[aktiv]]
    fehler_pro_provider: dict[str, str] = {}
    for kandidat in reihenfolge:
        try:
            if kandidat == "mistral":
                return await mistral.generiere_json(prompt, system, schema)
            return await gemini.generiere_json(prompt, system, schema)
        except (gemini.GeminiFehler, mistral.MistralFehler) as e:
            fehler_pro_provider[kandidat] = str(e)

    teile = " / ".join(f"{k}: {v}" for k, v in fehler_pro_provider.items())
    raise KiFehler(f"Alle KI-Anbieter nicht erreichbar — {teile}")


async def generiere_text(
    nachrichten: list[dict],
    system: str = "",
    *,
    provider: str | None = None,
    campaign_id: str | None = None,
) -> tuple[str, str]:
    """Freier Chat-Text (Beratung). Dieselbe Provider-Wahl wie generiere_json,
    zusätzlich mit `provider` überschreibbar — der Beratungs-Dropdown nutzt
    das für einen Aufruf, ohne die Kampagnen-Einstellung zu ändern.

    Gibt `(antwort_text, tatsaechlicher_provider)` zurück: schlägt der
    aufgelöste Provider fehl, wird automatisch einmal der andere versucht
    (z.B. Gemini dauerhaft überlastet -> Mistral übernimmt für diese eine
    Nachricht) — `tatsaechlicher_provider` sagt dem Frontend ehrlich, wer
    tatsächlich geantwortet hat, nicht nur wer angefragt wurde.
    """
    aktiv = _aufloesen(provider, await _kampagnen_provider(campaign_id))
    if aktiv not in _GUELTIGE_PROVIDER:
        raise KiFehler(f"Unbekannter KI_PROVIDER '{aktiv}' (erwartet: gemini, mistral)")

    reihenfolge = [aktiv, _FALLBACK_PROVIDER[aktiv]]
    fehler_pro_provider: dict[str, str] = {}
    for kandidat in reihenfolge:
        try:
            if kandidat == "mistral":
                text = await mistral.generiere_text(nachrichten, system)
            else:
                text = await gemini.generiere_text(nachrichten, system)
            return text, kandidat
        except (gemini.GeminiFehler, mistral.MistralFehler) as e:
            fehler_pro_provider[kandidat] = str(e)

    teile = " / ".join(f"{k}: {v}" for k, v in fehler_pro_provider.items())
    raise KiFehler(f"Alle KI-Anbieter nicht erreichbar — {teile}")
