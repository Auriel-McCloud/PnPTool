import { useEffect, useState } from "react";
import { entitiesApi, type Person } from "../entities/api";
import { haendlerApi } from "./api";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { TYP_OPTIONEN } from "../items/typKatalog";

/**
 * Macht aus einem NPC einen Händler (istHaendler=true) oder nimmt das wieder
 * zurück — ein Händler ist KEIN eigenes Node-Label, sondern derselbe
 * Person-Knoten mit einem Flag (analog istCritter/istKI, siehe
 * app/entities/schemas.py, app/haendler/repository.py). Deckt hier nur die
 * beiden Shop-Grundeinstellungen ab: Spezialisierung (welche Gegenstandstypen
 * der automatische Katalog-Bestand zeigt) und Vertriebsart (physisch/
 * digital) — das eigentliche Sortiment (Ware/Preise) pflegt sich weiterhin
 * über HaendlerBearbeiten im Shop-Bereich.
 *
 * Aufrufbar aus dem NPC-Detail-Popup (NPCDetail.tsx) — vorher gab es dafür
 * gar keine Oberfläche, nur die rohe API.
 */
export function HaendlerEinstellungenFenster({
  campaignId,
  person,
  offen,
  onSchliessen,
  onGeaendert,
}: {
  campaignId: string;
  person: Person;
  offen: boolean;
  onSchliessen: () => void;
  /** Liefert die aktualisierte Person zurück, damit der Aufrufer sie ohne
   * Neuladen sofort übernehmen kann (dasselbe Muster wie BegleiterFenster::
   * onSofortGeaendert). */
  onGeaendert: (neu: Person) => void;
}) {
  const warSchonHaendler = person.istHaendler ?? false;
  const [spezialisierung, setSpezialisierung] = useState<string[]>(person.spezialisierung ?? []);
  const [vertriebsart, setVertriebsart] = useState<"PHYSISCH" | "DIGITAL">(person.vertriebsart ?? "PHYSISCH");
  const [istTutorial, setIstTutorial] = useState(person.istTutorialHaendler ?? false);
  const [sendet, setSendet] = useState(false);
  const [entfernenOffen, setEntfernenOffen] = useState(false);

  // Frisch beginnen bei jedem Öffnen — sonst stehen noch Werte vom zuletzt
  // bearbeiteten NPC da (dasselbe Muster wie BegleiterAnlegenFenster).
  useEffect(() => {
    if (offen) {
      setSpezialisierung(person.spezialisierung ?? []);
      setVertriebsart(person.vertriebsart ?? "PHYSISCH");
      setIstTutorial(person.istTutorialHaendler ?? false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen, person.id]);

  function typUmschalten(typ: string) {
    setSpezialisierung((alt) => (alt.includes(typ) ? alt.filter((t) => t !== typ) : [...alt, typ]));
  }

  async function speichern() {
    setSendet(true);
    try {
      const neu = await entitiesApi.updatePerson(campaignId, person.id, {
        istHaendler: true,
        istTutorialHaendler: istTutorial,
        spezialisierung,
        vertriebsart,
      });
      const shops = await haendlerApi.alle(campaignId);
      const shop = shops.find((s) => (s.haendler ?? []).some((g) => g.id === person.id));
      if (shop) {
        await entitiesApi.updateOrt(campaignId, shop.id, { spezialisierung, vertriebsart });
      }
      onGeaendert(neu);
    } finally {
      setSendet(false);
    }
  }

  async function entfernen() {
    setEntfernenOffen(false);
    const neu = await entitiesApi.updatePerson(campaignId, person.id, { istHaendler: false });
    onGeaendert(neu);
  }

  return (
    <>
      <Fenster
        offen={offen}
        titel={warSchonHaendler ? `${person.name} — Händler-Einstellungen` : `${person.name} zum Händler machen`}
        unterzeile="Spezialisierung und Vertriebsart — das Sortiment selbst läuft über den Shop-Bereich"
        kennung={`haendler-einstellungen:${person.id}`}
        ton="var(--bereich-npcs)"
        onSchliessen={onSchliessen}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            speichern();
          }}
          style={{ display: "flex", flexDirection: "column", gap: 16, padding: 8 }}
        >
          {!warSchonHaendler && (
            <p className="pcd-hinweis" style={{ margin: 0 }}>
              {person.name} wird ein echter Händler — erscheint danach sofort in der Shop-Übersicht.
            </p>
          )}

          <div>
            <span className="pcd-label">
              Spezialisierung (leer = Gemischtwarenladen, zeigt den gesamten passenden Katalog)
            </span>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
              {TYP_OPTIONEN.map((typ) => (
                <label key={typ} style={{ fontSize: "0.9em", display: "flex", alignItems: "center", gap: 6 }}>
                  <input type="checkbox" checked={spezialisierung.includes(typ)} onChange={() => typUmschalten(typ)} />
                  {typ}
                </label>
              ))}
            </div>
          </div>

          <div>
            <span className="pcd-label">Vertriebsart</span>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                type="button"
                onClick={() => setVertriebsart("PHYSISCH")}
                style={
                  vertriebsart === "PHYSISCH"
                    ? { borderColor: "var(--neon)", color: "var(--neon)" }
                    : undefined
                }
              >
                Vor Ort
              </button>
              <button
                type="button"
                onClick={() => setVertriebsart("DIGITAL")}
                style={
                  vertriebsart === "DIGITAL"
                    ? { borderColor: "var(--neon)", color: "var(--neon)" }
                    : undefined
                }
              >
                Online
              </button>
            </div>
            <p className="pcd-hinweis" style={{ marginTop: 6 }}>
              {vertriebsart === "DIGITAL"
                ? "Kein Verhandeln, ein Kauf legt eine Bestellung an — die Lieferung gibt die SL später manuell frei."
                : "Laden mit eigenem Hintergrundbild, Verhandeln möglich, Ware wird bei Kauf sofort übergeben."}
            </p>
          </div>

          <div>
            <label style={{ fontSize: "0.9em", display: "flex", alignItems: "center", gap: 6 }}>
              <input type="checkbox" checked={istTutorial} onChange={(e) => setIstTutorial(e.target.checked)} />
              Tutorial-Shop
            </label>
            <p className="pcd-hinweis" style={{ marginTop: 6 }}>
              Erscheint NUR im Freebees-Schritt der Charaktererstellung, nicht in der normalen Shop-Übersicht —
              kein Verhandeln, keine Achievement-Auslöser.
            </p>
          </div>

          <button type="submit" disabled={sendet}>
            {sendet ? "Speichert…" : warSchonHaendler ? "Einstellungen speichern" : "Händler aktivieren"}
          </button>
        </form>

        {warSchonHaendler && (
          <div style={{ marginTop: 18, paddingTop: 14, borderTop: "1px solid var(--linie)" }}>
            <button
              type="button"
              style={{ borderColor: "var(--signal)", color: "var(--signal)" }}
              onClick={() => setEntfernenOffen(true)}
            >
              Kein Händler mehr
            </button>
          </div>
        )}
      </Fenster>

      {entfernenOffen && (
        <Bestaetigung
          titel={`${person.name} ist kein Händler mehr?`}
          text="Verschwindet aus der Shop-Übersicht. Sortiment-Einträge und bisherige Bestellungen bleiben erhalten und sind sofort wieder da, falls du ihn später erneut zum Händler machst."
          jaText="Kein Händler mehr"
          onJa={entfernen}
          onNein={() => setEntfernenOffen(false)}
        />
      )}
    </>
  );
}
