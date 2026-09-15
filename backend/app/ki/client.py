"""Wählt den aktiven KI-Anbieter (Gemini oder Mistral) — eine Stelle statt
überall `if settings.ki_provider == ...` zu wiederholen.

`routes.py` importiert nur `generiere_json` von hier und weiß nichts davon,
welcher Anbieter gerade läuft. Umschalten geht über `KI_PROVIDER` in der
.env, ohne Code-Änderung.
"""

from app.config import settings
from app.ki import gemini, mistral


class KiFehler(Exception):
    """Lesbare Fehlermeldung, unabhängig vom Anbieter dahinter."""


async def generiere_json(
    prompt: str,
    system: str = "",
    schema: dict | None = None,
) -> dict:
    provider = settings.ki_provider.lower()
    try:
        if provider == "mistral":
            return await mistral.generiere_json(prompt, system, schema)
        if provider == "gemini":
            return await gemini.generiere_json(prompt, system, schema)
        raise KiFehler(f"Unbekannter KI_PROVIDER '{settings.ki_provider}' (erwartet: gemini, mistral)")
    except (gemini.GeminiFehler, mistral.MistralFehler) as e:
        raise KiFehler(str(e)) from e
