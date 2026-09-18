---
title: Drohnen und Fahrzeuge
created: 2026-09-18
updated: 2026-09-18
type: konzept
tags: [drohnen, versionsgeschichte, offen]
sources: [../../reference/Neotopia_Drohnen_Fahrzeuge.md, ../../regeln-neotopia.md, ../../../backend/app/begleiter/]
status: teilweise-umgesetzt
---

# Drohnen und Fahrzeuge

## Definition

Beim Kauf wird die **Stufe** festgelegt und frei auf Werte/Fertigkeiten
verteilt:
- Gesundheit = Stufe
- Widerstand = Schadensreduktion
- Angriff = Treffen und Schaden
- Agilität = Geschwindigkeit

**Riggen:** nutzt eigene Werte, aber höchstens bis zur Stufe der Drohne (z. B.
Schusswaffen 4 des Riggers wird bei einer Stufe-3-Drohne zu 3). Der Rigger-Skill
kann alle körperlichen Skills ersetzen, zu denen die Drohne selbstständig fähig
sein sollte — ein körperliches Eintauchen in die Drohne, anders als FPV. Ohne
Sensoren an der Drohne fühlt der Rigger nichts.

Charakterblatt und eigenes `DrohneFahrzeug`-Sheet enthalten je bis zu 4 Slots
für „Drohne/Fahrzeug/Sprite/Geist" — siehe
[[../../reference/Neotopia_Drohnen_Fahrzeuge.md]] für die vollständige Feldliste.

## Preisformel (aus dem Excel, unverändert)

| Typ | Formel |
|---|---|
| Fahrzeug | Stufe×5.000¥ bis Stufe 5, ab 5×20.000¥, ab 10×40.000¥ |
| Drohne | Stufe×500¥ bis Stufe 5, ab 5×1.000¥, ab 10×5.000¥ |

## Offene Frage (von Mark selbst notiert, 30.08.2026)

**Mark will die Preisformel überdenken:** ein Motorrad mit Stufe 3 käme so auf
15.000¥ und wäre kaum leistbar. Vermutlich braucht es eine eigene, günstigere
Staffel für kleine Fahrzeuge — oder die Stufe eines Motorrads ist schlicht
niedriger als gedacht. **Status: offen, nicht behoben.**

## Entwicklung

Backend-Modul `backend/app/begleiter/` (Beziehung `(:Person)-[:BEGLEITET]`,
siehe [[../entities/neo4j-datenmodell]]) bildet das Konzept ab, unverändert zur
Excel-Regel — die einzige Diskussion bislang ist die oben genannte Preisfrage.

## Siehe auch

- [[../../reference/Neotopia_Drohnen_Fahrzeuge.md]] — vollständige Blattstruktur
- [[waehrung-und-preise]] — Einordnung der Preisformel
- [[../entities/neo4j-datenmodell]] — `BEGLEITET`-Beziehung
