import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { haendlerApi, type HaendlerGesicht } from "./api";
import { entitiesApi, type Person } from "../entities/api";
import { HaendlerBearbeiten } from "./HaendlerBearbeiten";
import { TypKachelAuswahl } from "../items/TypKachelAuswahl";
import "./shop.css";

/**
 * Ort-seitiger Einstieg ins Shop-System. Der Laden IST der Ort: Ware,
 * Spezialisierung, Vertriebsart und Tutorial-Flag hängen hier, nicht an
 * einer Person (10.10.2026, Mark: Shops nicht mehr über NPCs anlegen).
 *
 * Ein Verkäufer (BETREIBT) ist optional und nur für Verhandeln und Kontakte.
 * Ohne Gesicht ist der Laden trotzdem ein Shop.
 */
export function OrtLadenFenster({
  campaignId,
  ortId,
  ortName,
  offen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  ortId: string;
  ortName: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Ruft den Ort-Refresh der Eltern auf (istShop kann sich ändern). */
  onGeaendert: () => void;
}) {
  const [verkaeufer, setVerkaeufer] = useState<HaendlerGesicht[]>([]);
  const [npcs, setNpcs] = useState<Person[]>([]);
  const [neuerVerkaeuferId, setNeuerVerkaeuferId] = useState("");
  const [läuft, setLäuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);
  const [sortimentOffen, setSortimentOffen] = useState(false);
  const [istAktiv, setIstAktiv] = useState(false);
  const [geladen, setGeladen] = useState(false);
  const [spezialisierung, setSpezialisierung] = useState<string[]>([]);
  const [vertriebsart, setVertriebsart] = useState<"PHYSISCH" | "DIGITAL">("PHYSISCH");
  const [istTutorial, setIstTutorial] = useState(false);
  const [abschaltenOffen, setAbschaltenOffen] = useState(false);

  async function laden() {
    const [ort, alleNpcs] = await Promise.all([
      entitiesApi.getOrt(campaignId, ortId),
      entitiesApi.listPersonen(campaignId, { personType: "NPC" }),
    ]);
    setNpcs(alleNpcs);
    setSpezialisierung(ort.spezialisierung ?? []);
    setVertriebsart(ort.vertriebsart ?? "PHYSISCH");
    setIstTutorial(ort.istTutorialShop ?? false);
    const aktiv = ort.istShop ?? false;
    setIstAktiv(aktiv);
    if (aktiv) {
      try {
        const shop = await haendlerApi.einzeln(campaignId, ortId);
        setVerkaeufer(shop.haendler ?? []);
      } catch {
        setVerkaeufer([]);
      }
    } else {
      setVerkaeufer([]);
    }
    setGeladen(true);
  }

  useEffect(() => {
    if (!offen) return;
    laden().catch(() => setFehler("Laden fehlgeschlagen"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, campaignId, ortId]);

  const wählbareNpcs = npcs.filter((p) => !verkaeufer.some((v) => v.id === p.id));

  function typUmschalten(typ: string) {
    setSpezialisierung((alt) => (alt.includes(typ) ? alt.filter((t) => t !== typ) : [...alt, typ]));
  }

  async function ausfuehren(aktion: () => Promise<unknown>) {
    setLäuft(true);
    setFehler(null);
    try {
      await aktion();
      await laden();
      onGeaendert();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Aktion fehlgeschlagen");
    } finally {
      setLäuft(false);
    }
  }

  function einstellungen() {
    return { spezialisierung, vertriebsart, istTutorialShop: istTutorial };
  }

  async function aktivieren() {
    await ausfuehren(() => entitiesApi.updateOrt(campaignId, ortId, { istShop: true, ...einstellungen() }));
  }

  async function speichern() {
    await ausfuehren(() => entitiesApi.updateOrt(campaignId, ortId, einstellungen()));
  }

  async function abschalten() {
    setAbschaltenOffen(false);
    await ausfuehren(() => entitiesApi.updateOrt(campaignId, ortId, { istShop: false }));
  }

  async function verkaeuferHinzufuegen() {
    if (!neuerVerkaeuferId || !istAktiv) return;
    const npc = npcs.find((p) => p.id === neuerVerkaeuferId);
    await ausfuehren(async () => {
      if (!npc?.istHaendler) {
        await entitiesApi.updatePerson(campaignId, neuerVerkaeuferId, { istHaendler: true });
      }
      await haendlerApi.standortSetzen(campaignId, neuerVerkaeuferId, ortId);
    });
    setNeuerVerkaeuferId("");
  }

  async function verkaeuferEntfernen(personId: string) {
    await ausfuehren(async () => {
      await haendlerApi.standortSetzen(campaignId, personId, null);
      await entitiesApi.updatePerson(campaignId, personId, { istHaendler: false });
    });
  }

  return (
    <>
      <Fenster
        offen={offen}
        titel={`${ortName} — Laden`}
        unterzeile={
          !geladen
            ? "Lädt…"
            : istAktiv
              ? istTutorial
                ? "Tutorial-Shop — nur im Freebees-Schritt, nicht in der Shop-Übersicht"
                : "Ware am Ort. Verkäufer nur für Verhandeln und Kontakte."
              : "Noch kein Laden — den Ort selbst zum Shop machen"
        }
        kennung={`ort-laden:${ortId}`}
        onSchliessen={onSchliessen}
      >
        <div className="shop-editor">
          {fehler && <p className="shop-ware-fehler">{fehler}</p>}

          <section>
            <h3 className="gg-abschnitt">
              <span>Laden</span>
            </h3>
            <p className="shop-ware-hinweis">
              Keine Kachel = Gemischtwarenladen, zeigt den gesamten passenden Katalog. Leuchtende Kacheln sind die
              Arten, die dieser Laden führt.
            </p>
            <TypKachelAuswahl gewaehlt={spezialisierung} disabled={läuft} onWaehlen={typUmschalten} />
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button
                type="button"
                onClick={() => setVertriebsart("PHYSISCH")}
                disabled={läuft}
                style={
                  vertriebsart === "PHYSISCH" ? { borderColor: "var(--neon)", color: "var(--neon)" } : undefined
                }
              >
                Vor Ort
              </button>
              <button
                type="button"
                onClick={() => setVertriebsart("DIGITAL")}
                disabled={läuft}
                style={vertriebsart === "DIGITAL" ? { borderColor: "var(--neon)", color: "var(--neon)" } : undefined}
              >
                Online
              </button>
            </div>
            <p className="shop-ware-hinweis" style={{ marginTop: 6 }}>
              {vertriebsart === "DIGITAL"
                ? "Kein Verhandeln, ein Kauf legt eine Bestellung an — die Lieferung gibt die SL später frei."
                : "Verhandeln möglich, Ware wird bei Kauf sofort übergeben."}
            </p>
            <label style={{ fontSize: "0.9em", display: "flex", alignItems: "center", gap: 6, marginTop: 12 }}>
              <input
                type="checkbox"
                checked={istTutorial}
                onChange={(e) => setIstTutorial(e.target.checked)}
                disabled={läuft}
              />
              Tutorial-Shop
            </label>
            <p className="shop-ware-hinweis" style={{ marginTop: 6 }}>
              Erscheint nur im Freebees-Schritt der Charaktererstellung, nicht in der normalen Shop-Übersicht. Pro
              Kampagne zählt der erste. Kein Verhandeln, keine Achievement-Auslöser.
            </p>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              {istAktiv ? (
                <button type="button" onClick={speichern} disabled={läuft}>
                  Einstellungen speichern
                </button>
              ) : (
                <button type="button" onClick={aktivieren} disabled={läuft}>
                  Zum Laden machen
                </button>
              )}
            </div>
          </section>

          <section>
            <h3 className="gg-abschnitt">
              <span>Verkäufer</span>
              <span className="gg-abschnitt-zahl">{verkaeufer.length}</span>
            </h3>
            <p className="shop-ware-hinweis">
              Optional. Nur für Verhandeln und Kontakte — das Sortiment bleibt am Ort, auch ohne Gesicht.
            </p>
            <div className="shop-editor-liste">
              {verkaeufer.map((v) => (
                <div key={v.id} className="shop-editor-zeile">
                  <span className="shop-editor-zeile-name">{v.name}</span>
                  <span className="shop-editor-zeile-knoepfe">
                    <button type="button" onClick={() => verkaeuferEntfernen(v.id)} disabled={läuft}>
                      Entfernen
                    </button>
                  </span>
                </div>
              ))}
              {verkaeufer.length === 0 && <p className="shop-leer">Kein Verkäufer an diesem Laden.</p>}
            </div>
            <div className="shop-editor-hinzufuegen">
              <select
                value={neuerVerkaeuferId}
                onChange={(e) => setNeuerVerkaeuferId(e.target.value)}
                disabled={läuft || !istAktiv}
              >
                <option value="">— NPC wählen —</option>
                {wählbareNpcs.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
              <button type="button" onClick={verkaeuferHinzufuegen} disabled={läuft || !istAktiv || !neuerVerkaeuferId}>
                Hinzufügen
              </button>
            </div>
            {!istAktiv && <p className="shop-ware-hinweis">Erst zum Laden machen, dann ein Gesicht dranhängen.</p>}
          </section>

          {istAktiv && (
            <section>
              <button type="button" onClick={() => setSortimentOffen(true)} disabled={läuft}>
                🛒 Sortiment bearbeiten
              </button>
            </section>
          )}

          {istAktiv && (
            <section>
              <button
                type="button"
                style={{ borderColor: "var(--signal)", color: "var(--signal)" }}
                onClick={() => setAbschaltenOffen(true)}
                disabled={läuft}
              >
                Kein Laden mehr
              </button>
            </section>
          )}
        </div>

        {sortimentOffen && (
          <HaendlerBearbeiten
            campaignId={campaignId}
            haendlerId={ortId}
            offen={sortimentOffen}
            onSchliessen={() => setSortimentOffen(false)}
            onGeaendert={onGeaendert}
          />
        )}
      </Fenster>

      {abschaltenOffen && (
        <Bestaetigung
          titel={`${ortName} ist kein Laden mehr?`}
          text="Verschwindet aus der Shop-Übersicht und aus dem Tutorial-Schritt. Sortiment, Tutorial-Flag und Verkäufer bleiben erhalten und sind wieder da, sobald du den Ort erneut zum Laden machst."
          jaText="Kein Laden mehr"
          onJa={abschalten}
          onNein={() => setAbschaltenOffen(false)}
        />
      )}
    </>
  );
}
