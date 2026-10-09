import { useEffect, useMemo, useRef, useState } from "react";
import { lexikonApi, type LexikonEintrag, type LexikonKategorie } from "./api";
import { KACHEL_STIL, useProSeite } from "../items/kachelraster";
import { Fenster } from "../shell/Fenster";
import { RichTextEditor } from "../richtext/RichTextEditor";
import { parseRichText, serializeRichText } from "../richtext/content";
import { useAutosave } from "../shell/autosave";
import { spielernotizenApi } from "../spielernotizen/api";
import type { JSONContent } from "@tiptap/react";
import "../items/gegenstaende.css";
import "./lexikon.css";

/**
 * Spieler-Lexikon — "Gedächtnis der Welt" aus Spielersicht (09.10.2026,
 * siehe docs/wiki/entities/spieler-lexikon.md). Zeigt nur, was der eigene
 * PC über die automatische ENTDECKT-Kette erreicht hat — Existenz (Name
 * +Bild) ist dabei unabhängig von der Beschreibung, die weiterhin per
 * SL-Freigabe (Wissenswurf) aufgedeckt wird.
 *
 * Gleiches Kachelraster+Popup-Muster wie FloraFaunaUebersicht.tsx (SL-Seite)
 * — aber rein lesend, mit Favoriten und Notiz-Unterpunkt statt Bearbeiten.
 */

const KATEGORIEN: { id: LexikonKategorie; label: string; symbol: string }[] = [
  { id: "welt", label: "Welt", symbol: "⌖" },
  { id: "fauna", label: "Fauna", symbol: "❖" },
  { id: "flora", label: "Flora", symbol: "🌿" },
  { id: "objekte", label: "Objekte", symbol: "◈" },
];

type Sortierung = "naehe" | "alphabetisch" | "favoriten";

export function LexikonAnsicht() {
  const [eintraege, setEintraege] = useState<LexikonEintrag[]>([]);
  const [laden, setLaden] = useState(true);
  const [kategorie, setKategorie] = useState<LexikonKategorie>("welt");
  const [sortierung, setSortierung] = useState<Sortierung>("naehe");
  const [suche, setSuche] = useState("");
  const [offen, setOffen] = useState<LexikonEintrag | null>(null);
  const rasterRef = useRef<HTMLDivElement>(null);
  const proSeite = useProSeite(rasterRef);
  const [seite, setSeite] = useState(0);

  async function neuLaden() {
    const daten = await lexikonApi.liste();
    setEintraege(daten);
    setOffen((alt) => (alt ? daten.find((e) => e.id === alt.id) ?? null : null));
  }

  useEffect(() => {
    setLaden(true);
    neuLaden().finally(() => setLaden(false));
  }, []);

  const gefiltertNachKategorie = useMemo(
    () => eintraege.filter((e) => e.kategorie === kategorie),
    [eintraege, kategorie],
  );

  const gefiltert = useMemo(() => {
    const basis =
      sortierung === "favoriten" ? gefiltertNachKategorie.filter((e) => e.favorisiert) : gefiltertNachKategorie;
    const s = suche.trim().toLowerCase();
    const nachSuche = s ? basis.filter((e) => e.name.toLowerCase().includes(s)) : basis;
    const sortiert = [...nachSuche];
    if (sortierung === "alphabetisch") {
      sortiert.sort((a, b) => a.name.localeCompare(b.name, "de"));
    } else {
      // "naehe" (Default) und "favoriten": erst nach struktureller Nähe,
      // bei Gleichstand alphabetisch als Tiebreak.
      sortiert.sort((a, b) => a.naehe - b.naehe || a.name.localeCompare(b.name, "de"));
    }
    return sortiert;
  }, [gefiltertNachKategorie, suche, sortierung]);

  useEffect(() => {
    setSeite(0);
  }, [kategorie, suche, sortierung]);

  const seiten = Math.max(1, Math.ceil(gefiltert.length / proSeite));
  const aktuelleSeite = Math.min(seite, seiten - 1);
  const sichtbar = gefiltert.slice(aktuelleSeite * proSeite, (aktuelleSeite + 1) * proSeite);

  async function favoritToggle(e: LexikonEintrag) {
    if (e.favorisiert) {
      await lexikonApi.favorisierenEntfernen(e.id);
    } else {
      await lexikonApi.favorisieren(e.id);
    }
    await neuLaden();
  }

  if (laden) return <p style={{ color: "var(--text-leise)" }}>Lade Lexikon…</p>;

  return (
    <div className="gg-seite" style={KACHEL_STIL}>
      <div className="lx-kategorien">
        {KATEGORIEN.map((k) => (
          <button
            key={k.id}
            type="button"
            className={kategorie === k.id ? "lx-kategorie-aktiv" : ""}
            onClick={() => setKategorie(k.id)}
          >
            <span aria-hidden="true">{k.symbol}</span> {k.label}
            <span className="lx-kategorie-zahl">{eintraege.filter((e) => e.kategorie === k.id).length}</span>
          </button>
        ))}
      </div>

      <div className="gg-kopf">
        <input
          className="gg-suche"
          type="search"
          placeholder="Suchen — Name"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
        />
        <select value={sortierung} onChange={(e) => setSortierung(e.target.value as Sortierung)}>
          <option value="naehe">In meiner Nähe</option>
          <option value="alphabetisch">Alphabetisch</option>
          <option value="favoriten">★ Favoriten</option>
        </select>
        <span className="gg-anzahl">
          {gefiltert.length} von {gefiltertNachKategorie.length}
        </span>
      </div>

      <div className="gg-raster" ref={rasterRef}>
        {sichtbar.map((e) => (
          <button key={e.id} type="button" className="gg-kachel" onClick={() => setOffen(e)} title={e.name}>
            <span className="gg-kachel-bild">
              {e.bildUrl ? (
                <img src={e.bildUrl} alt="" />
              ) : (
                <span aria-hidden="true">{KATEGORIEN.find((k) => k.id === e.kategorie)?.symbol}</span>
              )}
              {e.favorisiert && <span className="lx-favorit-marke" aria-hidden="true">★</span>}
            </span>
            <span className="gg-kachel-name">{e.name}</span>
            {!e.beschreibungSichtbar && <span className="lx-gesperrt">noch nicht erforscht</span>}
          </button>
        ))}
      </div>

      {eintraege.length === 0 && (
        <p className="gg-leer">Noch nichts entdeckt — erkunde die Welt, um hier Einträge zu sehen.</p>
      )}
      {gefiltertNachKategorie.length === 0 && eintraege.length > 0 && (
        <p className="gg-leer">In dieser Kategorie noch nichts entdeckt.</p>
      )}
      {gefiltertNachKategorie.length > 0 && gefiltert.length === 0 && <p className="gg-leer">Nichts gefunden.</p>}

      {seiten > 1 && (
        <div className="gg-blaettern">
          <button type="button" onClick={() => setSeite((n) => Math.max(0, n - 1))} disabled={aktuelleSeite === 0}>
            ‹
          </button>
          <span>
            {aktuelleSeite + 1} / {seiten}
          </span>
          <button
            type="button"
            onClick={() => setSeite((n) => Math.min(seiten - 1, n + 1))}
            disabled={aktuelleSeite >= seiten - 1}
          >
            ›
          </button>
        </div>
      )}

      {offen && (
        <LexikonDetailFenster
          eintrag={offen}
          onSchliessen={() => setOffen(null)}
          onFavoritToggle={() => favoritToggle(offen)}
        />
      )}
    </div>
  );
}

function LexikonDetailFenster({
  eintrag,
  onSchliessen,
  onFavoritToggle,
}: {
  eintrag: LexikonEintrag;
  onSchliessen: () => void;
  onFavoritToggle: () => void;
}) {
  const [unteransicht, setUnteransicht] = useState<"uebersicht" | "notizen">("uebersicht");
  const [notizId, setNotizId] = useState<string | null>(null);
  const [notizDoc, setNotizDoc] = useState<JSONContent>(parseRichText(""));
  const [notizLaedt, setNotizLaedt] = useState(false);

  // bezugTyp folgt derselben Kategorie-Zuordnung wie im Backend
  // (lexikon/repository.py::_KATEGORIE_VON_LABEL) — nur umgekehrt aufgelöst.
  const bezugTyp = eintrag.kategorie === "fauna" ? "Person" : eintrag.kategorie === "flora" ? "Gewaechs"
    : eintrag.kategorie === "objekte" ? "Gegenstand" : "Ort";

  async function notizOeffnen() {
    setNotizLaedt(true);
    try {
      const notiz = await spielernotizenApi.fuerLexikonEintrag(bezugTyp, eintrag.id, `Notiz: ${eintrag.name}`);
      setNotizId(notiz.id);
      setNotizDoc(parseRichText(notiz.inhalt));
    } finally {
      setNotizLaedt(false);
    }
  }

  const autosaveNotiz = useAutosave(async (doc: JSONContent) => {
    if (!notizId) return;
    await spielernotizenApi.aendern(notizId, { inhalt: serializeRichText(doc) });
  });

  return (
    <Fenster offen titel={eintrag.name} unterzeile="Lexikon" kennung={`lexikon-${eintrag.id}`} onSchliessen={onSchliessen}>
      <div className="pcd-inhalt">
        <nav className="pcd-nav">
          <button
            type="button"
            className={unteransicht === "uebersicht" ? "pcd-nav-aktiv" : ""}
            onClick={() => setUnteransicht("uebersicht")}
          >
            Übersicht
          </button>
          <button
            type="button"
            className={unteransicht === "notizen" ? "pcd-nav-aktiv" : ""}
            onClick={() => {
              setUnteransicht("notizen");
              if (!notizId) notizOeffnen();
            }}
          >
            Meine Notizen
          </button>
        </nav>

        <div className="pcd-bereich">
          {unteransicht === "uebersicht" && (
            <div className="lx-detail">
              <div className="lx-detail-kopf">
                {eintrag.bildUrl && <img src={eintrag.bildUrl} alt="" className="lx-detail-bild" />}
                <button type="button" className="lx-favorit-knopf" onClick={onFavoritToggle}>
                  {eintrag.favorisiert ? "★ Favorisiert" : "☆ Favorisieren"}
                </button>
              </div>
              {eintrag.beschreibungSichtbar ? (
                <p>{eintrag.beschreibung}</p>
              ) : (
                <p className="lx-gesperrt-text">{eintrag.beschreibung}</p>
              )}
            </div>
          )}

          {unteransicht === "notizen" && (
            <div className="pcd-editor-bereich">
              {notizLaedt && <p style={{ color: "var(--text-leise)" }}>Lade…</p>}
              {!notizLaedt && notizId && (
                <RichTextEditor
                  content={notizDoc}
                  versteckenErlaubt={false}
                  onChange={(doc) => {
                    setNotizDoc(doc);
                    autosaveNotiz(doc);
                  }}
                  minHeight={180}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </Fenster>
  );
}
