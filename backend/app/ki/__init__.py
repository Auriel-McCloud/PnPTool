"""KI-Anbindung (Google Gemini) — dünner Client über die REST-API.

Bewusst schlank: ein einziger Aufrufpfad, der Gemini einen Auftrag gibt und
strukturiertes JSON zurückbekommt. Die eigentlichen Prompts (was für ein
NPC, welcher Story-Part) leben in routes.py, nicht hier — hier steht nur die
Transport-Schicht.
"""
