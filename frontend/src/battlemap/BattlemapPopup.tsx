import { useEffect, useRef, useState } from "react";
import { ReactSketchCanvas, type CanvasPath, type ReactSketchCanvasRef } from "react-sketch-canvas";
import { Fenster } from "../shell/Fenster";
import { battlemapApi, verbindeBattlemapLive, type Battlemap, type Pfad } from "./api";
import { distanz, hexEcken, hexNachPixel, pixelNachHex, reichweite, yFelder } from "./hex";
import { kampfApi, type Kampf, type Teilnehmer } from "../kampf/api";
import { bogenApi } from "../traits/bogenApi";
import "../players/portrait.css";
import "../zeichnungen/whiteboard.css";
import "./battlemap.css";

const FARBEN = ["#1a1a1a", "#c0392b", "#e67e22", "#d4a017", "#1e8449", "#2471a3", "#7d3c98", "#f4f4f4"];
const STIFTE = [3, 6, 12];
const Q_MIN = -14;
const Q_MAX = 14;

export function BattlemapPopup({
  offen,
  karte,
  campaignId,
  darfZeichnen,
  istGm,
  eigenePersonId,
  onSchliessen,
  onEinstellungenOeffnen,
  onKarte,
}: {
  offen: boolean;
  karte: Battlemap | null;
  campaignId: string;
  darfZeichnen: boolean;
  istGm: boolean;
  eigenePersonId?: string | null;
  onSchliessen: () => void;
  onEinstellungenOeffnen?: () => void;
  onKarte: (k: Battlemap) => void;
}) {
  const leinwand = useRef<ReactSketchCanvasRef>(null);
  const leitung = useRef<ReturnType<typeof verbindeBattlemapLive> | null>(null);
  const sperreBis = useRef(0);
  const buehne = useRef<HTMLDivElement>(null);
  const [farbe, setFarbe] = useState(FARBEN[0]);
  const stift = STIFTE[1];
  const [radierer, setRadierer] = useState(false);
  const [verbunden, setVerbunden] = useState(false);
  const [modus, setModus] = useState<"zeichnen" | "schieben" | "grid">("schieben");
  const [spawnArt, setSpawnArt] = useState<"pc" | "npc" | null>(null);
  const [kampf, setKampf] = useState<Kampf | null>(null);
  const [ziehend, setZiehend] = useState<string | null>(null);
  const [hoverHex, setHoverHex] = useState<{ q: number; r: number } | null>(null);
  const [gruen, setGruen] = useState<Set<string>>(new Set());
  const originZieh = useRef<{ sx: number; sy: number; ox: number; oy: number } | null>(null);
  const [ziehOrigin, setZiehOrigin] = useState<{ x: number; y: number } | null>(null);

  const size = karte?.hexGroesse || 48;
  const ox = ziehOrigin?.x ?? karte?.originX ?? 0;
  const oy = ziehOrigin?.y ?? karte?.originY ?? 0;

  useEffect(() => {
    leinwand.current?.eraseMode(radierer);
  }, [radierer, offen]);

  function standUebernehmen(pfade: Pfad[]) {
    sperreBis.current = Date.now() + 150;
    leinwand.current?.resetCanvas();
    if (pfade.length) leinwand.current?.loadPaths(pfade as unknown as CanvasPath[]);
  }

  useEffect(() => {
    if (!offen || !karte) return;
    let tot = false;
    battlemapApi.holen(campaignId, karte.id).then((frisch) => {
      if (!tot) {
        onKarte(frisch);
        standUebernehmen(frisch.pfade);
      }
    });
    kampfApi.laden(campaignId).then(async (k) => {
      if (tot) return;
      if (istGm && k && !k.battlemapId) {
        try {
          k = await kampfApi.karte(campaignId, karte.id);
        } catch {
          /* kein Kampf oder Karte schon anders gebunden */
        }
      }
      if (!tot) setKampf(k);
    });
    leitung.current = verbindeBattlemapLive(
      campaignId,
      karte.id,
      (n) => {
        if (n.typ === "pfade") standUebernehmen(n.daten.pfade);
        if (n.typ === "karte") onKarte(n.daten);
        if (n.typ === "tokens") {
          setKampf((alt) => ({
            id: alt?.id ?? "",
            runde: alt?.runde ?? 1,
            verbrauchteBeschwoerungen: alt?.verbrauchteBeschwoerungen,
            amZug: n.daten.amZug,
            battlemapId: n.daten.battlemapId,
            teilnehmer: n.daten.teilnehmer.map((t) => ({
              initiative: 0,
              kampfart: "NAHKAMPF" as const,
              notiz: "",
              erledigt: false,
              personId: null,
              personType: null,
              begleiterId: null,
              ...(alt?.teilnehmer.find((x) => x.id === t.id) ?? {}),
              ...t,
            })) as Teilnehmer[],
          }));
        }
      },
      setVerbunden,
    );
    return () => {
      tot = true;
      leitung.current?.trennen();
      leitung.current = null;
    };
  }, [offen, karte?.id, campaignId]);

  if (!karte) return null;
  const karteId = karte.id;

  const tokens = (kampf?.battlemapId === karte.id ? kampf.teilnehmer : []).filter((t) => !t.zusatzzug);
  const amZug = kampf?.amZug;

  function hexUnter(ev: React.PointerEvent) {
    const box = buehne.current?.getBoundingClientRect();
    if (!box) return null;
    return pixelNachHex(ev.clientX - box.left, ev.clientY - box.top, size, ox, oy);
  }

  async function spawnKlick(q: number, r: number) {
    if (!spawnArt || !istGm) return;
    const body = spawnArt === "pc" ? { spawnPcQ: q, spawnPcR: r } : { spawnNpcQ: q, spawnNpcR: r };
    const neu = await battlemapApi.aktualisieren(campaignId, karteId, body);
    onKarte(neu);
    setSpawnArt(null);
  }

  async function groesse(wert: number) {
    const neu = await battlemapApi.aktualisieren(campaignId, karteId, { hexGroesse: wert });
    onKarte(neu);
  }

  function gehoertMir(t: Teilnehmer) {
    if (istGm) return true;
    if (!eigenePersonId) return false;
    if (t.personId === eigenePersonId) return true;
    return t.besitzerId === eigenePersonId;
  }

  function istDran(t: Teilnehmer) {
    if (!amZug) return false;
    if (t.id === amZug) return true;
    const aktueller = tokens.find((x) => x.id === amZug);
    return Boolean(t.personId && aktueller?.personId === t.personId);
  }

  async function anheben(t: Teilnehmer) {
    if (modus !== "schieben") return;
    if (!istGm && (!gehoertMir(t) || !istDran(t))) return;
    if (t.hexQ == null || t.hexR == null) return;
    setZiehend(t.id);
    let rwe = 3;
    if (t.personId) {
      try {
        const bogen = await bogenApi.laden(campaignId, t.personId);
        const sport = bogen.werte.find((w) => w.name === "Sportlichkeit")?.rating ?? 0;
        const fliegenWert =
          bogen.werte.find((w) => w.name === "Fliegen")?.rating ??
          bogen.hotZusatz?.find((z) => z.name === "Fliegen")?.rating ??
          0;
        const drohne = Boolean(t.istDrohne || t.istFahrzeug);
        rwe = reichweite(sport, drohne ? fliegenWert : null);
      } catch {
        rwe = 3;
      }
    }
    const felder = new Set<string>();
    for (let q = Q_MIN; q <= Q_MAX; q++) {
      for (let r = Q_MIN; r <= Q_MAX; r++) {
        if (distanz(t.hexQ, t.hexR, q, r) <= rwe) felder.add(`${q},${r}`);
      }
    }
    setGruen(felder);
  }

  async function absetzen(ev: React.PointerEvent) {
    if (!ziehend) return;
    const hex = hexUnter(ev);
    setZiehend(null);
    setGruen(new Set());
    setHoverHex(null);
    if (!hex) return;
    try {
      const k = await kampfApi.position(campaignId, ziehend, hex.q, hex.r);
      setKampf(k);
    } catch {
      /* belegt */
    }
  }

  const hexListe: { q: number; r: number }[] = [];
  for (let q = Q_MIN; q <= Q_MAX; q++) {
    for (let r = Q_MIN; r <= Q_MAX; r++) hexListe.push({ q, r });
  }

  return (
    <Fenster
      offen={offen}
      titel={karte.name}
      kennung={`battlemap-${karte.id}`}
      breit
      ton="var(--bereich-battlemap)"
      unterzeile={verbunden ? "Live" : "Verbindung…"}
      onSchliessen={onSchliessen}
    >
      <div className="bm-leiste">
        <button type="button" data-aktiv={modus === "schieben"} onClick={() => setModus("schieben")}>
          Schieben
        </button>
        <button
          type="button"
          data-aktiv={modus === "zeichnen"}
          onClick={() => setModus("zeichnen")}
          disabled={!darfZeichnen}
        >
          Zeichnen
        </button>
        {istGm && (
          <>
            <button
              type="button"
              data-aktiv={modus === "grid"}
              onClick={() => {
                setModus("grid");
                setSpawnArt(null);
              }}
            >
              Grid schieben
            </button>
            <label>
              Größe
              <input
                type="range"
                min={24}
                max={96}
                value={size}
                onChange={(e) => groesse(Number(e.target.value))}
              />
            </label>
            <button type="button" data-aktiv={spawnArt === "pc"} onClick={() => setSpawnArt(spawnArt === "pc" ? null : "pc")}>
              PC-Spawn
            </button>
            <button type="button" data-aktiv={spawnArt === "npc"} onClick={() => setSpawnArt(spawnArt === "npc" ? null : "npc")}>
              NPC-Spawn
            </button>
            {onEinstellungenOeffnen && (
              <button type="button" className="port-mini" onClick={onEinstellungenOeffnen}>
                Einstellungen
              </button>
            )}
          </>
        )}
      </div>

      {modus === "zeichnen" && darfZeichnen && (
        <div className="port-werkzeug">
          <div className="port-farben">
            {FARBEN.map((f) => (
              <button
                key={f}
                type="button"
                className="port-farbe"
                style={{ background: f }}
                onClick={() => {
                  setFarbe(f);
                  setRadierer(false);
                }}
              />
            ))}
          </div>
          <button type="button" className="port-mini" onClick={() => setRadierer((r) => !r)}>
            {radierer ? "Radierer" : "Stift"}
          </button>
        </div>
      )}

      <div
        ref={buehne}
        className="bm-buehne"
        data-modus={modus}
        onPointerDown={(e) => {
          if (modus !== "grid" || !istGm) return;
          originZieh.current = { sx: e.clientX, sy: e.clientY, ox, oy };
          e.currentTarget.setPointerCapture(e.pointerId);
        }}
        onPointerMove={(e) => {
          const z = originZieh.current;
          if (z) {
            setZiehOrigin({ x: z.ox + e.clientX - z.sx, y: z.oy + e.clientY - z.sy });
            return;
          }
          if (ziehend || spawnArt) setHoverHex(hexUnter(e));
        }}
        onPointerUp={(e) => {
          const z = originZieh.current;
          if (z) {
            originZieh.current = null;
            const nx = z.ox + e.clientX - z.sx;
            const ny = z.oy + e.clientY - z.sy;
            setZiehOrigin({ x: nx, y: ny });
            void battlemapApi.aktualisieren(campaignId, karteId, { originX: nx, originY: ny }).then((neu) => {
              onKarte(neu);
              setZiehOrigin(null);
            }).catch(() => setZiehOrigin(null));
            return;
          }
          void absetzen(e);
        }}
        onClick={(e) => {
          if (!spawnArt || modus === "grid") return;
          const hex = hexUnter(e as unknown as React.PointerEvent);
          if (hex) void spawnKlick(hex.q, hex.r);
        }}
      >
        <div className="bm-skizze" style={{ pointerEvents: modus === "zeichnen" && darfZeichnen ? "auto" : "none" }}>
          {offen && (
            <ReactSketchCanvas
              ref={leinwand}
              width="100%"
              height="100%"
              strokeColor={farbe}
              strokeWidth={stift}
              eraserWidth={Math.max(stift * 2, 12)}
              canvasColor="transparent"
              backgroundImage={karte.bildUrl || ""}
              preserveBackgroundImageAspectRatio="xMidYMid meet"
              touchAction="none"
              readOnly={!darfZeichnen || modus !== "zeichnen"}
              onChange={(p) => {
                if (Date.now() < sperreBis.current) return;
                leitung.current?.senden(p as unknown as Pfad[]);
              }}
              style={{ border: "none" }}
            />
          )}
        </div>
        <svg className="bm-grid" width="100%" height="100%">
          {hexListe.map(({ q, r }) => {
            const { x, y } = hexNachPixel(q, r, size, ox, oy);
            const key = `${q},${r}`;
            const istGruen = ziehend && gruen.has(key);
            const spawnPc = karte.spawnPcQ === q && karte.spawnPcR === r;
            const spawnNpc = karte.spawnNpcQ === q && karte.spawnNpcR === r;
            const hover = hoverHex && hoverHex.q === q && hoverHex.r === r;
            return (
              <polygon
                key={key}
                points={hexEcken(x, y, size * 0.95)}
                className="bm-hex"
                data-gruen={istGruen || undefined}
                data-pc={spawnPc || undefined}
                data-npc={spawnNpc || undefined}
                data-hover={hover || undefined}
              />
            );
          })}
          {tokens.map((t) => {
            if (t.zugStartQ == null || t.zugStartR == null || t.id !== amZug) return null;
            const { x, y } = hexNachPixel(t.zugStartQ, t.zugStartR, size, ox, oy);
            return <polygon key={`g-${t.id}`} points={hexEcken(x, y, size * 0.95)} className="bm-hex-grau" />;
          })}
        </svg>
        {tokens.map((t) => {
          if (t.hexQ == null || t.hexR == null) return null;
          const anker = ziehend === t.id && hoverHex ? hoverHex : { q: t.hexQ, r: t.hexR };
          const { x, y } = hexNachPixel(anker.q, anker.r, size, ox, oy);
          const besitzer = t.besitzerId ? tokens.find((x) => x.personId === t.besitzerId) : undefined;
          const gehoertPc =
            (t.personType === "PC" && !t.istDrohne && !t.istCritter && !t.istFahrzeug) ||
            besitzer?.personType === "PC" ||
            t.besitzerId === eigenePersonId;
          const rand = istDran(t) ? "gold" : gehoertPc ? "blau" : "magenta";
          const felder = yFelder(anker.q, anker.r, Boolean(t.istGross), t.hexDrehung ?? 0);
          const { x: x2, y: y2 } = hexNachPixel(felder[felder.length - 1][0], felder[felder.length - 1][1], size, ox, oy);
          const cx = t.istGross ? (x + x2) / 2 : x;
          const cy = t.istGross ? (y + y2) / 2 : y;
          return (
            <button
              key={t.id}
              type="button"
              className="bm-token"
              data-rand={rand}
              data-gross={t.istGross || undefined}
              style={{
                left: cx,
                top: cy,
                width: t.istGross ? size * 2.2 : size * 1.7,
                height: t.istGross ? size * 2.2 : size * 1.7,
              }}
              onPointerDown={(e) => {
                e.stopPropagation();
                void anheben(t);
              }}
              title={t.name}
            >
              {t.bildUrl ? <img src={t.bildUrl} alt="" /> : <span>{t.name.slice(0, 2)}</span>}
            </button>
          );
        })}
      </div>
    </Fenster>
  );
}
