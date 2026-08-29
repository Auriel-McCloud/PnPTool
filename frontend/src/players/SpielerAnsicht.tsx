import { useEffect, useState } from "react";
import { entitiesApi, type Event, type Ort, type Person } from "../entities/api";
import { CampaignGraphView } from "../graph/CampaignGraphView";
import { ABLAGEN, itemsApi, type Ablage, type GegenstandMitBesitzer } from "../items/api";
import { parseRichText } from "../richtext/content";
import { RichTextView } from "../richtext/RichTextView";
import { CommlinkShell, type Bereich } from "../shell/CommlinkShell";
import "../items/gegenstaende.css";
import { playersApi, type SpielerMe } from "./api";

/**
 * Die Spieler-Ansicht — dieselbe Hülle wie beim Spielleiter, nur mit weniger
 * Bereichen und ohne Bearbeiten (siehe docs/ui-konzept.md, "eine Hülle, zwei
 * Rollen").
 *
 * Gefiltert wird ausschließlich serverseitig: hier kommt nur an, was der
 * Spieler sehen darf. Diese Ansicht versteckt nichts selbst — sie könnte es
 * auch nicht, die Daten sind schlicht nicht da.
 */
const BEREICHE: Bereich[] = [
  { id: "kontakte", name: "Kontakte", symbol: "◍", farbe: "#00e5ff" },
  { id: "inventar", name: "Inventar", symbol: "◈", farbe: "#a865d8" },
  { id: "orte", name: "Orte", symbol: "⌖", farbe: "#2fa96a" },
  { id: "graph", name: "Beziehungen", symbol: "⬡", farbe: "#4d8bd8" },
  { id: "blatt", name: "Charakterblatt", symbol: "▤", farbe: "#ffb648", bald: true },
  { id: "notizen", name: "Notizen", symbol: "✎", farbe: "#3ddc84", bald: true },
];

function Karte({ titel, unter, text }: { titel: string; unter?: string; text?: string }) {
  return (
    <article style={{ borderBottom: "1px solid var(--linie)", padding: "10px 0" }}>
      <h3 style={{ margin: 0, color: "var(--text)", textTransform: "none", letterSpacing: 0 }}>
        {titel}
        {unter && <span style={{ color: "var(--text-leise)", fontWeight: "normal" }}> · {unter}</span>}
      </h3>
      {text && (
        <div style={{ marginTop: 4, color: "var(--text-leise)" }}>
          <RichTextView content={parseRichText(text)} />
        </div>
      )}
    </article>
  );
}

export function SpielerAnsicht({ onAbgemeldet }: { onAbgemeldet: () => void }) {
  const [ich, setIch] = useState<SpielerMe | null>(null);
  const [bereich, setBereich] = useState("kontakte");
  const [ablageFilter, setAblageFilter] = useState<Ablage>("AUSGERUESTET");
  const [personen, setPersonen] = useState<Person[]>([]);
  const [orte, setOrte] = useState<Ort[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [sachen, setSachen] = useState<GegenstandMitBesitzer[]>([]);

  useEffect(() => {
    playersApi.me().then(setIch).catch(() => setIch(null));
  }, []);

  useEffect(() => {
    if (!ich) return;
    const cid = ich.campaignId;
    entitiesApi.listPersonen(cid).then(setPersonen).catch(() => setPersonen([]));
    entitiesApi.listOrte(cid).then(setOrte).catch(() => setOrte([]));
    entitiesApi.listEvents(cid).then(setEvents).catch(() => setEvents([]));
    itemsApi.listAlle(cid).then(setSachen).catch(() => setSachen([]));
  }, [ich]);

  if (!ich) return null;

  // Was der Spieler selbst besitzt, steht zuerst — alles andere ist Beiwerk.
  const meine = sachen.filter((g) => g.ownerId === ich.personId);
  const fremde = sachen.filter((g) => g.ownerId !== ich.personId);

  async function umlegen(itemId: string, ziel: Ablage) {
    if (!ich) return;
    // Ohne festes Ziel: der Spieler legt nur die Art fest, das genaue Wohin
    // (welches Fahrzeug, welcher Ort) bleibt Sache der Spielleitung.
    await itemsApi.setAblage(ich.campaignId, itemId, ziel, null);
    const frisch = await itemsApi.listAlle(ich.campaignId);
    setSachen(frisch);
  }

  async function abmelden() {
    await playersApi.abmelden();
    onAbgemeldet();
  }

  return (
    <CommlinkShell
      bereiche={BEREICHE}
      aktiv={bereich}
      onBereichWechsel={setBereich}
      titel={`${ich.campaignName} — ${BEREICHE.find((b) => b.id === bereich)?.name ?? ""}`}
      werkzeuge={
        <button type="button" className="cl-werkzeug" onClick={abmelden} title="Abmelden">
          ⏻
        </button>
      }
      fuss={
        <>
          <div style={{ color: "var(--text-leise)" }}>{ich.name}</div>
          <div>{ich.personName ?? "kein Charakter"}</div>
        </>
      }
    >
      {bereich === "kontakte" && (
        <>
          {personen.length === 0 && <p style={{ color: "var(--text-leise)" }}>Du kennst noch niemanden.</p>}
          {personen.map((p) => (
            <Karte
              key={p.id}
              titel={p.name}
              unter={p.id === ich.personId ? "du" : undefined}
              text={p.description}
            />
          ))}
        </>
      )}

      {bereich === "inventar" && (
        <>
          <div className="gg-reiter" style={{ marginBottom: 12 }}>
            {ABLAGEN.map((a) => {
              const anzahl = meine.filter((g) => g.ablage === a.wert).length;
              return (
                <button
                  key={a.wert}
                  type="button"
                  data-aktiv={ablageFilter === a.wert}
                  onClick={() => setAblageFilter(a.wert)}
                >
                  {a.symbol} {a.label} <span className="gg-reiter-zahl">{anzahl}</span>
                </button>
              );
            })}
          </div>

          {meine.filter((g) => g.ablage === ablageFilter).length === 0 && (
            <p style={{ color: "var(--text-leise)" }}>Hier ist nichts.</p>
          )}
          {meine
            .filter((g) => g.ablage === ablageFilter)
            .map((g) => (
              <div key={g.id} style={{ borderBottom: "1px solid var(--linie)", padding: "10px 0" }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
                  <strong style={{ color: "var(--text)" }}>{g.hatMenge ? `${g.name} ×${g.menge}` : g.name}</strong>
                  <span style={{ color: "var(--text-leise)", fontSize: "0.85em" }}>
                    {[g.typ, g.preis > 0 ? `${g.preis}¥` : null].filter(Boolean).join(" · ")}
                    {g.ablageZielName && ` · in ${g.ablageZielName}`}
                  </span>
                </div>
                {g.description && (
                  <div style={{ marginTop: 4, color: "var(--text-leise)" }}>
                    <RichTextView content={parseRichText(g.description)} />
                  </div>
                )}
                {/* Die einzige Stelle, an der ein Spieler etwas verändern darf */}
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
                  {ABLAGEN.filter((a) => a.wert !== g.ablage).map((a) => (
                    <button key={a.wert} type="button" onClick={() => umlegen(g.id, a.wert)}>
                      → {a.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}

          {fremde.length > 0 && (
            <>
              <h3 style={{ marginTop: 20 }}>Anderswo gesehen</h3>
              {fremde.map((g) => (
                <Karte key={g.id} titel={g.name} unter={g.ownerName ?? undefined} text={g.description} />
              ))}
            </>
          )}
        </>
      )}

      {bereich === "orte" && (
        <>
          {orte.length === 0 && <p style={{ color: "var(--text-leise)" }}>Noch keine Orte bekannt.</p>}
          {orte.map((o) => (
            <Karte key={o.id} titel={o.name} text={o.description} />
          ))}
          {events.length > 0 && (
            <>
              <h3 style={{ marginTop: 20 }}>Was geschehen ist</h3>
              {events.map((e) => (
                <Karte key={e.id} titel={e.title} unter={e.timestamp || undefined} text={e.description} />
              ))}
            </>
          )}
        </>
      )}

      {bereich === "graph" && <CampaignGraphView campaignId={ich.campaignId} />}
    </CommlinkShell>
  );
}
