"""Rüstungssystem: Kästchen + Durchlass.

Herleitung (Gespräch Mark/Claude, 10.09.2026 — die ausführliche Begründung mit
allen Zwischenschritten und Beispielen steht in docs/api/ruestung.md, hier nur
die knappe Fassung als Code-Kommentar):

**Warum nicht einfach ein Rüstungswert, der vom Schaden abgezogen wird** (wie
der alte `kraft`-Bonus, siehe items/schemas.py)? Weil das nur zwei Zustände
kennt — "hält" oder "hält nicht mehr" — und Rüstung im Spiel nie kaputtgeht.
Mark wollte, dass Rüstung sich abnutzt und mit jedem Treffer schlechter wird,
bis sie irgendwann nichts mehr bringt.

**Die Kernidee: zwei Werte statt einem.**

* **Kästchen** (`ruestungKaestchenMax` / `ruestungKaestchenAktuell`) — wie viel
  Substanz die Rüstung hat, um Treffer zu schlucken, bevor sie reißt. Sinkt
  mit Beschädigung, wie die Gesundheit einer Person.
* **Durchlass** (`ruestungDurchlassBasis` / `ruestungDurchlassAktuell`) — die
  Größe der Lücke in der Rüstung: wie viel Schaden *garantiert* ungehindert
  durchkommt, bevor die Rüstung überhaupt die Chance hat, etwas abzufangen.
  **Niedriger ist besser** — 0 heißt "hermetisch dicht". Das ist der
  entscheidende gedankliche Unterschied zu einem klassischen Rüstungswert:
  eine dicke Lederjacke ist nicht "Rüstung 3", sie hat "Durchlass 3" — sie
  ist von Haus aus löchrig, weil sie eben nur Leder ist. Eine Bombenweste
  startet dagegen bei Durchlass 0.

  Zwei Unterwerte, weil beide Zwecke sich sonst gegenseitig kaputt rechnen
  würden (siehe "Warum Basis UND Aktuell" unten):
  - **Basis** (`...Basis`): der Ausgangswert des Gegenstands, ändert sich nur
    durch Reparatur. Fließt in die Kästchenschaden-Berechnung ein.
  - **Aktuell** (`...Aktuell`): steigt mit jedem Treffer, der die Rüstung
    beschädigt. Bestimmt, wie viel beim NÄCHSTEN Treffer garantiert an die
    Trägerin durchgeht — die Rüstung wird spürbar schlechter, je kaputter sie
    ist.

**Warum Basis UND Aktuell, nicht nur ein Wert?** Erste Fassung nutzte einen
einzigen (steigenden) Durchlass-Wert auch für den Kästchenschaden. Ergebnis:
je kaputter die Rüstung wurde, desto *kleiner* wurde ihr Überschuss über dem
(jetzt höheren) Durchlass — sie nahm also mit jedem Treffer WENIGER
Kästchenschaden, bis irgendwann gar keinen mehr. Volle Rüstung war dadurch am
leichtesten zu zerstören, angeschlagene praktisch unzerstörbar — das genaue
Gegenteil von "kaputte Sachen gehen leichter weiter kaputt". Der Fix: der
Kästchenschaden rechnet gegen die **fixe Basis**, nur der HP-Durchlass rechnet
gegen die **steigende Aktuell**-Schwelle. Damit bleibt der Kästchenschaden pro
Treffer konstant (bzw. sinkt planbar mit der Trigger-Bedingung unten), während
trotzdem mehr durchsickert, je kaputter die Rüstung wird.

**Pro Treffer:**

1. `garantiert = min(Stärke, Durchlass-Aktuell)` — das kommt so oder so durch.
2. `überschuss = max(0, Stärke - Durchlass-Basis)` — das versucht die Rüstung
   abzufangen (Berechnungsgrundlage für den Kästchenschaden, s.o.).
3. **Schaden an die Trägerin**, abgestuft statt einfach geblockt — Rüstung
   "hält nicht auf", sie "dämpft": Unheilbar wird zu Tödlich, Tödlich wird zu
   Schlag (Menge bleibt gleich), Schlag ist schon die unterste Stufe und wird
   stattdessen **halbiert** (abgerundet). Es gibt keine Schadensart *unter*
   Schlag, deshalb dort die Halbierung statt einer weiteren Abstufung.
4. **Schaden an die Rüstung (Kästchen):**
   - **Tödlich/Unheilbar:** Mark: *"das wäre ja was wie eine Explosion, da
     kann man froh sein das überstanden zu haben"* — volle Wucht, immer,
     unabhängig vom Durchlass: `Stärke` (siehe unten für Unheilbar) bzw. für
     Tödlich eine Mischung, weil hier die Rüstung ja *etwas* geleistet hat: der
     Anteil bis zur Basis-Schwelle beschädigt sie nur zur Hälfte (sie hat ihn
     ja immerhin durchgelassen, ohne wirklich zu kämpfen), der Anteil darüber
     voll 1:1.
   - **Schlag:** nur wenn der Treffer mindestens die Hälfte der *aktuellen*
     Kästchen erreicht (`2×Stärke ≥ Kästchen-Aktuell`) — sonst prallt ein
     laues Klopfen wirkungslos ab. Trifft die Bedingung zu, beschädigt der
     Überschuss (über die Basis) die Rüstung zur Hälfte.
     **Bewusst `Kästchen-Aktuell` statt `Kästchen-Max`**: dadurch wird die
     Trigger-Schwelle mit jedem Treffer niedriger — eine bereits ramponierte
     Rüstung bricht leichter weiter zusammen, ganz wie erwartet. Das ist ein
     zweiter, unabhängiger "wird schlechter"-Mechanismus neben dem
     steigenden Durchlass.
5. **Durchlass-Aktuell steigt** um genau den entstandenen Kästchenschaden,
   gedeckelt auf `Kästchen-Max` (nicht `Kästchen-Aktuell` — sonst würde der
   Deckel selbst mit jedem Treffer sinken und die Rüstung könnte nie wieder
   so schlecht werden, wie sie laut ihrer Größe eigentlich werden dürfte).
6. **Ist eine Rüstung bereits bei 0 Kästchen**, wirkt sie gar nicht mehr — der
   Treffer geht unverändert und in voller Höhe durch, ohne jede Abstufung.

**Reparatur** (Hardware-Skill-Probe oder Händler, kostet Geld/Zeit — dieser
Teil des Ablaufs existiert im Tool noch nicht, siehe docs/api/ruestung.md)
füllt Kästchen auf und senkt dabei auch den Durchlass wieder in Richtung
Basis: Mark: *"Reparatur senkt auch die Schwelle"* — eine geflickte Rüstung
sitzt wieder enger, nicht nur "irgendwie ganz".

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


def berechne_treffer(
    art: str,
    staerke: int,
    kaestchen_aktuell: int,
    kaestchen_max: int,
    durchlass_basis: int,
    durchlass_aktuell: int,
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
    - `kaestchenNeu`, `durchlassNeu`: die neuen Werte für den Gegenstand.
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
            "durchlassNeu": durchlass_aktuell,
        }

    garantiert = min(staerke, durchlass_aktuell)
    ueberschuss_basis = max(0, staerke - durchlass_basis)
    hp_art, hp_menge = _abgestufter_schaden(art, garantiert)

    if art == "aggraviert":
        # Volle Wucht, immer — siehe Modulkommentar oben.
        kaestchen_schaden = staerke
    elif art == "schwer":
        # Der Anteil bis zur Basis-Schwelle nur zur Hälfte (die Rüstung hat
        # ihn durchgelassen, ohne wirklich zu kämpfen), der Rest voll.
        kaestchen_schaden = (min(staerke, durchlass_basis) // 2) + ueberschuss_basis
    else:  # "schlag"
        # Nur ab der Hälfte der AKTUELLEN Kästchen — ein laues Klopfen
        # richtet nichts aus, egal wie kaputt die Rüstung schon ist.
        loest_aus = 2 * staerke >= kaestchen_aktuell
        kaestchen_schaden = ueberschuss_basis // 2 if loest_aus else 0

    kaestchen_schaden = min(kaestchen_schaden, kaestchen_aktuell)
    kaestchen_neu = kaestchen_aktuell - kaestchen_schaden
    # Gedeckelt auf Kästchen-MAX (nicht -aktuell): sonst sänke der Deckel mit
    # jedem Treffer mit, und die Rüstung könnte nie so schlecht werden, wie
    # ihre Größe es eigentlich zuließe.
    durchlass_neu = min(kaestchen_max, durchlass_aktuell + kaestchen_schaden)

    return {
        "hpArt": hp_art,
        "hpMenge": hp_menge,
        "kaestchenSchaden": kaestchen_schaden,
        "kaestchenNeu": kaestchen_neu,
        "durchlassNeu": durchlass_neu,
    }


def reihenfolge(teile: list[dict]) -> list[dict]:
    """In welcher Reihenfolge die getragenen Rüstungsteile aufgebraucht werden.

    **Das dichteste zuerst** — aufsteigend nach `ruestungDurchlassAktuell`.
    Marks Vorgabe: *"zuerst wird das mit dem niedrigsten Durchlasswert
    zerstört... dann der nächste"*. Die engste Schicht hält den Treffer auf
    und wird dabei verbraucht; ist sie hin, übernimmt die nächste.

    Das ist zugleich die Regel, die einen sonst offenen Missbrauch schließt:
    ein winziges Teil mit Durchlass 0 (das "kugelsichere Suspensorium") würde
    dem Pool sonst dauerhaft seine Dichtheit leihen, während eine löchrige
    Jacke die Masse der Kästchen stellt. Weil aber genau dieses Teil zuerst
    aufgebraucht wird, ist es nach einem Kästchen weg und der Pool-Durchlass
    springt sofort auf die Jacke.

    Bei **gleichem Durchlass** zuerst das *kleinere* Teil (weniger Kästchen):
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
        key=lambda t: (t["ruestungDurchlassAktuell"], t["ruestungKaestchenAktuell"], t["id"]),
    )


def pool(teile: list[dict]) -> dict | None:
    """Alle getragenen Rüstungsteile als **eine** virtuelle Rüstung.

    Marks Vorgabe (und schon die erste Fassung des Konzepts): *"alle
    Rüstungen zu einem Pool addiert"*, ausdrücklich **ohne** Körperzonen —
    *"das ist zu kompliziert"*.

    * **Kästchen** = Summe aller Teile. Ein gemeinsamer Vorrat, wie eine
      zweite Gesundheitsleiste.
    * **Durchlass** = der des **dichtesten** Teils (nicht summiert!). Von
      diesem Teil kommt auch die **Basis**, damit beide Durchlasswerte aus
      derselben Schicht stammen: sie zusammen zu mischen (etwa niedrigste
      Aktuell von einem, niedrigste Basis von einem anderen Teil) könnte
      Kästchenschaden und HP-Durchlass gegeneinander laufen lassen.

    Damit trifft ein Treffer nie ein einzelnes Kleidungsstück, sondern immer
    den Pool — `berechne_treffer` wird mit diesen Werten aufgerufen. **Nur**
    `hpArt`, `hpMenge` und `kaestchenSchaden` von dort sind dann gültig; die
    Felder `kaestchenNeu`/`durchlassNeu` beziehen sich auf die virtuelle
    Gesamtrüstung und werden verworfen. Was die einzelnen Teile tatsächlich
    abbekommen, rechnet `verteile_kaestchenschaden`.

    Gibt None, wenn nichts (mehr) schützt — dann trifft der Schaden
    ungebremst, siehe den Aufrufer in traits/routes.py.
    """
    geordnet = reihenfolge(teile)
    if not geordnet:
        return None
    dichtestes = geordnet[0]
    return {
        "kaestchenAktuell": sum(t["ruestungKaestchenAktuell"] for t in geordnet),
        "kaestchenMax": sum(t["ruestungKaestchenMax"] for t in geordnet),
        "durchlassAktuell": dichtestes["ruestungDurchlassAktuell"],
        "durchlassBasis": dichtestes["ruestungDurchlassBasis"],
        "geordnet": geordnet,
    }


def uebersicht(teile: list[dict]) -> dict:
    """Der Rüstungszustand fürs Blatt: eine Kästchenreihe plus Durchlass.

    Fasst `pool` in eine anzeigefertige Form. Bewusst **serverseitig**, damit
    die Pool-Regel (Kästchen summieren, Durchlass vom dichtesten Teil,
    zerstörte Teile ignorieren) nur an einer Stelle steht — sonst rechnet
    das Charakterblatt sie nach und läuft irgendwann mit dem auseinander,
    was ein Treffer tatsächlich anrichtet.

    `teile` steht in Verbrauchsreihenfolge, damit das Blatt zeigen kann,
    welches Stück als nächstes dran ist.
    """
    gesamt = pool(teile)
    if gesamt is None:
        return {"kaestchenAktuell": 0, "kaestchenMax": 0, "durchlass": 0, "teile": []}
    return {
        "kaestchenAktuell": gesamt["kaestchenAktuell"],
        "kaestchenMax": gesamt["kaestchenMax"],
        "durchlass": gesamt["durchlassAktuell"],
        "teile": [
            {
                "id": t["id"],
                "name": t["name"],
                "kaestchenAktuell": t["ruestungKaestchenAktuell"],
                "kaestchenMax": t["ruestungKaestchenMax"],
                "durchlass": t["ruestungDurchlassAktuell"],
            }
            for t in gesamt["geordnet"]
        ],
    }


def verteile_kaestchenschaden(geordnet: list[dict], kaestchen_schaden: int) -> list[dict]:
    """Wer vom Kästchenschaden des Pools was abbekommt.

    Frisst sich in der Reihenfolge aus `reihenfolge` durch: das dichteste
    Teil zuerst, der Überlauf ins nächste. Jedes betroffene Teil bekommt
    seinen **eigenen** Durchlass um seinen **eigenen** Verlust erhöht
    (gedeckelt auf sein eigenes Kästchen-Max) — dieselbe Regel wie bei einer
    einzelnen Rüstung, nur eben pro Stück angewandt statt auf den Pool.

    Liefert nur die tatsächlich betroffenen Teile; wer nichts abbekommen hat,
    steht nicht in der Liste und muss auch nicht geschrieben werden.
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
                "durchlassNeu": min(t["ruestungKaestchenMax"], t["ruestungDurchlassAktuell"] + verlust),
                "zerstoert": kaestchen_neu <= 0,
            }
        )
    return folgen


def repariere(
    kaestchen_aktuell: int,
    kaestchen_max: int,
    durchlass_basis: int,
    durchlass_aktuell: int,
    betrag: int,
) -> dict:
    """Kästchen auffüllen und den Durchlass symmetrisch wieder senken.

    `betrag` ist, wie viele Kästchen repariert werden (Ergebnis einer
    Hardware-Probe oder das, wofür beim Händler bezahlt wurde — **dieser Teil
    fehlt im Tool noch**, siehe docs/api/ruestung.md "Was noch fehlt"). Diese
    Funktion kennt nur die Rechnung, nicht die Probe oder den Preis.

    Mark: *"Reparatur senkt auch die Schwelle"* — genau um den reparierten
    Betrag, symmetrisch zum Kästchenschaden, der den Durchlass erhöht hat.
    Nach oben durch `Kästchen-Max`, nach unten durch die Basis gedeckelt: eine
    Reparatur macht die Rüstung nie besser als neu.
    """
    betrag = max(0, betrag)
    kaestchen_neu = min(kaestchen_max, kaestchen_aktuell + betrag)
    durchlass_neu = max(durchlass_basis, durchlass_aktuell - betrag)
    return {"kaestchenNeu": kaestchen_neu, "durchlassNeu": durchlass_neu}
