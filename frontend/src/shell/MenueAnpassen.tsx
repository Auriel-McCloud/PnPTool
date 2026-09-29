import { useEffect, useMemo, useState } from "react";
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
        <ol className="cl-menue-anpassen-liste">
          {zeilen.map((z, i) => (
            <li key={z.id}>
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
