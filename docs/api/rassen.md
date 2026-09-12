# Rassen: Baukasten und Freigabe

Wie Völker gebaut, ausgewogen gehalten und je Kampagne freigegeben werden.
Code: `backend/app/rassen/` (Katalog, Balance, Routen),
`frontend/src/rassen/` (Baukasten der Spielleitung),
`frontend/src/traits/Charaktererstellung.tsx` (Auswahl und Infobox).

---

## Zwei Ebenen

**Katalog global, Freigabe je Kampagne** (Marks Vorgabe, 11.09.2026: *"es
sollten nicht automatisch alle zur Verfügung stehen, sondern nur
ausgewählte"*).

- Der **Katalog** gehört zum Regelwerk, nicht zu einer Runde — dieselbe
  Einordnung wie beim TraitDef-Katalog. Dort baut und pflegt die
  Spielleitung.
- Die **Freigabe** ist eine Beziehung `(:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)`.
  Nur freigegebene Rassen erscheinen in der Charaktererstellung.

Eine neu gebaute Rasse ist **absichtlich noch nicht freigegeben**: sie ins
Regelwerk aufzunehmen und sie in dieser Runde zuzulassen sind zwei
Entscheidungen. Bestehende Kampagnen haben beim Einführen alle fünf
eingebauten Rassen bekommen, damit sich für sie nichts ändert.

## Die Balance-Regel — gefunden, nicht erfunden

Beim Nachrechnen der fünf gewachsenen Rassen kam heraus, dass sie **exakt**
derselben Formel folgen, die nie jemand aufgeschrieben hatte:

| Rasse  | Freie Punkte | Σ Vorteile | Summe | Σ Nachteile |
|--------|--------------|------------|-------|-------------|
| Mensch | 7+5+3 = 15   | 0          | 15    | 0           |
| Ork    | 6+5+3 = 14   | +1         | 15    | 1           |
| Elf    | 5+5+3 = 13   | +2         | 15    | 1           |
| Zwerg  | 5+5+3 = 13   | +2         | 15    | 1           |
| Troll  | 5+4+3 = 12   | +3         | 15    | 2           |

1. **Freie Punkte + Summe der positiven Modifikatoren = 15.** Ein
   Vorteilspunkt kostet genau einen freien Punkt. Er ist mehr wert (er hebt
   zusätzlich die Obergrenze), aber nicht gratis.
2. **Nachteile = aufgerundet die Hälfte der Vorteile.** Sie sind **keine
   Währung**: Nachteile bringen keine freien Punkte ein. Sonst liesse sich
   ein Min-Max-Volk bauen ("−3 Charisma, +3 Körperkraft") — und genau das ist
   in keiner der fünf Rassen passiert.

`backend/tests/test_rassen_balance.py` hält beides fest. Schlägt der erste
Test fehl, ist entweder eine Rasse aus der Balance geraten oder die Formel
wurde stillschweigend geändert.

**Der Baukasten warnt, er blockiert nicht.** Ein bewusst übermächtiges
NPC-Volk muss möglich bleiben; der Editor zeigt die Abweichung deutlich an
("18 / 15 — 3 Punkte über dem Budget"), das Speichern gelingt trotzdem.

## Erstellungsgrenze und Lebensmaximum

Zwei Deckel, deren Verwechslung ein Bug war (bis 11.09.2026 wirkte die Rasse
nach der Erstellung überhaupt nicht mehr):

| | Formel | Gilt |
|---|---|---|
| `startmaxima` | 4 + Modifikator | **nur bei der Erstellung** |
| `lebensmaxima` | Katalogmaximum (6) + Modifikator | **dauerhaft** |

Ein Troll kommt bei Körperkraft also auf 8, ein Elf bei Widerstandsfähigkeit
nur auf 5 — sichtbar als `max` am Wert des Charakterbogens. Die Erstellung
schreibt das als `maxOverride` an die `HAS_TRAIT`-Beziehung
(`traits/repository.py::setze_maxima_bulk`).

Hätte man stattdessen `startmaxima` ins Blatt geschrieben, wäre jeder Mensch
für immer bei Körperkraft 4 gefangen gewesen.

**Bestehende Charaktere** wurden beim ersten Start nachgezogen
(`rassen/repository.py::_rassenmaxima_nachtragen`) — aber nur dort, wo noch
kein Maximum stand: ein von der Spielleitung von Hand angehobener Wert (die
Elder-NPC mit Schusswaffen 8) bleibt unangetastet.

## Umbenennen ist sicher

Die Rassen-Kennung ist eine **UUID und enthält den Namen nicht**. Das ist die
Lehre aus dem Arete/Hexkraft-Doppelgänger (Stolperstein 6 in CLAUDE.md): dort
lautet die Kennung `ruleset:category:name`, weshalb ein Umbenennen einen
zweiten, leeren Knoten erzeugte statt den alten zu ändern.

`Person.rasse` hält weiterhin den **Namen** — der Wert wird an vielen Stellen
als Text gebraucht, etwa für "Unbekannter Ork" in der Spielersicht des
Kampfes. Damit dadurch nichts verwaist, zieht das Umbenennen im Baukasten den
neuen Namen auf alle betroffenen Charaktere nach.

Beim **Löschen** behalten bestehende Charaktere ihren Rassennamen als Text und
bleiben spielbar; die Rasse lässt sich nur nicht mehr neu wählen. Eine
gespielte Figur soll nicht rückwirkend rasselos werden, bloss weil im
Baukasten aufgeräumt wurde.

## Endpunkte

Basis: `/api/campaigns/{campaign_id}/rassen`

Die Pfade hängen an einer Kampagne, die **Daten** aber nicht — das ist
derselbe Zuschnitt wie bei `/chromstufen`: die Kennung im Pfad dient der
Rechteprüfung, nicht der Zuordnung.

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| GET | `` | alle mit Zugang | Die in dieser Kampagne wählbaren Rassen |
| GET | `/katalog` | **nur SL** | Alle Rassen des Regelwerks, mit Freigabe-Häkchen |
| POST | `` | nur SL | Neue Rasse anlegen (noch nicht freigegeben) |
| PATCH | `/{id}` | nur SL | Bearbeiten; Umbenennen wird nachgezogen |
| DELETE | `/{id}` | nur SL | Aus dem Regelwerk entfernen |
| PUT | `/freigabe` | nur SL | Vollständige Auswahl für diese Kampagne setzen |
| POST | `/{id}/bild` | nur SL | Bild für die Infobox |

Der Katalog ist bewusst SL-only: dass es neben den spielbaren Völkern noch
andere gibt (oder welche gerade gebaut werden), ist Sache der Spielleitung.
Was in dieser Runde wählbar ist, sieht der Spieler unter `GET ``.

Jede Antwort trägt die `bilanz` mit (siehe oben) — Übersicht und Editor
zeigen damit dieselbe Bewertung, die auch beim Speichern gilt, ohne die
Formel im Frontend nachzubauen.

## Datenmodell (Neo4j)

```cypher
(:Rasse {
  id: "uuid",                       // NICHT aus dem Namen abgeleitet
  ruleset: "neotopia",
  name: "Troll",
  beschreibung: "Wuchtig und schwer umzuwerfen…",
  bildUrl: "/uploads/…",
  modifikatoren: '{"Körperkraft": 2, …}',  // JSON-Text, Neo4j kann keine Maps
  freiePunkte: [5, 4, 3],                  // Zahlenlisten kann es dagegen
  sortOrder: 5
})

(:Campaign)-[:ERLAUBT_RASSE]->(:Rasse)
```

## Was noch fehlt

Der Baukasten deckt **nur Attribute** ab (Marks Vorgabe: *"dabei geht es vor
allem nur um die Attribute"*). Rassen mit Fertigkeitsboni,
Sonderfähigkeiten oder Regelvorteilen gibt es nicht — sie liessen sich mit
der 15er-Regel auch nicht mehr nachrechnen. Käme so etwas dazu, bräuchte es
zuerst eine erweiterte Balance-Formel.
