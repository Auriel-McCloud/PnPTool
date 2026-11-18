import { useEffect, useMemo, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { entitiesApi, type CritterEintrag } from "../entities/api";
import { haendlerApi, type PetSortimentEintrag } from "./api";
import "./shop.css";
import { vorschau } from "../shell/vorschau";

/**
 * SL-Auswahl für den Tierladen (18.11.2026): welchen fertig gebauten,
 * besitzerlosen Critter bietet dieser Laden an, zu welchem Preis.
 *
 * Mark: die SL baut den Critter fertig (voller Bogen, Begleiter-Verwaltung)
 * — hier wird er nur noch an den Laden gehängt, kein neues Datenmodell nötig
 * (Kandidaten kommen aus der schon bestehenden `entitiesApi.listCritter`,
 * gefiltert auf besitzerlos, kein eigener Lookup-Endpunkt).
 */
export function PetAnbietenPopup({
  offen,
  campaignId,
  haendlerId,
  bereitsImAngebot,
  onGeaendert,
  onSchliessen,
}: {
  offen: boolean;
  campaignId: string;
  haendlerId: string;
  bereitsImAngebot: PetSortimentEintrag[];
  onGeaendert: () => void;
  onSchliessen: () => void;
}) {
  const [critter, setCritter] = useState<CritterEintrag[]>([]);
  const [gewaehlt, setGewaehlt] = useState<string | null>(null);
  const [preis, setPreis] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    entitiesApi.listCritter(campaignId).then(setCritter).catch(() => setCritter([]));
  }, [offen, campaignId]);

  const bereitsDrin = useMemo(() => new Set(bereitsImAngebot.map((p) => p.critterId)), [bereitsImAngebot]);
  const kandidaten = useMemo(
    () => critter.filter((c) => !c.besitzerId && !bereitsDrin.has(c.id)).sort((a, b) => a.name.localeCompare(b.name, "de")),
    [critter, bereitsDrin],
  );

  function zuruecksetzenUndSchliessen() {
    setGewaehlt(null);
    setPreis("");
    setFehler(null);
    onSchliessen();
  }

  async function anbieten() {
    if (!gewaehlt) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await haendlerApi.petVerkaufen(campaignId, haendlerId, gewaehlt, preis.trim() ? Number(preis) : 0);
      onGeaendert();
      zuruecksetzenUndSchliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Anbieten fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="Pet anbieten"
      unterzeile="Nur fertig gebaute, noch besitzerlose Critter — baue sie in der Begleiter-Verwaltung"
      kennung={`pet-anbieten:${haendlerId}`}
      breit
      onSchliessen={zuruecksetzenUndSchliessen}
    >
      {kandidaten.length === 0 && (
        <p className="shop-leer">
          Kein passender Critter. Lege ihn zuerst in der Begleiter-Verwaltung an, ohne ihn einem Spieler zuzuweisen.
        </p>
      )}
      <div className="shop-waren-raster" style={{ maxHeight: "48vh", overflowY: "auto" }}>
        {kandidaten.map((c) => (
          <button
            key={c.id}
            type="button"
            className="shop-ware"
            data-gewaehlt={gewaehlt === c.id}
            onClick={() => setGewaehlt((alt) => (alt === c.id ? null : c.id))}
            title={c.name}
          >
            {gewaehlt === c.id && (
              <span className="shop-ware-gewaehlt-marke" aria-hidden="true">
                ✓
              </span>
            )}
            <span className="shop-ware-bild">
              {c.bildUrl ? <img src={vorschau(c.bildUrl)} loading="lazy" decoding="async" alt="" /> : null}
            </span>
            <span className="shop-ware-name">{c.alias || c.name}</span>
          </button>
        ))}
      </div>

      <div className="shop-editor-hinzufuegen" style={{ marginTop: 12 }}>
        <input
          type="number"
          min={0}
          value={preis}
          onChange={(e) => setPreis(e.target.value)}
          placeholder="Preis (¥)"
          disabled={laeuft}
        />
        <button type="button" onClick={anbieten} disabled={laeuft || !gewaehlt}>
          {laeuft ? "Bietet an…" : "Anbieten"}
        </button>
      </div>
      {fehler && <p className="shop-ware-fehler">{fehler}</p>}
    </Fenster>
  );
}
