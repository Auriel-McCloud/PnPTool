# NeotopiA – Regeln

Transkription des Regelteils aus dem Excel-Sheet `Regeln` (Zeilen 47–108) aus `Neotopia.xlsx` (Stand der Quelle: 29.08.2026) — direkt im Anschluss an die Charaktererschaffung (`Neotopia_Charaktererschaffung.md`). Gegenstände/Preise siehe `Neotopia_Gegenstaende.md`.

## Proben

Gewürfelt wird mit einem Pool aus zehnseitigen Würfeln: 1–5 ist ein Misserfolg, 6–10 (0) ist ein Erfolg.

## Kritischer Erfolg / Patzer

- **Kritisch:** 2 Zehnen zählen wie 4 Erfolge, 3 Zehnen wie 6 Erfolge, ...
- **Patzer:** Hälfte der Würfel zeigt 1.
- Es gibt keine „Zahlenwerte" — alle Werte sind Würfel, gezählt wird das Ergebnis.

## Kampf

### Initiative (Kampfreihenfolge)

Geistesschärfe + Geschicklichkeit + Cyberware-Mod ergibt die Reihenfolge. Zwei Regeln gelten dabei:
1. Matrixnutzer vor Nahkämpfer vor Fernkämpfer.
2. In umgekehrter Reihenfolge sagen alle an, was sie vorhaben — die schnellste Person kann so reagieren; dann werden in der „richtigen" Reihenfolge die Proben gewürfelt.

### Treffen

- **Angriff:** Geschick + Kampfskill + Mod
- **vs. Ausweichen:** Geschick + Sportlichkeit (kumulativer −1-Malus pro Einsatz in derselben Kampfrunde)
- **vs. Parieren:** Geschick + Waffenfertigkeit — gegen Fernkampf nur mit Cyberware/Magie möglich (ebenfalls kumulativer −1 pro Einsatz/Runde)
- Netto-Erfolge werden zu Bonuswürfeln (BW) beim Schaden.

### Schaden

- **Fernkampf:** Waffenschaden + BW vs. Rüstungsbonus
- **Nahkampf:** Waffenschaden + Stärke + BW vs. Rüstungsbonus

### Schadensarten

Drei Arten: Schlag / Tödlich (X) / Unheilbar (X)

### Heilen

- Schlagschaden heilt Widerstandskraft-Wert über Nacht.
- Tödlicher Schaden heilt ½ Widerstandskraft-Wert über Nacht (nur bei Behandlung).
- Unheilbarer Schaden heilt Widerstandskraft-Wert über (7 − Widerstandskraft) Wochen (nur bei Behandlung).

### Rüstung

Der Rüstungsbonus wird addiert.

> 🥚 **Randnotiz im Excel (Zeile 78):** *„David Martinez – Edgerunner-Fans... scrollen auf 42(0), denn da steht die Antwort... am besten ignorieren"* — ein Insider-Scherz von Mark, keine Regel.

## Magie

Nach dem Zaubern muss ein Willenskraftwurf gemacht werden, der die Netto-Erfolge des Arete-Wurfs erreichen oder übersteigen muss — sonst verursacht die Magie Schaden in Höhe der nicht abgedeckten Erfolge. Erfolge können entweder in Power oder in Zeit investiert werden.

### Arete (Magie)

- Arete ist der Magiewert.
- Der Magier kann Bonuswürfel bis zur Höhe seiner Willenskraft hinzufügen („Wilde Magie") — kann auch unkontrolliert an Orten hoher Magie auftreten.
- Ein **kontrollierter** Zauber würfelt nur den Arete-Wert. Bei Wilder Magie muss vorher ein Zielwert festgelegt werden; wird er unterschritten, ist die Probe gescheitert.
- Nach einem erfolgreichen wilden Zauber: Willenskraftwurf gegen die Erfolgszahl des Zaubers (entfällt, wenn die Erfolge exakt dem Zielwert entsprechen). Die Differenz wird als Schaden/Lebenspunkte abgezogen.
- Kritische Treffer zählen beim Zielwert **nicht** als zusätzliche Erfolge — nur Netto-Erfolge zählen; bei einem kritischen Treffer führt „zu wenig" trotzdem zum Erfolg.
- Sphärenpunkte beschreiben die magischen Fähigkeiten/Limitierungen des Magiers und zählen **nicht** als Bonuswürfel.

### Sphären

Stufen: 1 wahrnehmbar · 2 Manipulation bis ~50 cm³ · 3 bis ~4 m³ · 4 bis Hausgröße · 5 „Nach meiner Größe beurteilst du mich, tust du das?"

| Sphäre | Beschreibung |
|---|---|
| Korrespondenz | Raummagie, „Entfernung? Was ist das?" |
| Entropie | Wahrscheinlichkeiten, „Glück? HA!" |
| Kräfte* | Physikalische Kräfte manipulieren |
| Leben | Jede lebende Materie unterliegt meinem Willen |
| Materie | Alles was nicht lebt, beugt sich meinem Willen |
| Gedanken | „Das sind nicht die Droiden, die ihr sucht" |
| Ursprung | Reine Magie — nötig für Verzauberungen und um Magie in Objekten zu festigen; ermöglicht auch Lichtschwerter... und KAME-HAME-HA... |
| Geister | Medium-Fähigkeiten, Reisen in die Astralwelt, Interaktion von Geistern mit der Realität |
| Zeit | Die schwierigste aller Sphären — schon 3 Minuten zurückreisen kann retten, aber Vorsicht vor 300 Jahren (da gab's keine Magie); die meisten Zeitmagier bleiben für immer verschollen |

*Schaden durch Kräfte ist automatisch +1.*

### NeuroWeaving

Gleiche Grundregeln wie Arete (inkl. Willenskrafteinsatz und Konsequenzen), aber:
- Punkte in NeuroWeaving-Fähigkeiten gelten als Bonuswürfel für die jeweilige Aktion.
- Der Technomancer (NeuroWeaver) kann auch NeuroWeaving-Fertigkeiten nutzen, in denen er keine Punkte hat.

### Cyberwall

Wird von einem Decker (Hacker) benötigt, der Geräte verwendet. Die Verteidigungsfähigkeit eines NeuroWeavers bestimmt sich über Fassung + Geistesschärfe.

### Decking

Beim Arbeiten mit Cyberdecks wird i. d. R. Intelligenz + Matrix zum Hacken verwendet. Die Fertigkeiten des Cyberdecks (abgekürzt B/S/D/K) geben Bonuswürfel für die jeweilige Aktion.

### Riggen

Steuern von Drohnen — im Gegensatz zu FPV ein körperliches Eintauchen in die Drohne (Sensoren nicht vergessen, sonst spürt man nichts). In der Drohne können eigene Werte genutzt werden, gedeckelt auf die Stufe der Drohne (z. B. Schusswaffen 4 wird bei einer Stufe-3-Drohne zu 3). Der Rigger-Skill kann alle körperlichen Skills ersetzen, zu denen die Drohne selbstständig fähig sein sollte.

### Drohnen / Fahrzeuge

Beim Kauf einer Drohne/eines Fahrzeugs wird deren Stufe festgelegt; die Stufe kann dabei beliebig auf Werte und Fertigkeiten verteilt werden.
- Gesundheit = Stufe
- Widerstand = Schadensreduktion
- Angriff = Treffen & Schaden
- Agilität = Geschwindigkeit
- Fertigkeiten werden zu den Drohnen-Attributen addiert, wenn kompatibel.
