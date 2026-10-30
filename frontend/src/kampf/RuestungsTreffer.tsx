import { useEffect, useState } from "react";
import type { RuestungsArt } from "../items/api";
import { Fenster } from "../shell/Fenster";
import { Zahlenpad } from "../shell/Zahlenpad";
import { bogenApi, type RuestungTrefferErgebnis } from "../traits/bogenApi";

/**
 * "3× Tödlich" eingeben, Rüstung und Gesundheit rechnen automatisch mit.
 *
 * Genau der Ablauf aus dem Konzept — und mehr als Art und Stärke braucht es
 * nicht: die getragene Rüstung wirkt als **ein Pool**, es gibt keine
 * Körperzonen und damit nichts zu zielen. Welche Teile der Kästchenschaden
 * aufbraucht (dichtestes zuerst), rechnet der Server; siehe
 * backend/app/kampf/ruestung.py und docs/api/ruestung.md.
 *
 * Was zurückkommt, wird ausdrücklich angezeigt statt stillschweigend
 * verbucht: wer nur "3× Tödlich" eintippt, soll sehen, was daraus geworden
 * ist — sonst wirkt die Automatik wie ein Zufallsgenerator.
 *
 * "Elementar" (30.10.2026, Ki-Tama-Attacken) ist KEINE vierte Art, die das
 * Backend kennt — es ist eine Anzeige-Wahl, die hier zusätzlich nach der
 * Effektivität gegen das Ziel fragt und daraus erst eine der drei echten
 * Arten macht (sehr effektiv → Schwerheilbar, effektiv → Tödlich, nicht
 * effektiv → Schlag — Mark, 30.10.2026). Keine automatische
 * Typen-Tabelle (Feuer/Eis/...), die SL entscheidet das am Tisch.
 */

type AnzeigeArt = RuestungsArt | "elementar";

const ARTEN: { wert: AnzeigeArt; label: string; hinweis: string }[] = [
  { wert: "aggraviert", label: "Schwerheilbar", hinweis: "z.B. eine Explosion — trifft immer voll auf die Rüstung durch." },
  { wert: "schwer", label: "Tödlich", hinweis: "z.B. Schusswaffen — Rüstung wandelt es in Schlagschaden um." },
  { wert: "schlag", label: "Schlag", hinweis: "z.B. Faustschlag — Rüstung halbiert, was durchkommt." },
  { wert: "elementar", label: "Elementar", hinweis: "Feuer, Eis, Blitz... — wie effektiv gegen das Ziel entscheidet die Art." },
];

const EFFEKTIVITAET: { wert: "sehr" | "normal" | "nicht"; label: string; ergibt: RuestungsArt }[] = [
  { wert: "sehr", label: "Sehr effektiv", ergibt: "aggraviert" },
  { wert: "normal", label: "Effektiv", ergibt: "schwer" },
  { wert: "nicht", label: "Nicht effektiv", ergibt: "schlag" },
];

function artLabel(art: RuestungsArt) {
  return ARTEN.find((a) => a.wert === art)?.label ?? art;
}

export function RuestungsTreffer({
  campaignId,
  personId,
  offen,
  onSchliessen,
  onAngewendet,
}: {
  campaignId: string;
  personId: string;
  offen: boolean;
  onSchliessen: () => void;
  /** Nach einem angewendeten Treffer — der Aufrufer lädt daraufhin neu. */
  onAngewendet: () => void | Promise<void>;
}) {
  const [art, setArt] = useState<AnzeigeArt>("schlag");
  const [effektivitaet, setEffektivitaet] = useState<"sehr" | "normal" | "nicht">("normal");
  // Als Zeichenkette geführt wie in ZustandFenster (Zahlenpad statt
  // Systemtastatur) — vorher stand hier ein rohes <input type="number">,
  // das je nach Gerät die Systemtastatur samt Spinner-Pfeilen aufklappte
  // und optisch nicht zu den übrigen Zahlen-Eingaben im Tool passte.
  const [staerkeEingabe, setStaerkeEingabe] = useState("1");
  // Die "1" ist nur ein Vorschlag (häufigster Fall am Tisch), kein Tippstart
  // wie bei Gesundheit/Willenskraft (die beginnen leer). Ohne diese
  // Unterscheidung hängt der erste Tastendruck an die Vorgabe an: "4"
  // getippt ergibt "14" statt 4 — genau der Fehler, den Mark gemeldet hat.
  // Der erste Tastendruck ersetzt die Vorgabe komplett, danach wird normal
  // angehängt wie überall sonst.
  const [staerkeIstVorschlag, setStaerkeIstVorschlag] = useState(true);
  const [laeuft, setLaeuft] = useState(false);
  const [ergebnis, setErgebnis] = useState<RuestungTrefferErgebnis | null>(null);

  // Bei jedem Öffnen frisch beginnen — sonst zeigt das Fenster noch das
  // Ergebnis des letzten Treffers, wenn ein neuer angesagt wird.
  useEffect(() => {
    if (offen) {
      setArt("schlag");
      setEffektivitaet("normal");
      setStaerkeEingabe("1");
      setStaerkeIstVorschlag(true);
      setErgebnis(null);
    }
  }, [offen]);

  const staerke = Number(staerkeEingabe) || 0;
  // "Elementar" ist nur eine Anzeige-Wahl — vor dem Anwenden immer auf eine
  // der drei echten Arten auflösen (siehe Kommentar oben am Dateikopf).
  const aufgeloesteArt: RuestungsArt =
    art === "elementar" ? EFFEKTIVITAET.find((e) => e.wert === effektivitaet)!.ergibt : art;

  async function anwenden() {
    setLaeuft(true);
    try {
      setErgebnis(await bogenApi.ruestungTreffer(campaignId, personId, aufgeloesteArt, staerke));
      await onAngewendet();
    } finally {
      setLaeuft(false);
    }
  }

  const zerstoert = ergebnis?.betroffen.filter((b) => b.zerstoert) ?? [];

  return (
    <Fenster
      offen={offen}
      titel="Treffer eintragen"
      unterzeile="Rüstung rechnet automatisch mit"
      kennung="ruestungs-treffer"
      onSchliessen={onSchliessen}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: 14, padding: 4 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: "0.9em", color: "var(--text-leise)" }}>Schadensart</span>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {ARTEN.map((a) => (
              <button
                key={a.wert}
                type="button"
                data-aktiv={art === a.wert}
                onClick={() => setArt(a.wert)}
                title={a.hinweis}
                style={{
                  borderColor: art === a.wert ? "var(--neon)" : undefined,
                  color: art === a.wert ? "var(--neon)" : undefined,
                }}
              >
                {a.label}
              </button>
            ))}
          </div>
          {art === "elementar" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
              <span style={{ fontSize: "0.85em", color: "var(--text-leise)" }}>
                Wie effektiv gegen das Ziel?
              </span>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {EFFEKTIVITAET.map((e) => (
                  <button
                    key={e.wert}
                    type="button"
                    data-aktiv={effektivitaet === e.wert}
                    onClick={() => setEffektivitaet(e.wert)}
                    title={`Wird als ${artLabel(e.ergibt)} gewertet.`}
                    style={{
                      borderColor: effektivitaet === e.wert ? "var(--neon)" : undefined,
                      color: effektivitaet === e.wert ? "var(--neon)" : undefined,
                    }}
                  >
                    {e.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: "0.9em", color: "var(--text-leise)" }}>Stärke</span>
          <Zahlenpad
            wert={staerkeEingabe}
            onZiffer={(z) => {
              setStaerkeIstVorschlag(false);
              setStaerkeEingabe((alt) => {
                if (staerkeIstVorschlag) return z;
                return alt.length >= 2 ? alt : (alt + z).replace(/^0+(?=\d)/, "");
              });
            }}
            onLoeschen={() => {
              setStaerkeIstVorschlag(false);
              setStaerkeEingabe((a) => (staerkeIstVorschlag ? "" : a.slice(0, -1)));
            }}
            onAlleLoeschen={() => {
              setStaerkeIstVorschlag(false);
              setStaerkeEingabe("");
            }}
          />
        </div>

        <button type="button" onClick={anwenden} disabled={laeuft} style={{ fontWeight: 600 }}>
          Treffer anwenden
        </button>

        {ergebnis && (
          <div style={{ fontSize: "0.9em", color: "var(--text-leise)", display: "flex", flexDirection: "column", gap: 4 }}>
            <p style={{ margin: 0 }}>
              Durchgekommen:{" "}
              <strong>
                {ergebnis.hpMenge} {artLabel(ergebnis.hpArt)}
              </strong>
              {ergebnis.betroffen.length === 0 && " — ohne Rüstung voll angekommen"}
            </p>
            {ergebnis.kaestchenSchaden > 0 && (
              <p style={{ margin: 0 }}>
                Rüstung: <strong>−{ergebnis.kaestchenSchaden}</strong> Kästchen (
                {ergebnis.betroffen.map((b) => `${b.name} −${b.verlust}`).join(", ")})
              </p>
            )}
            {(ergebnis.hotRueckschlag ?? []).map((r) => (
              <p key={r.riggerId} style={{ margin: 0, color: "var(--p-magenta)" }}>
                Hot-Rückschlag: <strong>{r.riggerName}</strong> nimmt {r.schlag} Schlagschaden
              </p>
            ))}
            {(ergebnis.dumpshock ?? []).map((r) => (
              <p key={`dump-${r.riggerId}`} style={{ margin: 0, color: "var(--p-magenta)" }}>
                Dumpshock: <strong>{r.riggerName}</strong> setzt den Rest der Runde aus. Die Verbindung ist tot.
              </p>
            ))}
            {zerstoert.length > 0 && (
              <p style={{ margin: 0, color: "var(--nein)" }}>
                Zerstört: <strong>{zerstoert.map((b) => b.name).join(", ")}</strong> — liegt jetzt im Mitgeführten
                und schützt nicht mehr, bis es repariert ist.
              </p>
            )}
          </div>
        )}
      </div>
    </Fenster>
  );
}
