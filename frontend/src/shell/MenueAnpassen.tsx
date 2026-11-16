import { useEffect, useMemo, useRef, useState } from "react";
import { Fenster } from "./Fenster";
import type { Bereich } from "./CommlinkShell";
import type { Geraet, MenueLayouts, MenueSlot } from "./menue";
import { LEER_SLOT } from "./menue";

function mitAllen(alle: Bereich[], slot: MenueSlot): { id: string; name: string; sichtbar: boolean }[] {
  const byId = new Map(alle.map((b) => [b.id, b]));
  const gesehen = new Set<string>();
  const zeilen: { id: string; name: string; sichtbar: boolean }[] = [];
  const hidden = new Set(slot.ausgeblendet);
  for (const id of slot.ordnung) {
    const b = byId.get(id);
    if (!b || gesehen.has(id)) continue;
    gesehen.add(id);
    zeilen.push({ id, name: b.name, sichtbar: !hidden.has(id) });
  }
  for (const b of alle) {
    if (gesehen.has(b.id)) continue;
    zeilen.push({ id: b.id, name: b.name, sichtbar: !hidden.has(b.id) });
  }
  return zeilen;
}

export function MenueAnpassen({
  offen,
  onSchliessen,
  bereiche,
  layouts,
  geraet,
  onSpeichern,
}: {
  offen: boolean;
  onSchliessen: () => void;
  bereiche: Bereich[];
  layouts: MenueLayouts;
  geraet: Geraet;
  onSpeichern: (layouts: MenueLayouts) => Promise<void>;
}) {
  const startSlot: "pc" | "tablet" = geraet === "tablet" ? "tablet" : "pc";
  const [slotName, setSlotName] = useState<"pc" | "tablet">(startSlot);
  const [lokal, setLokal] = useState<MenueLayouts>(layouts);

  useEffect(() => {
    if (!offen) return;
    setLokal(layouts);
    setSlotName(geraet === "tablet" ? "tablet" : "pc");
    // Nur beim Öffnen snapshotten — sonst springt der Slot nach jedem Speichern zurück.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offen]);

  const zeilen = useMemo(
    () => mitAllen(bereiche, lokal[slotName] ?? LEER_SLOT),
    [bereiche, lokal, slotName],
  );

  async function schreibe(naechstes: MenueLayouts) {
    setLokal(naechstes);
    await onSpeichern(naechstes);
  }

  function slotAktualisieren(zeilenNeu: { id: string; name: string; sichtbar: boolean }[]) {
    const slot: MenueSlot = {
      ordnung: zeilenNeu.map((z) => z.id),
      ausgeblendet: zeilenNeu.filter((z) => !z.sichtbar).map((z) => z.id),
    };
    void schreibe({ ...lokal, [slotName]: slot });
  }

  // Ziehen am Griff (Mark, 16.11.2026: „so viele Menüpunkte, mit rauf und
  // runter sehr mühsam“). Pointer statt HTML5-Drag, sonst geht es am Tablet
  // nicht. Während des Ziehens nur lokale Vorschau, gespeichert wird beim Loslassen.
  const liste = useRef<HTMLOListElement>(null);
  const [zug, setZug] = useState<{ id: string; von: number; nach: number; dy: number; hoehe: number } | null>(null);
  const zugStart = useRef<{ y: number; pointer: number; hoehe: number } | null>(null);
  const scrollTakt = useRef<number | null>(null);
  const letzteY = useRef(0);

  const anzeige = useMemo(() => {
    if (!zug) return zeilen;
    const neu = zeilen.slice();
    const [z] = neu.splice(zug.von, 1);
    neu.splice(zug.nach, 0, z);
    return neu;
  }, [zeilen, zug]);

  function scrollBehaelter(): HTMLElement | null {
    let el = liste.current?.parentElement ?? null;
    while (el) {
      const s = getComputedStyle(el).overflowY;
      if ((s === "auto" || s === "scroll") && el.scrollHeight > el.clientHeight) return el;
      el = el.parentElement;
    }
    return null;
  }

  function zielBerechnen(y: number) {
    setZug((alt) => {
      if (!alt || !liste.current || !zugStart.current) return alt;
      // Abstand zum Start in Zeilen, Scrollen des Fensters eingerechnet.
      const box = scrollBehaelter();
      const gescrollt = box ? box.scrollTop - (Number(box.dataset.zugScroll) || 0) : 0;
      const dy = y - zugStart.current.y + gescrollt;
      const nach = Math.max(0, Math.min(zeilen.length - 1, alt.von + Math.round(dy / zugStart.current.hoehe)));
      return { ...alt, nach, dy };
    });
  }

  function randScrollen() {
    const box = scrollBehaelter();
    if (box) {
      const r = box.getBoundingClientRect();
      const y = letzteY.current;
      const rand = 48;
      const schritt = y < r.top + rand ? -Math.ceil((r.top + rand - y) / 4) : y > r.bottom - rand ? Math.ceil((y - (r.bottom - rand)) / 4) : 0;
      if (schritt) {
        box.scrollTop += schritt;
        zielBerechnen(y);
      }
    }
    scrollTakt.current = requestAnimationFrame(randScrollen);
  }

  function griffRunter(ev: React.PointerEvent<HTMLSpanElement>, index: number, id: string) {
    const li = ev.currentTarget.closest("li");
    if (!li) return;
    ev.preventDefault();
    // Auf der Liste fangen, nicht am Griff: React verschiebt die Zeile beim
    // Umsortieren im DOM, dabei ginge die Pointer-Capture verloren.
    liste.current?.setPointerCapture(ev.pointerId);
    const naechste = li.nextElementSibling?.getBoundingClientRect().top;
    const hoehe = naechste ? naechste - li.getBoundingClientRect().top : li.getBoundingClientRect().height + 6;
    const box = scrollBehaelter();
    if (box) box.dataset.zugScroll = String(box.scrollTop);
    zugStart.current = { y: ev.clientY, pointer: ev.pointerId, hoehe };
    letzteY.current = ev.clientY;
    setZug({ id, von: index, nach: index, dy: 0, hoehe });
    scrollTakt.current = requestAnimationFrame(randScrollen);
  }

  function griffBewegen(ev: React.PointerEvent<HTMLOListElement>) {
    if (!zugStart.current || ev.pointerId !== zugStart.current.pointer) return;
    letzteY.current = ev.clientY;
    zielBerechnen(ev.clientY);
  }

  function griffLos(ev: React.PointerEvent<HTMLOListElement>, abbrechen = false) {
    if (!zugStart.current || ev.pointerId !== zugStart.current.pointer) return;
    if (scrollTakt.current !== null) cancelAnimationFrame(scrollTakt.current);
    scrollTakt.current = null;
    zugStart.current = null;
    const fertig = zug;
    setZug(null);
    if (!abbrechen && fertig && fertig.nach !== fertig.von) slotAktualisieren(anzeige);
  }

  useEffect(
    () => () => {
      if (scrollTakt.current !== null) cancelAnimationFrame(scrollTakt.current);
    },
    [],
  );

  function schieben(index: number, delta: number) {
    const ziel = index + delta;
    if (ziel < 0 || ziel >= zeilen.length) return;
    const neu = zeilen.map((z) => ({ ...z }));
    const tmp = neu[index];
    neu[index] = neu[ziel];
    neu[ziel] = tmp;
    slotAktualisieren(neu);
  }

  return (
    <Fenster
      offen={offen}
      titel="Burgermenü"
      unterzeile="PC und Tablet getrennt — Handy scrollt die volle Liste."
      kennung="menue-anpassen"
      onSchliessen={onSchliessen}
    >
      <div className="cl-menue-anpassen">
        <div className="cl-menue-slots">
          <button type="button" data-an={slotName === "pc" ? "true" : undefined} onClick={() => setSlotName("pc")}>
            PC
          </button>
          <button
            type="button"
            data-an={slotName === "tablet" ? "true" : undefined}
            onClick={() => setSlotName("tablet")}
          >
            Tablet
          </button>
        </div>
        <ol
          className="cl-menue-anpassen-liste"
          ref={liste}
          data-zieht={zug ? "ja" : undefined}
          onPointerMove={griffBewegen}
          onPointerUp={(ev) => griffLos(ev)}
          onPointerCancel={(ev) => griffLos(ev, true)}
        >
          {anzeige.map((z, i) => (
            <li
              key={z.id}
              data-gezogen={zug?.id === z.id ? "ja" : undefined}
              // Die gezogene Zeile folgt dem Finger, die anderen rücken in Zeilenschritten.
              style={zug?.id === z.id ? { transform: `translateY(${zug.dy - (zug.nach - zug.von) * zug.hoehe}px)`, position: "relative", zIndex: 2 } : undefined}
            >
              <span
                className="cl-menue-griff"
                role="button"
                aria-label={`${z.name} ziehen`}
                title="Gedrückt halten und ziehen"
                onPointerDown={(ev) => griffRunter(ev, i, z.id)}
              >
                ⠿
              </span>
              <label>
                <input
                  type="checkbox"
                  checked={z.sichtbar}
                  onChange={(ev) => {
                    const neu = zeilen.map((x) => (x.id === z.id ? { ...x, sichtbar: ev.target.checked } : x));
                    slotAktualisieren(neu);
                  }}
                />
                {z.name}
              </label>
              <span>
                <button type="button" onClick={() => schieben(i, -1)} disabled={i === 0} aria-label="Nach oben">
                  ↑
                </button>
                <button
                  type="button"
                  onClick={() => schieben(i, 1)}
                  disabled={i === zeilen.length - 1}
                  aria-label="Nach unten"
                >
                  ↓
                </button>
              </span>
            </li>
          ))}
        </ol>
      </div>
    </Fenster>
  );
}
