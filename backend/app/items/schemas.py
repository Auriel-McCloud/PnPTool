from typing import Literal

from app.entities.schemas import SichtbarkeitModus
from pydantic import BaseModel

# Dieselben drei Arten wie im Treffer-Dialog und auf dem Blatt
# (kampf/ruestung.py::SCHADENSARTEN). Am Tisch: Schlag / Tödlich / Schwerheilbar.
# Leer = noch nicht gesetzt — Bestandsdaten raten wir nicht. "elementar"
# (30.10.2026, Marks Ki-Tama-Attacken-Idee): löst sich NICHT selbst auf — beim
# Eintragen eines Treffers (RuestungsTreffer.tsx) fragt das Tool zusätzlich
# die Effektivität ab (sehr/normal/nicht effektiv gegen das Ziel) und bildet
# erst daraus eine der drei "echten" Schadensarten unten. kampf/ruestung.py
# kennt "elementar" deshalb bewusst NICHT — es rechnet immer nur mit einer der
# drei physischen Arten.
SchadenArt = Literal["", "schlag", "schwer", "aggraviert", "elementar"]

# Leer = noch nicht markiert. Schusswaffen ist Fernkampf (Geschick + Skill).
KampfFertigkeit = Literal["", "Schusswaffen", "Nahkampf", "Handgemenge"]

# Gemeinsamer Typ-Katalog — muss inhaltlich mit frontend/src/items/typKatalog.ts
# übereinstimmen (dort die Kachel-Auswahl beim Anlegen, hier u.a. die Enum für
# die KI-Gegenstandsgenerierung, app/ki/routes.py). Der Typ ist seit
# 22.09.2026 nach dem Anlegen fix (siehe GegenstandUpdate unten).
GEGENSTAND_TYPEN = [
    "Waffe",
    "Rüstung",
    "Cyberware",
    "Bioware",
    "Hexware",
    "Droge",
    "Verbrauchsgegenstand",
    "Werkzeug",
    "Fahrzeug",
    "Drohne",
    "Behälter",
    "Commlink",
    "Cyberdeck",
    "Riggerkonsole",
    "Sonstiges",
]


class GegenstandCreate(BaseModel):
    name: str
    description: str = ""
    notes: str = ""
    typ: str = "Sonstiges"
    preis: int = 0
    # Punkte-Bonus (Waffe: Schaden 1–12, Rüstung: alter flacher Soak 0–7),
    # nur relevant wenn typ Waffe/Rüstung ist, aber generisch gespeichert.
    # Für Rüstung: alter, flacher Soak-Wert (Regelblatt Zeile 66-67/76). Bleibt
    # aus Kompatibilitätsgründen bestehen; Rüstung mit ruestungKaestchenMax > 0
    # nutzt stattdessen das Kästchen-/Durchlass-System (siehe unten und
    # docs/api/ruestung.md), das den flachen Bonus fachlich ablöst.
    kraft: int = 0
    # Cyberwall eines Commlinks: bestimmt die Matrix-Verteidigung (I.C.E.)
    # seines Trägers. Nur bei typ "Commlink" von Belang. 200¥ je Punkt bis 5,
    # darüber 500¥ (siehe docs/regeln-neotopia.md).
    cyberwall: int = 0
    # Freie Zusatzeigenschaften für alles, was kein eigenes Feld hat (Munition,
    # Magazingröße, ...) — bewusst nicht als starres Schema pro Typ, damit neue
    # Gegenstandsarten keine Backend-Änderung brauchen. Die Schadensart einer
    # Waffe ist KEIN Freitext mehr: siehe schadenArt.
    eigenschaften: dict[str, str] = {}
    # MacGuffins/plot-relevante Gegenstände: erscheinen als eigener Knoten im
    # Beziehungsgraph (normale Gegenstände wie ein Hemdknopf nicht) UND sind
    # Grundlage der Lexikon-Entdeckungskette fürs Spieler-Lexikon (09.10.2026,
    # siehe docs/wiki/entities/spieler-lexikon.md). Hieß bis dahin zeigeInGraph.
    storyRelevant: bool = False
    # Einzigartig = genau ein Exemplar in der Welt (z.B. "Das Amulett von
    # Neotopia"), rein thematisch/für die Lore. Unabhängig davon: hatMenge
    # steuert, ob überhaupt eine Stückzahl geführt wird — z.B. ist ein Seil
    # nicht einzigartig, aber trotzdem muss niemand zählen wie viele man hat.
    # Erst wenn hatMenge=true UND nicht einzigartig ergibt "menge" wirklich
    # Sinn (z.B. Munition: jede besitzende Person führt ihre eigene Menge,
    # bewusst noch keine geteilte Vorlage über Personen hinweg — das wäre erst
    # für einen echten Shop-Katalog nötig).
    einzigartig: bool = True
    hatMenge: bool = False
    menge: int = 1
    # Markiert diesen Gegenstand als Vorlage: kann per "Zuweisen" beliebig oft
    # als unabhängige, individualisierbare Kopie an eine Person vergeben werden
    # (z.B. ein Pistolenmodell, das zwei Spieler kaufen und dann unterschiedlich
    # aufrüsten). Die Vorlage selbst bleibt dabei unverändert bestehen.
    # Invariante: istVorlage <=> kein Besitzer. Wird beim Anlegen serverseitig
    # anhand dessen erzwungen, ob ein owner_person_id übergeben wurde — dieser
    # Wert hier wird für die person-gescopte Route ignoriert.
    istVorlage: bool = False
    # Seltenheit 1 (überall verfügbar) bis 5 (nur Speziallabor/Schwarzmarkt).
    # Wird später für automatische Shop-Bestückung genutzt (noch nicht gebaut).
    seltenheit: int = 1
    # Soll dieser Gegenstand automatisch im Angebot von Shops (Orten mit
    # passender Seltenheitsstufe) auftauchen, sobald es Shops gibt? Reines
    # Datenfeld ohne Logik — die automatische Shop-Bestückung selbst ist noch
    # nicht gebaut (Phase 5), siehe CLAUDE.md.
    automatischImShop: bool = False
    # Wo der Gegenstand steckt: AUSGERUESTET (angelegt/getragen), RUCKSACK
    # (mitgeführt) oder GELAGERT (an einem Ort oder in einem Fahrzeug — dann
    # zeigt eine :LIEGT_IN-Beziehung auf das Ziel). Das meiste, was man
    # besitzt, trägt man mit sich, daher RUCKSACK als Ausgangswert.
    ablage: str = "RUCKSACK"
    # Ob etwas anderes hineinpasst. **Nicht** aus dem Typ abgeleitet: ein
    # Motorrad ist ein Fahrzeug ohne Stauraum, eine Kiste hat Stauraum ohne
    # Räder. Ohne Angabe entscheidet das Repository nach dem Typ.
    istBehaelter: bool | None = None
    # Schloss (nur sinnvoll bei Behältern). Genau eine Art: Passwort (die
    # Lösung, das Rätsel steht sichtbar drauf), ein bestimmter Schlüssel-
    # Gegenstand, oder eine Tastenfolge. Leer = kein Schloss.
    schlossArt: str = ""
    schlossPasswort: str = ""
    schlossRaetsel: str = ""
    schluesselId: str = ""
    aufgeschlossen: bool = False
    spielLaenge: int = 0
    # Blatt für Drohne/Fahrzeug/Sprite/Geist (Neotopia.xlsx). Die Stufe wird
    # beim Kauf frei auf diese Werte und die Fertigkeiten verteilt.
    stufe: int = 0
    widerstand: int = 0
    angriff: int = 0
    agilitaet: int = 0
    fahrzeugFertigkeiten: dict[str, int] = {}
    # Cyberdeck: Bonuswürfel je Matrix-Aktion (B/S/D/K, Regelblatt Zeile 157).
    # EW/N (22.09.2026, Erweiterung auf 6 Skills) siehe CLAUDE.md Punkt 9.
    deckBruteForce: int = 0
    deckSchleichen: int = 0
    deckDaten: int = 0
    deckKompilieren: int = 0
    deckElectronicWarfare: int = 0
    deckMatrixNavigation: int = 0
    # Fällt am Körper auf. Ein Sturmgewehr kann man nicht unauffällig tragen,
    # ein Datenchip schon. Reine Anzeige — Folgen entscheidet die Spielleitung.
    immerSichtbar: bool = False
    # Riggerkonsole: Bonus aufs Steuern (kann negativ sein) und wie viele
    # Drohnen gleichzeitig geführt werden können (Zeilen 158-167).
    riggerBonus: int = 0
    maxDrohnen: int = 0
    # Cyber-/Bioware: dauerhafter Willenskraftverlust und wo es sitzt.
    # **Ungerundet** gespeichert (0,67 ist ein gültiger Wert): die Brüche
    # mehrerer Implantate summieren sich, gerundet wird erst am Ende
    # (app/items/chrom.py). Sonst würde jedes Stück für sich aufgerundet und
    # teure Arbeit hätte sich nicht gelohnt.
    wVerlust: float = 0.0
    koerperzone: str = ""
    # Welcher der drei Plätze dieser Zone belegt ist (1-3, Regelblatt: "je
    # drei Plätze mit Bonus und Verlust"). None = kein fester Platz (z.B. bei
    # allem, was keine Cyber-/Bio-/Hexware ist). Wird beim Ausrüsten gegen
    # bereits belegte Plätze derselben Person geprüft (siehe
    # items/repository.py::slot_konflikt).
    slot: int | None = None
    # Unabhängig vom Typ: Cyberware kann z.B. gleichzeitig eine ausfahrbare
    # Klinge und damit eine Waffe sein. Bestimmt nur, ob Kraft/Schaden als
    # Waffe zählt — keine eigene Mechanik, nur eine Kennzeichnung.
    istWaffe: bool = False
    # Häkchen im Umbauen: diese Cyberware ist ein Neurolink. Schaltet Hot frei,
    # sobald sie verbaut ist. Der Name ist egal (Mark, 28.10.2026).
    istNeurolink: bool = False
    # Waffenschaden (1–12), separat vom Chrom-Bonus. Ein Cyberarm mit +2 auf
    # Stärke und eingebauter Klinge (Schaden 3) zählt als Level 5 fürs Chrom,
    # macht aber nur 3 Schaden. Nur relevant wenn istWaffe=True.
    schaden: int = 0
    # Welche der drei Schadensarten die Waffe verursacht. Nur relevant wenn
    # typ "Waffe" oder istWaffe. Standard Tödlich — Schlag und Schwerheilbar
    # setzt man extra (Mark, 10.10.2026).
    schadenArt: SchadenArt = ""
    # Welcher Kampfskill die Waffe würfelt. Leer = noch nicht markiert, die
    # Kampfkarte rät nicht. Auch an Chrom, das zusätzlich als Waffe zählt.
    kampfFertigkeit: KampfFertigkeit = ""
    # Bonuswürfel auf BESTEHENDE Attribute/Fertigkeiten/Sphären, solange
    # ausgerüstet — Schlüssel ist der TraitDef-Name (wie fahrzeugFertigkeiten),
    # nicht die ID, damit es unabhängig vom Ruleset lesbar bleibt. Analog zu
    # den Cyberdeck-Boni (deckBruteForce etc.), aber frei statt fest verdrahtet.
    traitBoni: dict[str, int] = {}
    # Verschiebt die Initiative, solange ausgerüstet (Regelblatt Zeile 57:
    # "CyberwareMod"). Reflex-Booster: +1 / +3 / +6 je nach Stufe (Zeilen
    # 421-444), "Dash" +2 (Zeile 174). Freies Feld statt Sonderregel, damit
    # auch Drogen und Artefakte die Reihenfolge verschieben können.
    initiativeBonus: int = 0
    # Cyber-/Bio-/Hexware: sitzt das Stück im Körper? Chrom ist keine
    # Ausrüstung, die man an- und ablegt — es wird eingesetzt und nur per
    # Operation wieder entfernt. Wirkt nur, wenn verbaut.
    verbaut: bool = False
    # Wie oft der Reflex-Booster pro Kampf eine Zusatzaktion erlaubt:
    # 1 (Stufe 1), 2 (Stufe 2), -1 = jede Runde (Stufe 3), 0 = gar nicht.
    zusatzaktionen: int = 0
    # NEUE Fertigkeiten, die es OHNE diesen Gegenstand gar nicht gibt (z.B.
    # ein NeuroWeaving-Skill an einem Cyberdeck, oder "Springen" an
    # magischen Stiefeln) — Name -> Bonuswürfel. Erscheinen nur, solange
    # ausgerüstet, als eigener Abschnitt auf dem Charakterbogen.
    ausruestungsfertigkeiten: dict[str, int] = {}
    # Ki-Tama (29.10.2026, Marks FF7-Idee, 30.10.2026 umbenannt von "Materia"
    # zu "Ki-Tama" — jap. "Tama" = Perle/Kugel + "Ki" = KI-Kristall):
    # welche der obigen ausruestungsfertigkeiten der Spieler mit eigener
    # Erfahrung hochleveln darf (bis Stufe 6, dieselbe Kostenkurve wie eine
    # normale Fertigkeit, siehe traits/erfahrung.py::kitama_schluessel).
    # Name -> true. Bewusst ein EIGENES Flag statt alle
    # ausruestungsfertigkeiten automatisch steigerbar zu machen — Mark:
    # "eigenes Häkchen pro Fertigkeit", nicht jeder flache Item-Bonus soll
    # EP-Investitionen anziehen. Die Stufe selbst steht weiterhin nur in
    # ausruestungsfertigkeiten; dieses Feld markiert nur, WELCHE Einträge
    # dort steigerbar sind. Der Clou: die Stufe hängt am GEGENSTAND, nicht
    # an der Person — wandert ein Gegenstand per Besitzerwechsel (z.B. Loot
    # vom Endboss) weiter, kommt die hochgelevelte Stufe automatisch mit,
    # ganz ohne eigene Logik dafür.
    kiTamaFertigkeiten: dict[str, bool] = {}
    # Attacken-Fertigkeiten (30.10.2026, Marks Idee direkt im Anschluss ans
    # Ki-Tama-Feature): markiert, welche der obigen ausruestungsfertigkeiten
    # ZUSÄTZLICH ein Kampfangriff sind — unabhängig von kiTamaFertigkeiten
    # oben (eine Fertigkeit kann Attacke, Ki-Tama, beides oder keins von
    # beidem sein). Erscheint dann in der Kampfkarte wie eine Waffe. Name ->
    # true, genau dasselbe Schlüssel-Muster wie kiTamaFertigkeiten.
    attackenFertigkeiten: dict[str, bool] = {}
    # Schadensart je Attacken-Fertigkeit (nur relevant, wenn der Name auch in
    # attackenFertigkeiten steht). KEIN eigener Schadenswert: Mark, 30.10.2026
    # — "der Schaden sind die Erfolge die übrig bleiben", also exakt wie bei
    # Waffen die Nettoerfolge des Wurfs, nie ein fixer Bonus. Default beim
    # Setzen des Häkchens ist "schwer" (Tödlich), dieselbe Konvention wie
    # SCHADEN_ART_DEFAULT bei Waffen.
    attackenSchadensart: dict[str, SchadenArt] = {}
    # Beschwörungs-Ki-Tama (30.10.2026): Link auf den fest gebundenen
    # Critter-Person-Knoten (persistentes Pet) — siehe GegenstandResponse
    # unten für die volle Begründung. Leer = kein Beschwörungs-Ki-Tama.
    beschworenerCritterId: str = ""
    # SL-Schwierigkeitsgrad (0-2), additiv auf die benötigten Erfolge der
    # Beschwörungs-Probe.
    beschwoerungsSchwierigkeit: int = 0
    # Eigengewicht in kg. 0 = vernachlässigbar (Ausweis, Datenchip).
    gewicht: float = 0.0
    # Wie viel dieser Gegenstand aufnehmen kann, in kg. 0 = kein Behälter.
    # Bei Personen ergibt sich die Traglast stattdessen aus einem Attribut,
    # siehe campaigns/repository.py (EINSTELLUNGEN_DEFAULTS).
    kapazitaet: float = 0.0
    # Ideenschmiede: Entwürfe sind noch nicht Teil der aktiven Kampagne
    istEntwurf: bool = False
    # Wird beim Anlegen automatisch gesetzt (PC-Besitzer -> nur für ihn sichtbar,
    # NPC-Besitzer -> SL-geheim), falls hier nicht explizit übersteuert.
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    # Rüstung: Kästchen + Schadensreduktion statt eines flachen Bonus (siehe
    # kampf/ruestung.py für die vollständige Herleitung, docs/api/ruestung.md
    # für die ausführliche Begründung). 0 = dieses Stück nutzt das System
    # nicht (z.B. Bestandsdaten oder alle Nicht-Rüstungsgegenstände).
    #
    # Max ist der Ausgangswert des Gegenstands ("wie robust ist die Rüstung
    # gebaut"). Aktuell defaultet beim Anlegen auf Max (frisches Stück ist
    # unbeschädigt) — None statt einer festen Zahl, damit "nicht angegeben"
    # von "ausdrücklich beschädigt angelegt" unterscheidbar bleibt.
    ruestungKaestchenMax: int = 0
    ruestungKaestchenAktuell: int | None = None
    # Wie viel Schaden die Rüstung pro Treffer direkt abfängt — höher ist
    # besser (klassischer Soak-Wert). Kein eigener "Aktuell"-Wert mehr nötig:
    # die tatsächlich wirksame Reduktion ergibt sich aus dem
    # Kästchen-Verhältnis (siehe kampf/ruestung.py::reduktion_effektiv) und
    # sinkt automatisch, je beschädigter die Rüstung ist.
    ruestungReduktionBasis: int = 0
    # Reparaturmaterial (23.09.2026, Rüstungs-Reparatur): dieser Gegenstand
    # kann bei der Selbst-Reparatur einer Rüstung eingesetzt werden. Gestuft
    # wie Chrom-Qualitätsstufen (items/chrom.py) — kleines improvisiertes Kit
    # deckt wenig, hochwertiges Ersatzteil-Paket mehr. Kapazität ist der
    # harte Deckel pro Versuch: selbst ein guter Wurf repariert nie mehr, als
    # das eingesetzte Material an Kästchen abdeckt (kampf/ruestung.py::
    # selbstreparatur_ergebnis). Verbraucht wird IMMER genau 1 Stück pro
    # Versuch (auch bei 0 reparierten Kästchen — realistisches Risiko).
    istReparaturmaterial: bool = False
    reparaturKapazitaet: int = 0
    # Natürliche Rüstung (11.10.2026 Verfeinerung, Rassen-/Kreatur-Feature —
    # z.B. Dug'Rahs Chitinpanzer, später Drachenschuppen): generisches Flag,
    # analog zu `verbaut` bei Cyberware (siehe items/chirurgie.py). Wirkung:
    # (1) für den Spieler nicht ablegbar, nur die SL kann es im Ausnahmefall
    # (siehe chirurgie.py::kann_ablegen); (2) Reparatur-Routen lehnen mit 409
    # ab — heilt stattdessen nur über die Rast-Mechanik (app/traits/rast.py);
    # (3) `ruestungKaestchenMax` dieses Stücks wird überall, wo der
    # Rüstungspool berechnet wird, durch die LIVE Widerstandsfähigkeit-Rating
    # der tragenden Person ersetzt (siehe kampf/ruestung.py::
    # anwende_natuerliche_ruestung) — der hier gespeicherte Wert ist dann nur
    # noch ein Vorlagen-Hinweis, keine Wahrheit mehr. `ruestungReduktionBasis`
    # bleibt dagegen ein normaler, pro Item-Template frei konfigurierbarer
    # Wert (Dug'Rah: 2 — für künftige Kreaturen einfach ein zweites Template).
    istNatuerlich: bool = False
    # Maschinenteil (26.10.2026, Drohnen-/Fahrzeug-Umbau mit Material statt
    # Nuyen, docs/wiki/concepts/drohnen-fahrzeuge.md): gestuft wie
    # Reparaturmaterial/Chrom-Qualitätsstufen. Minderwertig taugt nur für die
    # Rüstungs-/Drohnen-Reparatur (kampf/ruestung.py), normal deckt
    # Fertigkeiten/Zusatzfertigkeiten, hochwertig zusätzlich Attribute — siehe
    # traits/drohnen.py::maschinenteil_reicht. Leer = kein Maschinenteil.
    istMaschinenteil: bool = False
    maschinenteilQualitaet: Literal["", "minderwertig", "normal", "hochwertig"] = ""
    # Waffen-/Rüstungs-/Drohnen-Augments (29.10.2026, siehe
    # docs/wiki/concepts/augments-ausruestung.md): wie viele Augments in
    # dieses Stück montierbar sind. Nur bei Typ Waffe/Rüstung gesetzt
    # (Drohnen/Fahrzeuge tragen dasselbe Feld an `Person`, siehe
    # entities/schemas.py) — Mark: "ich würde das gerne variabel halten",
    # kein fixer Wert für alle Waffen.
    upgradeSlots: int = 0
    # Dieser Gegenstand IST ein Augment (montierbar an Waffe/Rüstung/Drohne).
    # Sein `traitBoni`-Feld (oben über GegenstandCreate wiederverwendet)
    # trägt den Bonus, den es beim Montieren gibt — Mark: "genau wie
    # traitBoni heute", kein eigenes zweites Bonus-Feld nötig.
    istAugment: bool = False
    # Leer = passt auf jedes Ziel (Waffe jeden Typs, Rüstung, Drohne/
    # Fahrzeug). Gesetzt = nur an Waffen MIT genau diesem kampfFertigkeit-Typ
    # montierbar (items/augments.py::waffentyp_passt).
    augmentWaffentyp: KampfFertigkeit = ""
    # Ein Patzer beim Montieren/Demontieren beschädigt das Augment, statt die
    # Aktion nur scheitern zu lassen (Mark, 29.10.2026) — reparierbar über
    # dieselbe Werkbank-Material-Mechanik wie Rüstung/Drohne, nur mit dem
    # Augment-Level (items/augments.py::augment_level) als Zielgröße statt
    # "fehlenden Kästchen". Solange defekt, zählt der Bonus nicht.
    defekt: bool = False
    # Zieltyp-Einschränkung (29.10.2026 Nachbesserung, Mark: "ein zusätzliches
    # Feld dafür, wenn es leer ist gilt es für alle, bei Auswahl z.B. nur für
    # Decks"): leer = an jedem AUGMENT_TRAEGER_TYPEN montierbar (Normalfall,
    # wie bisher). Gesetzt = NUR an genau diesem Gegenstandstyp — z.B. ein
    # Reflexbooster-Upgrade, das nur an Cyberdeck/Riggerkonsole sinnvoll ist.
    # Unabhängig von `augmentWaffentyp` oben, das NUR innerhalb von Waffen
    # weiter nach Kampffertigkeit filtert (items/augments.py::zieltyp_passt).
    augmentZielTyp: Literal["", "Waffe", "Rüstung", "Cyberdeck", "Riggerkonsole"] = ""
    # Boni, die dieses Augment beim Ziel bewirkt, sobald es montiert und
    # nicht defekt ist (29.10.2026 Nachbesserung, Mark: Waffenschaden,
    # Rüstungs-Absorption/Kästchen, Initiative/Zusatzaktionen änderbar
    # machen). Additiv zum Basiswert des Ziels — reine Wiederverwendung
    # bestehender Felder (`schaden`, `ruestungReduktionBasis`,
    # `ruestungKaestchenMax`, `initiativeBonus`, `zusatzaktionen` oben),
    # kein zweites Bonus-Schema. `schadenArt` ist hier die Ausnahme: kein
    # Bonus, sondern ein Override (siehe `items/augments.py::
    # wende_augment_boni_an`) — deshalb darf pro Ziel höchstens EIN
    # montiertes Augment eine Schadensart setzen (409 beim Montieren, Mark:
    # "Montieren wird abgelehnt, wenn am Ziel schon ein Schadensart-Augment
    # sitzt").


class GegenstandUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None
    # typ war bis 06.10.2026 bewusst NICHT hier (Marks Entscheidung vom
    # 22.09.2026: "wer's falsch gewählt hat, löscht und legt neu an") —
    # jetzt doch erlaubt, aber NUR für die Spielleitung (dieselbe
    # require_campaign_gm-Absicherung wie der ganze PATCH-Endpunkt): die
    # KI-Gegenstandserstellung (app/ki/routes.py) ordnet gelegentlich den
    # falschen Typ zu, und "löschen und neu anlegen" ist dort kein
    # brauchbarer Korrekturweg mehr. Ursprüngliche Sorge bleibt real und
    # ungelöst: typ-spezifische Werte des ALTEN Typs (Schaden,
    # Rüstungskästchen, Deck-Werte, ...) räumt ein Typwechsel nicht auf,
    # sie bleiben unsichtbar in der DB stehen, bis jemand sie von Hand
    # löscht oder der Gegenstand gelöscht wird. Für den eigentlichen
    # Anwendungsfall (frisch von der KI angelegt, bevor jemand die
    # Umbauen-Werte überhaupt angefasst hat) ist das meist kein Problem.
    typ: str | None = None
    preis: int | None = None
    kraft: int | None = None
    cyberwall: int | None = None
    eigenschaften: dict[str, str] | None = None
    storyRelevant: bool | None = None
    einzigartig: bool | None = None
    hatMenge: bool | None = None
    menge: int | None = None
    # istVorlage bewusst NICHT hier: ob ein Gegenstand eine Vorlage ist, ergibt
    # sich ausschließlich daraus, ob er einen Besitzer hat (siehe Besitzer
    # wechseln/Vorlage machen/Zuweisen-Endpoints) — kein direktes Umschalten
    # per PATCH, sonst könnten owned+istVorlage-Widersprüche entstehen.
    seltenheit: int | None = None
    automatischImShop: bool | None = None
    gewicht: float | None = None
    kapazitaet: float | None = None
    istEntwurf: bool | None = None  # Verschieben zwischen Ideenschmiede und Kampagne
    istBehaelter: bool | None = None
    schlossArt: str | None = None
    schlossPasswort: str | None = None
    schlossRaetsel: str | None = None
    schluesselId: str | None = None
    aufgeschlossen: bool | None = None
    spielLaenge: int | None = None
    stufe: int | None = None
    widerstand: int | None = None
    angriff: int | None = None
    agilitaet: int | None = None
    fahrzeugFertigkeiten: dict[str, int] | None = None
    deckBruteForce: int | None = None
    deckSchleichen: int | None = None
    deckDaten: int | None = None
    deckKompilieren: int | None = None
    deckElectronicWarfare: int | None = None
    deckMatrixNavigation: int | None = None
    immerSichtbar: bool | None = None
    riggerBonus: int | None = None
    maxDrohnen: int | None = None
    wVerlust: float | None = None
    koerperzone: str | None = None
    slot: int | None = None
    istWaffe: bool | None = None
    istNeurolink: bool | None = None
    schaden: int | None = None
    schadenArt: SchadenArt | None = None
    kampfFertigkeit: KampfFertigkeit | None = None
    traitBoni: dict[str, int] | None = None
    initiativeBonus: int | None = None
    verbaut: bool | None = None
    zusatzaktionen: int | None = None
    ausruestungsfertigkeiten: dict[str, int] | None = None
    kiTamaFertigkeiten: dict[str, bool] | None = None
    attackenFertigkeiten: dict[str, bool] | None = None
    attackenSchadensart: dict[str, SchadenArt] | None = None
    beschworenerCritterId: str | None = None
    beschwoerungsSchwierigkeit: int | None = None
    bildUrl: str | None = None
    sichtbarkeit: SichtbarkeitModus | None = None
    sichtbarFuer: list[str] | None = None
    ruestungKaestchenMax: int | None = None
    ruestungKaestchenAktuell: int | None = None
    ruestungReduktionBasis: int | None = None
    istReparaturmaterial: bool | None = None
    reparaturKapazitaet: int | None = None
    istNatuerlich: bool | None = None
    istMaschinenteil: bool | None = None
    maschinenteilQualitaet: Literal["", "minderwertig", "normal", "hochwertig"] | None = None
    upgradeSlots: int | None = None
    istAugment: bool | None = None
    augmentWaffentyp: Literal["", "Schusswaffen", "Nahkampf", "Handgemenge"] | None = None
    augmentZielTyp: Literal["", "Waffe", "Rüstung", "Cyberdeck", "Riggerkonsole"] | None = None
    defekt: bool | None = None
    # weggeworfen bewusst NICHT hier — wie istVorlage. Ob etwas im Mülleimer
    # liegt, ergibt sich ausschliesslich aus den Routen wegwerfen/zurueckholen,
    # die zusätzlich die Ablage aufräumen. Ein PATCH könnte das Flag setzen,
    # ohne die :LIEGT_IN-Verknüpfung zu lösen — dann zählte das Gewicht weiter.


class ZuweisenRequest(BaseModel):
    zielPersonId: str
    # True: immer eine Kopie anlegen, auch wenn die Vorlage einzigartig oder
    # story-relevant ist. Die Vorlage selbst bleibt besitzerlos. False (Default)
    # behält das alte Verhalten: einzigartig/storyRelevant übergibt das Stück.
    kopie: bool = False


class HineinlegenRequest(BaseModel):
    """Vom Behälter aus bedient (31.10.2026, Mark: Workflow umgekehrt —
    nicht mehr am Gegenstand das Ziel suchen, sondern am Behälter den
    Gegenstand). `gegenstandId` ist, was hineingelegt werden soll."""

    gegenstandId: str


class ZusammenlegenRequest(BaseModel):
    """Mehrere gleichwertige Gegenstände zu einem Stapel zusammenlegen.

    `item_id` aus der URL ist das Ziel (bekommt die Summe der Mengen,
    hatMenge=true); die hier genannten Quellen werden wie beim normalen
    Wegwerfen in den Mülleimer der Spielleitung gelegt, nicht gelöscht —
    siehe `items/repository.py::zusammenlegen` für die Gleichheitsprüfung.
    """

    quellItemIds: list[str]


class GegenstandResponse(BaseModel):
    id: str
    name: str
    description: str
    notes: str
    typ: str
    preis: int
    kraft: int
    cyberwall: int
    eigenschaften: dict[str, str]
    storyRelevant: bool
    einzigartig: bool
    hatMenge: bool
    menge: int
    istVorlage: bool
    seltenheit: int
    automatischImShop: bool
    bildUrl: str
    sichtbarkeit: str
    sichtbarFuer: list[str]
    ablage: str
    gewicht: float
    kapazitaet: float
    istEntwurf: bool = False  # Ideenschmiede
    istBehaelter: bool = False
    # Leer = kein Schloss. Lösung und Schlüssel-Kennung sehen Spieler nie
    # (visibility.py streicht sie); das Rätsel schon.
    schlossArt: str = ""
    schlossPasswort: str = ""
    schlossRaetsel: str = ""
    schluesselId: str = ""
    aufgeschlossen: bool = False
    spielLaenge: int = 0
    stufe: int = 0
    widerstand: int = 0
    angriff: int = 0
    agilitaet: int = 0
    fahrzeugFertigkeiten: dict[str, int] = {}
    deckBruteForce: int = 0
    deckSchleichen: int = 0
    deckDaten: int = 0
    deckKompilieren: int = 0
    deckElectronicWarfare: int = 0
    deckMatrixNavigation: int = 0
    # Fällt am Körper auf. Ein Sturmgewehr kann man nicht unauffällig tragen,
    # ein Datenchip schon. Reine Anzeige — Folgen entscheidet die Spielleitung.
    immerSichtbar: bool = False
    # Riggerkonsole: Bonus aufs Steuern (kann negativ sein) und wie viele
    # Drohnen gleichzeitig geführt werden können (Zeilen 158-167).
    riggerBonus: int = 0
    maxDrohnen: int = 0
    # Cyber-/Bioware: dauerhafter Willenskraftverlust und wo es sitzt.
    # **Ungerundet** gespeichert (0,67 ist ein gültiger Wert): die Brüche
    # mehrerer Implantate summieren sich, gerundet wird erst am Ende
    # (app/items/chrom.py). Sonst würde jedes Stück für sich aufgerundet und
    # teure Arbeit hätte sich nicht gelohnt.
    wVerlust: float = 0.0
    koerperzone: str = ""
    slot: int | None = None
    istWaffe: bool = False
    istNeurolink: bool = False
    schaden: int = 0
    schadenArt: SchadenArt = ""
    kampfFertigkeit: KampfFertigkeit = ""
    traitBoni: dict[str, int] = {}
    initiativeBonus: int = 0
    verbaut: bool = False
    entfernungBeantragt: bool = False
    zusatzaktionen: int = 0
    ausruestungsfertigkeiten: dict[str, int] = {}
    kiTamaFertigkeiten: dict[str, bool] = {}
    # Siehe GegenstandCreate für die volle Begründung.
    attackenFertigkeiten: dict[str, bool] = {}
    attackenSchadensart: dict[str, SchadenArt] = {}
    # Beschwörungs-Ki-Tama (30.10.2026, Marks Idee direkt im Anschluss ans
    # Ki-Tama-Feature, siehe docs/wiki/concepts/augments-ausruestung.md):
    # Link auf den fest ans Ki-Tama gebundenen Critter-Person-Knoten
    # (persistentes Pet, heilt beim Rasten mit). Leer = kein Beschwörungs-
    # Ki-Tama, ganz normales Ki-Tama/Upgrade-Material. Der Beschwörungswert
    # selbst ist KEIN eigenes Feld — er ist einfach die höchste als Ki-Tama
    # markierte ausruestungsfertigkeiten-Stufe auf diesem Gegenstand
    # (items/beschwoerung.py::beschwoerungsstufe), wandert also beim
    # EP-Hochleveln automatisch mit.
    beschworenerCritterId: str = ""
    # SL-Schwierigkeitsgrad beim ANLEGEN (nicht pro Wurf), additiv auf die
    # benötigten Erfolge der Beschwörungs-Probe (Beschwörungswert ÷ 2
    # aufgerundet) — Mark: "damit besonders starke Beschwörungen nicht
    # automatisch so leicht sind wie schwache". 0-2 vorgesehen, kein hartes
    # Enum-Cap (wer mehr einträgt, hat's sich selbst zuzuschreiben).
    beschwoerungsSchwierigkeit: int = 0
    # ein einzigartiges Stück wäre sonst fort. Überall ausgeblendet ausser in
    # der Mülleimer-Liste; zählt weder Gewicht noch Boni.
    weggeworfen: bool = False
    # Name dessen, der es weggeworfen hat — damit im Mülleimer steht, woher es
    # kommt. Leer, wenn es nie weggeworfen wurde.
    weggeworfenVon: str = ""
    # Nur bei GELAGERT gesetzt: worin bzw. wo der Gegenstand liegt.
    ablageZielId: str | None = None
    ablageZielName: str | None = None
    ablageZielKind: str | None = None
    # Rüstung: Kästchen + Schadensreduktion. 0/0 = dieses Stück nutzt das
    # System nicht (siehe GegenstandCreate für die Bedeutung der Felder).
    ruestungKaestchenMax: int = 0
    ruestungKaestchenAktuell: int = 0
    ruestungReduktionBasis: int = 0
    istReparaturmaterial: bool = False
    reparaturKapazitaet: int = 0
    istNatuerlich: bool = False
    istMaschinenteil: bool = False
    maschinenteilQualitaet: str = ""
    upgradeSlots: int = 0
    istAugment: bool = False
    augmentWaffentyp: str = ""
    augmentZielTyp: str = ""
    defekt: bool = False
    # Montage-Ziel (nur bei istAugment relevant) — Pendant zu ablageZiel*,
    # kann ein Gegenstand (Waffe/Rüstung/Cyberdeck/Riggerkonsole) ODER eine
    # Person (Drohne/Fahrzeug) sein, siehe items/repository.py::MONTIERT_AN.
    montiertAnId: str | None = None
    montiertAnName: str | None = None
    montiertAnKind: str | None = None


class GegenstandMitBesitzer(GegenstandResponse):
    # Vorlagen haben keinen Besitzer (siehe istVorlage-Kommentar in
    # GegenstandUpdate) — daher optional statt Pflichtfeld.
    ownerId: str | None = None
    ownerName: str | None = None
    ownerPersonType: str | None = None


class AblageRequest(BaseModel):
    """Umlegen eines Gegenstands.

    `zielId` ist nur bei ablage="GELAGERT" von Belang und wird sonst
    ignoriert; ohne Ziel gilt der Gegenstand als unbestimmt gelagert.
    """

    ablage: str
    zielId: str | None = None


class AblageZiel(BaseModel):
    id: str
    name: str
    # "Ort" oder "Gegenstand" — bestimmt nur die Darstellung
    kind: str
    # Nur gesetzt, wenn die SL campaignweit auswählt (siehe routes.py::ablageziele)
    # und der Behälter jemand anderem gehört — zur Unterscheidung gleichnamiger
    # Rucksäcke. Bei den eigenen Zielen eines Spielers immer leer.
    besitzerName: str | None = None
