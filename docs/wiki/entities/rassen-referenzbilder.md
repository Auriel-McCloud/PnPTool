---
title: Rassen-Referenzbilder für die Bildgenerierung
created: 2026-11-20
updated: 2026-11-20
type: entität
tags: [ki-integration, rassen]
sources: [../../../CLAUDE.md, ../../api/ki.md, ../../api/rassen.md, ../../../backend/app/rassen/referenz.py]
status: aktuell
---

# Rassen-Referenzbilder für die Bildgenerierung

## Skizze (20.11.2026, Mark)

Bilder für PCs und NPCs bestimmter Rassen sollen wie diese Rasse aussehen.
Dafür soll es Vorlagen geben. Jedes generierte Bild wird bei der Rasse
abgelegt, damit Varietät entsteht, und beim nächsten Mal wird zufällig eine
dieser Vorlagen gezogen. An der Rasse soll einstellbar sein, ob Bilder als
Referenz genommen werden. Gewünscht an für Dug'Rah, Sephari und Quill, beim
Rest erstmal aus, aber als Option. Die Bilder sollen sichtbar sein, damit
welche aussortiert werden können, die nicht passen oder Probleme machen.

## Entscheidung (20.11.2026)

Mark: in den Pool kommt ein Bild **nur, wenn das Portrait übernommen wurde**.
Verworfene Vorschauen nicht. Der Pool startet leer; die ersten Vorlagen lädt
die SL im Baukasten hoch. Vorhandene Kampagnenportraits werden nicht
mitgenommen. **Annahme:** Nebenfiguren zählen mit, weil sie dieselbe
Personen-Galerie nutzen. Critter, KI, Drohnen, Orte und Gegenstände nicht.

## Gebaut (20.11.2026)

- Schalter `referenzAktiv` und Liste `referenzbilder` an der Rasse, nicht am
  Namen. Start an nur für Dug'Rah, Sephari und Quill, und nur solange das
  Feld noch fehlt (`referenzAktiv IS NULL`). Danach entscheidet der Schalter.
- Galerie im Rassen-Baukasten: sehen, Vorlage hochladen, Aussortieren mit
  Bestätigung. Wegwerfen löscht die Kopie unter `uploads/rassen/{id}/`, nicht
  das Portrait der Figur. Das Kartenbild der Infobox bleibt getrennt.
- Generierung (SL an PC/NPC/Nebenfigur, Spieler am eigenen Portrait): ist der
  Schalter an und der Pool nicht leer, geht zufällig eine vorhandene Datei
  mit. Gemini als Bild, Fooocus als ImagePrompt (kein FaceSwap). Hinweis im
  Popup: `Referenz: Name`. Leerer Pool: Generierung ohne Vorlage.
- In den Pool nur nach „Übernehmen“, nicht bei Datei-Upload oder Skizze.
- Lokaler Fooocus-Wrapper (`C:/DEV/Fooocus/pnptool_server.py`, nicht im
  Repo) muss neu gestartet werden, sonst meldet die lokale Generierung mit
  Vorlage, dass der Wrapper die Referenz noch nicht kennt. Cloud braucht das
  nicht.

## Bugfix (20.11.2026)

Mark: erster Generierungsversuch mit Quill-Referenzbild scheiterte mit
„Gemini liefert kein Bild (Grund: No Image)“. `NO_IMAGE` ist laut
Google-API-Doku Modell-Unzuverlässigkeit, kein bewusster Inhalts-Block —
`generiere_bild`/`_generiere_gemini` versucht seither bei `NO_IMAGE`/
`IMAGE_OTHER` automatisch bis zu 2× erneut, bevor der Fehler durchschlägt.
Gleichzeitig läuft `/bild-generieren` jetzt als Hintergrund-Job + Polling
(dasselbe Muster wie `/massenidee`), weil die Generierung mit Referenzbild
mehrere zig Sekunden dauert und ein Netzwerk-Hänger den einzelnen langen
Request sonst mit „Failed to fetch“ killt. Siehe `docs/api/ki.md`,
`CLAUDE.md`.

Siehe [[ki-integration]], [[../concepts/rassen]], [[rassen-baukasten-feature]].

## Offene Idee (20.11.2026): Rassen-Beschreibung fehlt im Bild-Prompt

Mark, am Live-Beispiel Quill ("Häretiker"): der Bild-Prompt-Vorschlag (Schritt
1 vor der eigentlichen Generierung) kennt die Rassen-Beschreibung
(`Rasse.beschreibung`, z.B. Quill: "Kleine geschickte, schlaue Aliens.
Erinnern an humanoide Rote Pandas.") NIRGENDS — weder über die eigene
Personen-Beschreibung noch über `sammle_kontext` (zieht Person/Ort/Event/
**Fraktion**/Gegenstand/WikiSeite, aber keine `Rasse`-Knoten). Die Text-KI
rät deshalb allein vom Rassennamen und assoziierte bei "Quill" frei
"feather-like quills"/"avian" (Beleg: KI-Protokoll-Eintrag 20.11.2026
08:06 UTC) — obwohl ein korrektes Referenzbild mitgeschickt wurde, hat der
widersprüchliche Text-Prompt offenbar mehr Gewicht bekommen als das Bild.

**Offene Achsen, Formular ohne Antwort geblieben:**
- Reichweite: nur in den Bild-Prompt-Vorschlag, oder generell in
  `sammle_kontext` (dann wissen auch NPC-/Story-Generierung die Rassen-Lore)?
- Verhalten bei vorhandenem Referenzbild: Text-Prompt automatisch
  zurückhaltender beim Aussehen (Bild soll führen), oder weiterhin frei
  beschreiben, nur mit korrekter Rassen-Info?

Status: offen, nicht gebaut.
