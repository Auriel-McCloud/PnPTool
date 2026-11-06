import { useEffect, useRef, useState } from "react";
import { ReactSketchCanvas, type CanvasPath, type ReactSketchCanvasRef } from "react-sketch-canvas";
import { Fenster } from "../shell/Fenster";
import { battlemapApi, verbindeBattlemapLive, type Battlemap, type Pfad } from "./api";
import { hexEcken, hexNachPixel, hexRasterRechteck, pixelNachHex, reichweite, yFelder } from "./hex";
import { kampfApi, type Kampf, type Teilnehmer } from "../kampf/api";
import { einstellungenApi } from "../campaigns/einstellungen";
import { partyApi } from "../party/api";
import { bogenApi } from "../traits/bogenApi";
import "../players/portrait.css";
import "../zeichnungen/whiteboard.css";
import "./battlemap.css";

const FARBEN = ["#1a1a1a", "#c0392b", "#e67e22", "#d4a017", "#1e8449", "#2471a3", "#7d3c98", "#f4f4f4"];
const STIFTE = [3, 6, 12];
const BLICK_WINKEL = [0, -60, -120, 180, 120, 60];

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
  const [partei, setPartei] = useState<Set<string>>(new Set());
  const [flaeche, setFlaeche] = useState({ w: 800, h: 420 });
  const [fog, setFog] = useState(false);
  const [chipId, setChipId] = useState<string | null>(null);
  const tipp = useRef<{ id: string; x: number; y: number; angehoben: boolean } | null>(null);

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
          setFog(Boolean(n.daten.fog));
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

  useEffect(() => {
    if (!offen) return;
    partyApi
      .liste(campaignId)
      .then((alle) => {
        const aktiv = alle.find((p) => p.aktiv);
        setPartei(new Set((aktiv?.mitglieder ?? []).map((m) => m.id)));
      })
      .catch(() => setPartei(new Set()));
    einstellungenApi.lesen(campaignId).then((e) => setFog(Boolean(e.fogOfWar))).catch(() => undefined);
  }, [offen, campaignId]);

  useEffect(() => {
    if (!offen) return;
    const el = buehne.current;
    if (!el) return;
    const messen = () => setFlaeche({ w: el.clientWidth, h: el.clientHeight });
    messen();
    const ro = new ResizeObserver(messen);
    ro.observe(el);
    return () => ro.disconnect();
  }, [offen, karte?.id]);

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
    for (let dq = -rwe; dq <= rwe; dq++) {
      for (let dr = Math.max(-rwe, -dq - rwe); dr <= Math.min(rwe, -dq + rwe); dr++) {
        felder.add(`${t.hexQ + dq},${t.hexR + dr}`);
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

  async function umschauen(t: Teilnehmer, richtung: number) {
    try {
      setKampf(await kampfApi.blick(campaignId, t.id, richtung));
    } catch {
      /* nicht am Zug */
    }
  }

  async function verstecken(t: Teilnehmer) {
    try {
      setKampf(await kampfApi.versteckt(campaignId, t.id, !t.versteckt));
    } catch {
      /* nicht der eigene Token */
    }
  }

  const hexListe = hexRasterRechteck(flaeche.w, flaeche.h, size, ox, oy);

  function inPartei(t: Teilnehmer) {
    if (t.personId && partei.has(t.personId)) return true;
    if (t.besitzerId && partei.has(t.besitzerId)) return true;
    if (partei.size === 0) {
      if (t.personType === "PC" && !t.istDrohne && !t.istCritter && !t.istFahrzeug) return true;
      const besitzer = t.besitzerId ? tokens.find((x) => x.personId === t.besitzerId) : undefined;
      return besitzer?.personType === "PC" || t.besitzerId === eigenePersonId;
    }
    return false;
  }

  const belegung = new Map<string, "blau" | "magenta" | "gold">();
  for (const t of tokens) {
    if (t.hexQ == null || t.hexR == null) continue;
    const anker = ziehend === t.id && hoverHex ? hoverHex : { q: t.hexQ, r: t.hexR };
    const farbe: "blau" | "magenta" | "gold" = istDran(t) ? "gold" : inPartei(t) ? "blau" : "magenta";
    for (const [q, r] of yFelder(anker.q, anker.r, Boolean(t.istGross), t.hexDrehung ?? 0)) {
      const key = `${q},${r}`;
      if (farbe === "gold" || !belegung.has(key)) belegung.set(key, farbe);
    }
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
            const farbe = belegung.get(key);
            return (
              <polygon
                key={key}
                points={hexEcken(x, y, size * 0.95)}
                className="bm-hex"
                data-gruen={istGruen || undefined}
                data-gold={farbe === "gold" || undefined}
                data-pc={farbe === "blau" || (!farbe && spawnPc) || undefined}
                data-npc={farbe === "magenta" || (!farbe && spawnNpc) || undefined}
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
          const rand = istDran(t) ? "gold" : inPartei(t) ? "blau" : "magenta";
          const felder = yFelder(anker.q, anker.r, Boolean(t.istGross), t.hexDrehung ?? 0);
          const { x: x2, y: y2 } = hexNachPixel(felder[felder.length - 1][0], felder[felder.length - 1][1], size, ox, oy);
          const cx = t.istGross ? (x + x2) / 2 : x;
          const cy = t.istGross ? (y + y2) / 2 : y;
          const winkel = BLICK_WINKEL[t.blickrichtung ?? 0] ?? 0;
          const chip = chipId === t.id;
          return (
            <span key={t.id}>
              {fog && (
                <span
                  className="bm-blick"
                  style={{
                    left: cx,
                    top: cy,
                    transform: `translate(-50%, -50%) rotate(${winkel}deg) translateX(${size * 0.85}px)`,
                  }}
                />
              )}
              <button
                type="button"
                className="bm-token"
                data-rand={rand}
                data-gross={t.istGross || undefined}
                data-veraltet={t.veraltet || undefined}
                data-versteckt={t.versteckt || undefined}
                style={{
                  left: cx,
                  top: cy,
                  width: t.istGross ? size * 2.2 : size * 1.7,
                  height: t.istGross ? size * 2.2 : size * 1.7,
                }}
                onPointerDown={(e) => {
                  e.stopPropagation();
                  if (t.veraltet) return;
                  tipp.current = { id: t.id, x: e.clientX, y: e.clientY, angehoben: false };
                  e.currentTarget.setPointerCapture(e.pointerId);
                }}
                onPointerMove={(e) => {
                  const tip = tipp.current;
                  if (!tip || tip.id !== t.id || tip.angehoben || t.veraltet) return;
                  if (Math.hypot(e.clientX - tip.x, e.clientY - tip.y) > 8) {
                    tip.angehoben = true;
                    void anheben(t);
                  }
                }}
                onPointerUp={(e) => {
                  e.stopPropagation();
                  const tip = tipp.current;
                  tipp.current = null;
                  if (!tip || tip.id !== t.id) return;
                  if (!tip.angehoben) {
                    setChipId(t.id);
                    return;
                  }
                  void absetzen(e);
                }}
              >
                {t.bildUrl ? <img src={t.bildUrl} alt="" /> : <span>{t.name.slice(0, 2)}</span>}
              </button>
              {chip && (
                <div className="bm-name" style={{ left: cx, top: cy - size }}>
                  <strong>{t.name}</strong>
                  {fog && (istGm || (gehoertMir(t) && istDran(t))) && (
                    <div className="bm-richtungen">
                      {BLICK_WINKEL.map((_, i) => (
                        <button
                          key={i}
                          type="button"
                          data-aktiv={t.blickrichtung === i}
                          onClick={() => void umschauen(t, i)}
                        >
                          {i + 1}
                        </button>
                      ))}
                    </div>
                  )}
                  {fog && (istGm || gehoertMir(t)) && (
                    <button type="button" onClick={() => void verstecken(t)}>
                      {t.versteckt ? "Sichtbar" : "Verstecken"}
                    </button>
                  )}
                  <button type="button" onClick={() => setChipId(null)}>
                    zu
                  </button>
                </div>
              )}
            </span>
          );
        })}
      </div>
    </Fenster>
  );
}
