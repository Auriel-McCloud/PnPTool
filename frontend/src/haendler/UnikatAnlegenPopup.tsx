import { useState } from "react";
import { Fenster } from "../shell/Fenster";

/** Einzelstück direkt im Laden anlegen — kein KI-Umweg, keine Vorlage. */
export function UnikatAnlegenPopup({
  offen,
  typ,
  onAnlegen,
  onSchliessen,
}: {
  offen: boolean;
  typ: string;
  onAnlegen: (name: string, preis: number, description: string) => Promise<void>;
  onSchliessen: () => void;
}) {
  const [name, setName] = useState("");
  const [preis, setPreis] = useState("");
  const [beschreibung, setBeschreibung] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  function schliessen() {
    setName("");
    setPreis("");
    setBeschreibung("");
    setFehler(null);
    onSchliessen();
  }

  async function anlegen() {
    if (!name.trim()) return;
    setLaeuft(true);
    setFehler(null);
    try {
      await onAnlegen(name.trim(), preis.trim() ? Number(preis) : 0, beschreibung.trim());
      schliessen();
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Anlegen fehlgeschlagen");
    } finally {
      setLaeuft(false);
    }
  }

  return (
    <Fenster
      offen={offen}
      titel="Einzelstück anlegen"
      unterzeile={`${typ} · gibt es nur einmal, danach ist es aus dem Regal`}
      kennung="unikat-anlegen"
      onSchliessen={schliessen}
    >
      <div className="shop-editor-hinzufuegen" style={{ flexDirection: "column", alignItems: "stretch" }}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Name"
          autoFocus
          disabled={laeuft}
          onKeyDown={(e) => e.key === "Enter" && anlegen()}
        />
        <input
          type="number"
          min={0}
          value={preis}
          onChange={(e) => setPreis(e.target.value)}
          placeholder="Preis in ¥ (leer = 0)"
          disabled={laeuft}
        />
        <input
          value={beschreibung}
          onChange={(e) => setBeschreibung(e.target.value)}
          placeholder="Kurzbeschreibung (optional)"
          disabled={laeuft}
        />
        {fehler && <p className="shop-ware-fehler">{fehler}</p>}
        <div className="shop-ware-knoepfe">
          <button type="button" onClick={schliessen} disabled={laeuft}>
            Abbrechen
          </button>
          <button type="button" onClick={anlegen} disabled={laeuft || !name.trim()}>
            {laeuft ? "Legt an…" : "Ins Regal"}
          </button>
        </div>
      </div>
    </Fenster>
  );
}
