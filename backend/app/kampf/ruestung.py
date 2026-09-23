"""Rüstungssystem: Kästchen + Schadensreduktion.

Herleitung (Gespräch Mark/Claude, 10.09.2026 für die erste Fassung mit
"Durchlass", 18.09.2026 für den Umbau auf "Reduktion" — die ausführliche
Begründung mit allen Zwischenschritten steht in docs/api/ruestung.md, hier
nur die knappe Fassung als Code-Kommentar).

**Warum nicht einfach ein Rüstungswert, der vom Schaden abgezogen wird** (wie
der alte `kraft`-Bonus, siehe items/schemas.py)? Weil das nur zwei Zustände
kennt — "hält" oder "hält nicht mehr" — und Rüstung im Spiel nie kaputtgeht.
Mark wollte, dass Rüstung sich abnutzt und mit jedem Treffer schlechter wird,
bis sie irgendwann nichts mehr bringt.

**Die Kernidee: zwei Werte statt einem.**

* **Kästchen** (`ruestungKaestchenMax` / `ruestungKaestchenAktuell`) — wie viel
  Substanz die Rüstung hat, um Treffer zu schlucken, bevor sie reißt. Sinkt
  mit Beschädigung, wie die Gesundheit einer Person.
* **Reduktion** (`ruestungReduktionBasis`) — wie viel Schaden die Rüstung pro
  Treffer direkt abfängt. **Hoch ist gut** (klassischer Soak-Wert, anders als
  die frühere "Durchlass"-Fassung, wo niedriger besser war — Mark fand das
  nach dem Ausprobieren am Tisch unintuitiv: *"Durchlass ist ein dummer
  Wert"*). `absorbiert = min(Stärke, Reduktion)`, der Rest kommt durch.

  Anders als beim alten Durchlass gibt es **keinen separaten "Aktuell"-Wert**
  für die Reduktion mehr — das war die Quelle eines echten Bugs (siehe
  `items/repository.py::update_gegenstand`, Fix vom 18.09.2026: der Aktuell-
  Wert zog beim nachträglichen Aktivieren nicht automatisch mit, wodurch
  frische Rüstung fälschlich als zerstört galt). Stattdessen wird die
  **effektive Reduktion aus dem Kästchen-Verhältnis abgeleitet** — weniger
  gespeicherter Zustand, eine Fehlerquelle weniger:

  - über 50 % der Kästchen übrig: volle Reduktion
  - über 25 %: halbe Reduktion (abgerundet)
  - darüber (aber > 0): ein Viertel (abgerundet)
  - 0 Kästchen: keine Reduktion, Rüstung wirkt nicht mehr

  Mark: *"könnte sich die Reduktion aufgrunden halbieren wenn die Kästchen
  halbiert werden? und dann beim 4tel? somit bleibt eine Lederjacke mit 1
  Absorption immer gleich, aber ein Bombenschutzanzug der stark beschädigt
  wird wird schwächer"* — eine Rüstung mit wenig Reduktion merkt die Stufen
  kaum (0 bleibt 0, 1 wird höchstens 0), eine mit viel Reduktion verliert
  spürbar an Wirkung, je kaputter sie ist.

**Pro Treffer:**

1. `reduktion = reduktion_effektiv(Basis, Kästchen-Aktuell, Kästchen-Max)`.
2. `absorbiert = min(Stärke, reduktion)` — was die Rüstung abfängt.
3. `durchkommend = max(0, Stärke - reduktion)` — der Rest.
4. **Schaden an die Trägerin**, abgestuft statt einfach geblockt — Rüstung
   "hält nicht auf", sie "dämpft": Unheilbar wird zu Tödlich, Tödlich wird zu
   Schlag (Menge bleibt gleich), Schlag ist schon die unterste Stufe und wird
   stattdessen **halbiert** (abgerundet). Menge ist immer `durchkommend`.
5. **Schaden an die Rüstung (Kästchen):**
   - **Unheilbar:** Mark: *"das wäre ja was wie eine Explosion, da kann man
     froh sein das überstanden zu haben"* — immer die volle Stärke, 1:1,
     unabhängig von der Reduktion.
   - **Tödlich:** eine Mischung, weil die Rüstung hier tatsächlich etwas
     leistet: der absorbierte Anteil beschädigt sie nur zur Hälfte (sie hat
     ihn ja immerhin abgefangen, ohne wirklich zu kämpfen), der
     durchkommende Anteil voll 1:1.
   - **Schlag:** nur wenn der Treffer mindestens die Hälfte der *aktuellen*
     Kästchen erreicht (`2×Stärke ≥ Kästchen-Aktuell`) — sonst prallt ein
     laues Klopfen wirkungslos ab. Trifft die Bedingung zu, beschädigt der
     durchkommende Anteil die Rüstung zur Hälfte.
     **Bewusst `Kästchen-Aktuell` statt `Kästchen-Max`**: dadurch wird die
     Trigger-Schwelle mit jedem Treffer niedriger — eine bereits ramponierte
     Rüstung bricht leichter weiter zusammen.
6. **Ist eine Rüstung bereits bei 0 Kästchen**, wirkt sie gar nicht mehr — der
   Treffer geht unverändert und in voller Höhe durch, ohne jede Abstufung.

**Reparatur** (Hardware-Skill-Probe oder Händler, kostet Geld/Zeit — dieser
Teil des Ablaufs existiert im Tool noch nicht, siehe docs/api/ruestung.md)
füllt nur noch die Kästchen auf — die Reduktion braucht keine eigene
Reparatur mehr, sie folgt automatisch aus dem wiederhergestellten
Kästchen-Verhältnis.

Rechnet **rein** (keine Datenbankzugriffe), damit die Formel unabhängig
testbar ist und an einer einzigen Stelle steht — dieselbe Motivation wie bei
`traits/bogen.py` und `items/chrom.py`.
"""

# Die drei Schadensarten aus dem WoD-Dreiklang, wie er im ganzen Projekt schon
# verwendet wird (Kaestchen.tsx::SCHADENSARTEN, Person.schaden{Schlag,Schwer,
# Aggraviert}). Mark benutzt am Tisch eher "Schlag/Tödlich/Unheilbar" — das
# entspricht 1:1 schlag/schwer/aggraviert, siehe Mapping unten.
SCHADENSARTEN = ("schlag", "schwer", "aggraviert")

# Eine Stufe leichter, wenn ein Treffer die Rüstung durchdringt. "schlag" hat
# keine leichtere Stufe mehr — siehe HALBIERT_STATT_ABGESTUFT.
EINE_STUFE_LEICHTER = {"aggraviert": "schwer", "schwer": "schlag"}


def _abgestufter_schaden(art: str, menge: int) -> tuple[str, int]:
    """Wie ein Treffer bei der Trägerin ankommt: eine Stufe leichter, oder
    (für "schlag", die leichteste Stufe) halbiert statt abgestuft."""
    leichter = EINE_STUFE_LEICHTER.get(art)
    if leichter is None:
        return "schlag", menge // 2
    return leichter, menge


def reduktion_effektiv(reduktion_basis: int, kaestchen_aktuell: int, kaestchen_max: int) -> int:
    """Wie viel Reduktion eine Rüstung im aktuellen Zustand tatsächlich gibt.

    Gestuft statt linear (Marks Vorgabe): über 50 % der Kästchen volle
    Wirkung, über 25 % die Hälfte, darüber (aber noch etwas übrig) ein
    Viertel, bei 0 Kästchen nichts mehr. Eine Rüstung mit wenig Reduktion
    (z.B. 1) merkt die Stufen kaum, eine mit viel Reduktion (z.B. 8) verliert
    spürbar an Wirkung, je kaputter sie ist — genau der gewünschte Effekt.
    """
    if kaestchen_max <= 0 or kaestchen_aktuell <= 0:
        return 0
    anteil = kaestchen_aktuell / kaestchen_max
    if anteil > 0.5:
        return reduktion_basis
    if anteil > 0.25:
        return reduktion_basis // 2
    return reduktion_basis // 4


def berechne_treffer(
    art: str,
    staerke: int,
    kaestchen_aktuell: int,
    kaestchen_max: int,
    reduktion_basis: int,
) -> dict:
    """Ein einzelner Treffer gegen EIN Rüstungsteil.

    `art` ist "schlag", "schwer" (= Tödlich) oder "aggraviert" (= Unheilbar).
    `staerke` ist die Anzahl Schadenspunkte des Treffers (was der Spieler als
    "3× Tödlich" einträgt).

    Wird mit den Werten **einer** Rüstung aufgerufen — bei mehreren
    getragenen Teilen sind das die des Pools (`pool` unten), nicht die eines
    einzelnen Stücks. Dann gelten von der Rückgabe nur `hpArt`, `hpMenge`
    und `kaestchenSchaden`; wie sich der Kästchenschaden auf die einzelnen
    Teile verteilt, rechnet `verteile_kaestchenschaden`.

    Gibt zurück:
    - `hpArt`, `hpMenge`: was bei der Trägerin an Schaden ankommt.
    - `kaestchenSchaden`: wie viele Kästchen dieser Treffer gekostet hat.
    - `kaestchenNeu`: der neue Kästchen-Wert für den Gegenstand.
    """
    if art not in SCHADENSARTEN:
        raise ValueError(f"Unbekannte Schadensart: {art}")
    staerke = max(0, staerke)

    if kaestchen_aktuell <= 0:
        # Zerstörte Rüstung wirkt nicht mehr — sie kann auch nichts mehr
        # abstufen. Der Treffer geht unveraendert durch (Mark: "wirkt gar
        # nicht mehr").
        return {
            "hpArt": art,
            "hpMenge": staerke,
            "kaestchenSchaden": 0,
            "kaestchenNeu": 0,
        }

    reduktion = reduktion_effektiv(reduktion_basis, kaestchen_aktuell, kaestchen_max)
    absorbiert = min(staerke, reduktion)
    durchkommend = staerke - absorbiert
    hp_art, hp_menge = _abgestufter_schaden(art, durchkommend)

    if art == "aggraviert":
        # Volle Wucht, immer — siehe Modulkommentar oben.
        kaestchen_schaden = staerke
    elif art == "schwer":
        # Der absorbierte Anteil nur zur Hälfte (die Rüstung hat ihn
        # abgefangen, ohne wirklich zu kämpfen), der durchkommende Rest voll.
        kaestchen_schaden = (absorbiert // 2) + durchkommend
    else:  # "schlag"
        # Nur ab der Hälfte der AKTUELLEN Kästchen — ein laues Klopfen
        # richtet nichts aus, egal wie kaputt die Rüstung schon ist.
        loest_aus = 2 * staerke >= kaestchen_aktuell
        kaestchen_schaden = durchkommend // 2 if loest_aus else 0

    kaestchen_schaden = min(kaestchen_schaden, kaestchen_aktuell)
    kaestchen_neu = kaestchen_aktuell - kaestchen_schaden

    return {
        "hpArt": hp_art,
        "hpMenge": hp_menge,
        "kaestchenSchaden": kaestchen_schaden,
        "kaestchenNeu": kaestchen_neu,
    }


def reihenfolge(teile: list[dict]) -> list[dict]:
    """In welcher Reihenfolge die getragenen Rüstungsteile aufgebraucht werden.

    **Die beste Reduktion zuerst** — absteigend nach `ruestungReduktionBasis`.
    Marks Vorgabe (aus der Durchlass-Fassung übernommen, nur umgekehrt
    sortiert weil "hoch=gut" jetzt gilt): die beste Schicht hält den Treffer
    auf und wird dabei verbraucht; ist sie hin, übernimmt die nächstbeste.

    Das ist zugleich die Regel, die einen sonst offenen Missbrauch schließt:
    ein winziges Teil mit sehr hoher Reduktion würde dem Pool sonst
    dauerhaft seine Stärke leihen, während eine schwache Jacke die Masse der
    Kästchen stellt. Weil aber genau dieses Teil zuerst aufgebraucht wird,
    ist es nach wenigen Treffern weg und der Pool fällt auf die Jacke zurück.

    Bei **gleicher Reduktion** zuerst das *kleinere* Teil (weniger Kästchen):
    so wird es fertig aufgebraucht, statt dass mehrere Teile halb
    angeknackst herumliegen. Danach die Kennung, damit die Reihenfolge bei
    völligem Gleichstand reproduzierbar bleibt und nicht von der Sortierung
    der Datenbankabfrage abhängt.

    **Zerstörte Teile fallen heraus** (0 Kästchen): sie wirken nicht mehr und
    gelten auch nicht mehr als ausgerüstet (siehe traits/routes.py, das sie
    ins Mitgeführte zurücklegt).
    """
    wirksam = [t for t in teile if t.get("ruestungKaestchenAktuell", 0) > 0]
    return sorted(
        wirksam,
        key=lambda t: (-t["ruestungReduktionBasis"], t["ruestungKaestchenAktuell"], t["id"]),
    )


def pool(teile: list[dict]) -> dict | None:
    """Alle getragenen Rüstungsteile als **eine** virtuelle Rüstung.

    Marks Vorgabe (und schon die erste Fassung des Konzepts): *"alle
    Rüstungen zu einem Pool addiert"*, ausdrücklich **ohne** Körperzonen —
    *"das ist zu kompliziert"*.

    * **Kästchen** = Summe aller Teile. Ein gemeinsamer Vorrat, wie eine
      zweite Gesundheitsleiste.
    * **Reduktion** = die des Teils mit der **besten** Basis-Reduktion (nicht
      summiert!). Die effektive Reduktion des Pools wird daraus mit dem
      **Kästchen-Verhältnis des Pools** berechnet (nicht dem des einzelnen
      Teils) — der Pool als Ganzes wird schlechter, wenn seine Gesamtsubstanz
      sinkt, nicht nur das beste Einzelteil.

    Damit trifft ein Treffer nie ein einzelnes Kleidungsstück, sondern immer
    den Pool — `berechne_treffer` wird mit diesen Werten aufgerufen. **Nur**
    `hpArt`, `hpMenge` und `kaestchenSchaden` von dort sind dann gültig; das
    Feld `kaestchenNeu` bezieht sich auf die virtuelle Gesamtrüstung und wird
    verworfen. Was die einzelnen Teile tatsächlich abbekommen, rechnet
    `verteile_kaestchenschaden`.

    Gibt None, wenn nichts (mehr) schützt — dann trifft der Schaden
    ungebremst, siehe den Aufrufer in traits/routes.py.
    """
    geordnet = reihenfolge(teile)
    if not geordnet:
        return None
    bestes = geordnet[0]
    return {
        "kaestchenAktuell": sum(t["ruestungKaestchenAktuell"] for t in geordnet),
        "kaestchenMax": sum(t["ruestungKaestchenMax"] for t in geordnet),
        "reduktionBasis": bestes["ruestungReduktionBasis"],
        "geordnet": geordnet,
    }


def uebersicht(teile: list[dict]) -> dict:
    """Der Rüstungszustand fürs Blatt: eine Kästchenreihe plus Reduktion.

    Fasst `pool` in eine anzeigefertige Form. Bewusst **serverseitig**, damit
    die Pool-Regel (Kästchen summieren, Reduktion vom besten Teil, zerstörte
    Teile ignorieren) nur an einer Stelle steht — sonst rechnet das
    Charakterblatt sie nach und läuft irgendwann mit dem auseinander, was ein
    Treffer tatsächlich anrichtet.

    `teile` steht in Verbrauchsreihenfolge, damit das Blatt zeigen kann,
    welches Stück als nächstes dran ist. `reduktionEffektiv` ist die aktuell
    wirksame Reduktion des Pools (nach den Stufen aus `reduktion_effektiv`),
    `reduktionBasis` der volle Wert bei intakter Rüstung.
    """
    gesamt = pool(teile)
    if gesamt is None:
        return {"kaestchenAktuell": 0, "kaestchenMax": 0, "reduktionBasis": 0, "reduktionEffektiv": 0, "teile": []}
    reduktion_jetzt = reduktion_effektiv(gesamt["reduktionBasis"], gesamt["kaestchenAktuell"], gesamt["kaestchenMax"])
    return {
        "kaestchenAktuell": gesamt["kaestchenAktuell"],
        "kaestchenMax": gesamt["kaestchenMax"],
        "reduktionBasis": gesamt["reduktionBasis"],
        "reduktionEffektiv": reduktion_jetzt,
        "teile": [
            {
                "id": t["id"],
                "name": t["name"],
                "kaestchenAktuell": t["ruestungKaestchenAktuell"],
                "kaestchenMax": t["ruestungKaestchenMax"],
                "reduktion": t["ruestungReduktionBasis"],
            }
            for t in gesamt["geordnet"]
        ],
    }


def verteile_kaestchenschaden(geordnet: list[dict], kaestchen_schaden: int) -> list[dict]:
    """Wer vom Kästchenschaden des Pools was abbekommt.

    Frisst sich in der Reihenfolge aus `reihenfolge` durch: das Teil mit der
    besten Reduktion zuerst, der Überlauf ins nächste. Liefert nur die
    tatsächlich betroffenen Teile; wer nichts abbekommen hat, steht nicht in
    der Liste und muss auch nicht geschrieben werden.
    """
    folgen: list[dict] = []
    rest = max(0, kaestchen_schaden)
    for t in geordnet:
        if rest <= 0:
            break
        verlust = min(rest, t["ruestungKaestchenAktuell"])
        rest -= verlust
        kaestchen_neu = t["ruestungKaestchenAktuell"] - verlust
        folgen.append(
            {
                "id": t["id"],
                "name": t["name"],
                "verlust": verlust,
                "kaestchenNeu": kaestchen_neu,
                "zerstoert": kaestchen_neu <= 0,
            }
        )
    return folgen


def repariere(kaestchen_aktuell: int, kaestchen_max: int, betrag: int) -> dict:
    """Kästchen auffüllen.

    `betrag` ist, wie viele Kästchen repariert werden — das Ergebnis einer
    Hardware-Probe (`selbstreparatur_ergebnis`) oder das, wofür beim Händler
    bezahlt wurde (`haendler_reparatur_preis`). Diese Funktion kennt nur die
    Rechnung, nicht die Probe oder den Preis.

    Die Reduktion braucht seit dem Umbau auf gestufte Werte **keine eigene
    Reparatur mehr** — sie folgt automatisch aus dem wiederhergestellten
    Kästchen-Verhältnis (`reduktion_effektiv`).
    """
    betrag = max(0, betrag)
    kaestchen_neu = min(kaestchen_max, kaestchen_aktuell + betrag)
    return {"kaestchenNeu": kaestchen_neu}


# =====================================================================
# Reparatur (23.09.2026, Marks Entscheidungen per clarify — siehe
# docs/api/ruestung.md "Reparatur" für die volle Herleitung)
#
# Zwei Wege, dieselbe Zielgröße (Kästchen auffüllen):
#
# (A) SELBST REPARIEREN — Hardware-Skill-Probe + Material, kein Geld.
# (B) HÄNDLER — reine Geldsache, kein Wurf, dafür eine Verhandlung
#     (SL macht einen Preisvorschlag, der Spieler nimmt an oder lehnt ab —
#     siehe app/mitteilungen/ für den Verhandlungs-Popup-Mechanismus).
# =====================================================================


def reparatur_schwelle(kaestchen_max: int) -> int:
    """Ab wie vielen Erfolgen die Hardware-Probe überhaupt etwas repariert.

    **Die Hälfte des Kästchen-Max, abgerundet** (Marks Vorgabe) — je robuster
    die Rüstung gebaut ist, desto mehr Können braucht ihre Reparatur. Nur der
    ÜBERSCHUSS über diese Schwelle wird zu reparierten Kästchen, siehe
    `selbstreparatur_ergebnis`.
    """
    return max(0, kaestchen_max) // 2


def hardware_probe_pool(werte: dict[str, int]) -> int:
    """Der Würfelpool für die Reparatur-Probe: Maker (Hardware) + Intelligenz.

    Intelligenz statt Geistesschärfe, weil Reparieren planvolles Vorgehen ist
    ("Probleme lösen, Zusammenhänge erkennen", TRAIT_BESCHREIBUNGEN in
    traits/seed.py) und kein Reflex — anders als z.B. die Initiative-Formel.
    """
    return max(0, int(werte.get("Maker (Hardware)", 0)) + int(werte.get("Intelligenz", 0)))


def selbstreparatur_ergebnis(erfolge: int, kaestchen_max: int, material_kapazitaet: int) -> dict:
    """Was die Hardware-Probe tatsächlich repariert.

    Marks Vorgabe, an einem Beispiel: Max 10 → Schwelle 5. Bei 8 Erfolgen
    werden **3** Kästchen repariert (der Überschuss über die Schwelle), bei
    5 oder weniger Erfolgen **0** — die Probe hat nicht gereicht, um
    überhaupt etwas zu bewirken, nicht nur "weniger".

    `material_kapazitaet` ist der harte Deckel: selbst ein sehr guter Wurf
    repariert nie mehr, als das eingesetzte Material an Kästchen abdeckt
    (kleines Kit an einer schwer beschädigten Rüstung bleibt also begrenzt
    wirksam, auch bei einem Kritischen Erfolg).
    """
    schwelle = reparatur_schwelle(kaestchen_max)
    ueberschuss = max(0, erfolge - schwelle)
    repariert = min(ueberschuss, max(0, material_kapazitaet))
    return {"schwelle": schwelle, "ueberschuss": ueberschuss, "repariert": repariert}


def summe_quadrate(n: int) -> int:
    """1² + 2² + ... + n² — geschlossene Formel, kein Schleifen-Summieren."""
    n = max(0, n)
    return n * (n + 1) * (2 * n + 1) // 6


def haendler_reparatur_preis(
    fehlende_kaestchen: int, kaestchen_max: int, neuwert: int, deckel_anteil: float = 0.75
) -> int:
    """Was der Händler für die Reparatur von `fehlende_kaestchen` Kästchen verlangt.

    **Herleitung** (Marks Vorgabe: quadratisch/progressiv, mit hartem
    75%-Deckel bei Totalschaden):

    Der naheliegende Ansatz ist ein Grenzpreis je Kästchen, der mit dem
    Anteil am Kästchen-Max quadratisch wächst:

        kosten(i) = basispreis · (i / kaestchenMax)²   für das i-te fehlende
                    Kästchen (i = 1..N), aufsummiert über N.

    Das allein braucht aber einen `basispreis`, den man für jede Rüstung
    einzeln kalibrieren müsste, damit der Deckel bei N=kaestchenMax passt.
    Stattdessen wird `basispreis` direkt so gewählt, dass die Summe bei
    **N = kaestchenMax** (Totalschaden) exakt `deckel_anteil · neuwert`
    ergibt — nach Auflösen von

        Σ_{i=1}^{max} basispreis · (i/max)²  =  deckel_anteil · neuwert

    nach `basispreis` und Zurückeinsetzen bleibt für ein beliebiges N:

        kosten(N) = deckel_anteil · neuwert · (Σ_{i=1}^{N} i²) / (Σ_{i=1}^{max} i²)

    — der Anteil der Quadratsumme bis N an der Quadratsumme bis Max, skaliert
    auf den Deckel. Das ist **dieselbe** quadratische Formel wie oben (nur
    ohne den Umweg über einen separat zu kalibrierenden Basispreis), erfüllt
    den Deckel bei Totalschaden **exakt per Konstruktion** (Anteil = 1 bei
    N=max) und ist trotzdem progressiv: der Grenzpreis für das i-te Kästchen
    wächst mit i² — die letzten Kästchen vor dem Ziel sind spürbar teurer als
    die ersten (glatte Rüstung reparieren ist billig, die letzten Risse vor
    "wie neu" sind das teure Handwerk).

    `int()` rundet für positive Werte immer ab (floor) — der Deckel wird also
    **nie** überschritten, auch nicht durch Rundung.
    """
    if kaestchen_max <= 0 or neuwert <= 0:
        return 0
    n = max(0, min(fehlende_kaestchen, kaestchen_max))
    gesamt_quadrate = summe_quadrate(kaestchen_max)
    if gesamt_quadrate <= 0:
        return 0
    anteil = summe_quadrate(n) / gesamt_quadrate
    deckel = neuwert * deckel_anteil
    return int(deckel * anteil)
