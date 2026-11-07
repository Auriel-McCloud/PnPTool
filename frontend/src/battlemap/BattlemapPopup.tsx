import { useEffect, useRef, useState } from "react";
import { ReactSketchCanvas, type CanvasPath, type ReactSketchCanvasRef } from "react-sketch-canvas";
import { Fenster } from "../shell/Fenster";
import { Bestaetigung } from "../shell/Bestaetigung";
import { battlemapApi, verbindeBattlemapLive, type Battlemap, type Pfad } from "./api";
import { hexEcken, hexNachPixel, hexRasterRechteck, NACHBARN, naechsteEcke, pixelNachHex, reichweite, yFelder } from "./hex";
import { kampfApi, type Kampf, type Teilnehmer } from "../kampf/api";
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
  const [modus, setModus] = useState<"zeichnen" | "schieben" | "grid" | "wand">("schieben");
  const [spawnArt, setSpawnArt] = useState<"pc" | "npc" | null>(null);
  const [kampf, setKampf] = useState<Kampf | null>(null);
  const [ziehend, setZiehend] = useState<string | null>(null);
  const [hoverHex, setHoverHex] = useState<{ q: number; r: number } | null>(null);
  const [gruen, setGruen] = useState<Set<string>>(new Set());
  const originZieh = useRef<{ sx: number; sy: number; ox: number; oy: number } | null>(null);
  const [ziehOrigin, setZiehOrigin] = useState<{ x: number; y: number } | null>(null);
  const [partei, setPartei] = useState<Set<string>>(new Set());
  const [flaeche, setFlaeche] = useState({ w: 800, h: 420 });
  const [wahlId, setWahlId] = useState<string | null>(null);
  const [sichtDa, setSichtDa] = useState(istGm);
  const [linien, setLinien] = useState<{ ax: number; ay: number; bx: number; by: number }[]>([]);
  const tipp = useRef<{ id: string; x: number; y: number; angehoben: boolean } | null>(null);
  const wahlSperre = useRef(0);
  const wandVon = useRef<{ ax: number; ay: number; px: number; py: number } | null>(null);
  const [wandZiel, setWandZiel] = useState<{ ax: number; ay: number; px: number; py: number } | null>(null);
  const [wandWeg, setWandWeg] = useState<number | null>(null);

  const size = karte?.hexGroesse || 48;
  const ox = ziehOrigin?.x ?? karte?.originX ?? 0;
  const oy = ziehOrigin?.y ?? karte?.originY ?? 0;

  useEffect(() => {
    setLinien(karte?.waende ?? []);
  }, [karte?.id, karte?.waende]);

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
    kampfApi.fuerKarte(campaignId).then(async (k) => {
      if (tot) return;
      if (istGm && k && !k.battlemapId) {
        try {
          await kampfApi.karte(campaignId, karte.id);
          k = await kampfApi.fuerKarte(campaignId);
        } catch {
          /* kein Kampf oder Karte schon anders gebunden */
        }
      }
      if (!tot) {
        setKampf(k);
        // Bugfix 06.11.2026: sichtDa wurde bisher NUR vom WS-"tokens"-Push
        // gesetzt. Die REST-Antwort hier ist für Spieler bereits serverseitig
        // gefiltert (ansicht()) — ohne dieses Set blieb die Karte bis zum
        // nächsten zufälligen Kartenzug leer/leer-ähnlich, wenn der
        // WS-Connect minimal später kam als dieser REST-Call.
        if (k) setSichtDa(true);
      }
    });
    leitung.current = verbindeBattlemapLive(
      campaignId,
      karte.id,
      (n) => {
        if (n.typ === "pfade") standUebernehmen(n.daten.pfade);
        if (n.typ === "karte") {
          onKarte(n.daten);
          setLinien(n.daten.waende ?? []);
        }
        if (n.typ === "tokens") {
          setSichtDa(true);
          if (n.daten.waende) setLinien(n.daten.waende);
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

  const tokens = (sichtDa && kampf?.battlemapId === karte.id ? kampf.teilnehmer : []).filter((t) => !t.zusatzzug);
  const amZug = kampf?.amZug;

  function hexUnter(ev: React.PointerEvent) {
    const box = buehne.current?.getBoundingClientRect();
    if (!box) return null;
    return pixelNachHex(ev.clientX - box.left, ev.clientY - box.top, size, ox, oy);
  }

  function eckeUnter(ev: React.PointerEvent) {
    const box = buehne.current?.getBoundingClientRect();
    if (!box) return null;
    return naechsteEcke(ev.clientX - box.left, ev.clientY - box.top, size, ox, oy);
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

  function istEigen(t: Teilnehmer) {
    if (!eigenePersonId) return false;
    return t.personId === eigenePersonId || t.besitzerId === eigenePersonId;
  }

  function istDran(t: Teilnehmer) {
    if (t.hotKoerper) return false;
    if (t.hotGesteuert) {
      const rigger = tokens.find((x) => x.hotKoerper && x.personId === t.besitzerId);
      return Boolean(rigger && rigger.id === amZug);
    }
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

  const schau = tokens.find((t) => t.id === wahlId);
  const schauFelder = new Set<string>();
  const wahlFelder = new Set<string>();
  if (schau && schau.hexQ != null && schau.hexR != null) {
    for (const [q, r] of yFelder(schau.hexQ, schau.hexR, Boolean(schau.istGross), schau.hexDrehung ?? 0)) {
      wahlFelder.add(`${q},${r}`);
    }
    if (istGm || (istEigen(schau) && istDran(schau))) {
      for (const [dq, dr] of NACHBARN) schauFelder.add(`${schau.hexQ + dq},${schau.hexR + dr}`);
    }
  }

  return (
    <>
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
            <button
              type="button"
              data-aktiv={modus === "wand"}
              onClick={() => {
                setModus("wand");
                setSpawnArt(null);
              }}
            >
              Wand
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
        {schau && (
          <span className="bm-wahl">
            <strong>{schau.name}</strong>
            {(istGm || istEigen(schau)) && (
              <button type="button" onClick={() => void verstecken(schau)}>
                {schau.versteckt ? "Sichtbar" : "Verstecken"}
              </button>
            )}
          </span>
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
          if (modus === "wand" && istGm) {
            if ((e.target as HTMLElement).closest(".bm-wand")) return;
            const ecke = eckeUnter(e);
            if (!ecke) return;
            wandVon.current = ecke;
            setWandZiel(ecke);
            e.currentTarget.setPointerCapture(e.pointerId);
            return;
          }
          if (modus !== "grid" || !istGm) return;
          originZieh.current = { sx: e.clientX, sy: e.clientY, ox, oy };
          e.currentTarget.setPointerCapture(e.pointerId);
        }}
        onPointerMove={(e) => {
          if (wandVon.current) {
            setWandZiel(eckeUnter(e));
            return;
          }
          const z = originZieh.current;
          if (z) {
            setZiehOrigin({ x: z.ox + e.clientX - z.sx, y: z.oy + e.clientY - z.sy });
            return;
          }
          if (ziehend || spawnArt) setHoverHex(hexUnter(e));
        }}
        onPointerUp={(e) => {
          if (wandVon.current) {
            const start = wandVon.current;
            wandVon.current = null;
            const ziel = eckeUnter(e);
            setWandZiel(null);
            if (ziel && (Math.abs(ziel.ax - start.ax) > 0.05 || Math.abs(ziel.ay - start.ay) > 0.05)) {
              const liste = [...linien, { ax: start.ax, ay: start.ay, bx: ziel.ax, by: ziel.ay }];
              setLinien(liste);
              void battlemapApi.aktualisieren(campaignId, karteId, { waende: liste }).then(onKarte).catch(() => undefined);
            }
            return;
          }
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
          const ziel = e.target as HTMLElement;
          if (Date.now() < wahlSperre.current) return;
          if (ziel.closest(".bm-token, .bm-name, .bm-aktion, .bm-wand")) return;
          const gewaehlt = tokens.find((t) => t.id === wahlId);
          if (gewaehlt && gewaehlt.hexQ != null && gewaehlt.hexR != null && (istGm || (istEigen(gewaehlt) && istDran(gewaehlt)))) {
            const hex = hexUnter(e as unknown as React.PointerEvent);
            const richtung = hex
              ? NACHBARN.findIndex(([dq, dr]) => gewaehlt.hexQ! + dq === hex.q && gewaehlt.hexR! + dr === hex.r)
              : -1;
            if (richtung >= 0) {
              void umschauen(gewaehlt, richtung);
              setWahlId(null);
              return;
            }
          }
          if (wahlId) {
            setWahlId(null);
            return;
          }
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
        <svg className="bm-bild" width="100%" height="100%">
          {karte.bildUrl && karte.bildBreite && karte.bildHoehe && (
            <image
              href={karte.bildUrl}
              x={ox}
              y={oy}
              width={karte.bildBreite}
              height={karte.bildHoehe}
              preserveAspectRatio="none"
            />
          )}
        </svg>
        <svg className="bm-grid" width="100%" height="100%">
          {hexListe.map(({ q, r }) => {
            const { x, y } = hexNachPixel(q, r, size, ox, oy);
            const key = `${q},${r}`;
            const istGruen = ziehend && gruen.has(key);
            const spawnPc = istGm && karte.spawnPcQ === q && karte.spawnPcR === r;
            const spawnNpc = istGm && karte.spawnNpcQ === q && karte.spawnNpcR === r;
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
                data-schau={schauFelder.has(key) || undefined}
                data-wahl={wahlFelder.has(key) || undefined}
              />
            );
          })}
          {tokens.map((t) => {
            if (t.zugStartQ == null || t.zugStartR == null || t.id !== amZug) return null;
            const { x, y } = hexNachPixel(t.zugStartQ, t.zugStartR, size, ox, oy);
            return <polygon key={`g-${t.id}`} points={hexEcken(x, y, size * 0.95)} className="bm-hex-grau" />;
          })}
        </svg>
        <svg className="bm-waende">
          {linien.map((w, i) => (
            <line
              key={`${w.ax}-${w.ay}-${w.bx}-${w.by}-${i}`}
              className="bm-wand"
              x1={w.ax * size + ox}
              y1={w.ay * size + oy}
              x2={w.bx * size + ox}
              y2={w.by * size + oy}
              onClick={(e) => {
                e.stopPropagation();
                if (istGm && modus === "wand") setWandWeg(i);
              }}
            />
          ))}
          {wandVon.current && wandZiel && (
            <line
              className="bm-wand-vorschau"
              x1={wandVon.current.px}
              y1={wandVon.current.py}
              x2={wandZiel.px}
              y2={wandZiel.py}
            />
          )}
        </svg>
        {tokens.map((t) => {
          if (t.hexQ == null || t.hexR == null) return null;
          const anker = ziehend === t.id && hoverHex ? hoverHex : { q: t.hexQ, r: t.hexR };
          const { x, y } = hexNachPixel(anker.q, anker.r, size, ox, oy);
          const rand = t.veraltet ? undefined : istDran(t) ? "gold" : inPartei(t) ? "blau" : "magenta";
          const felder = yFelder(anker.q, anker.r, Boolean(t.istGross), t.hexDrehung ?? 0);
          const { x: x2, y: y2 } = hexNachPixel(felder[felder.length - 1][0], felder[felder.length - 1][1], size, ox, oy);
          const cx = t.istGross ? (x + x2) / 2 : x;
          const cy = t.istGross ? (y + y2) / 2 : y;
          const winkel = BLICK_WINKEL[t.blickrichtung ?? 0] ?? 0;
          return (
            <span key={t.id}>
              {(
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
                data-wahl={wahlId === t.id || undefined}
                data-gross={t.istGross || undefined}
                data-veraltet={t.veraltet || undefined}
                data-erinnerung={t.veraltet || undefined}
                data-versteckt={t.versteckt || undefined}
                style={{
                  left: cx,
                  top: cy,
                  width: t.istGross ? size * 2.2 : size * 1.7,
                  height: t.istGross ? size * 2.2 : size * 1.7,
                }}
                draggable={false}
                onDragStart={(e) => e.preventDefault()}
                onPointerDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (t.veraltet) {
                    wahlSperre.current = Date.now() + 500;
                    setWahlId(t.id);
                    return;
                  }
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
                    wahlSperre.current = Date.now() + 500;
                    setWahlId(t.id);
                    return;
                  }
                  void absetzen(e);
                }}
              >
                {t.bildUrl ? <img src={t.bildUrl} alt="" draggable={false} /> : <span>{t.name.slice(0, 2)}</span>}
              </button>
              {t.veraltet && (
                <i className="bm-mem" style={{ left: cx, top: cy }} title="Erinnerung">
                  ALT
                </i>
              )}
            </span>
          );
        })}
      </div>
    </Fenster>
    {wandWeg != null && (
      <Bestaetigung
        titel="Wand weg?"
        text="Bist du sicher? Die Linie blockiert dann keine Sicht mehr."
        jaText="Weg damit"
        onNein={() => setWandWeg(null)}
        onJa={() => {
          const liste = linien.filter((_, i) => i !== wandWeg);
          setWandWeg(null);
          setLinien(liste);
          void battlemapApi.aktualisieren(campaignId, karteId, { waende: liste }).then(onKarte).catch(() => undefined);
        }}
      />
    )}
    </>
  );
}
