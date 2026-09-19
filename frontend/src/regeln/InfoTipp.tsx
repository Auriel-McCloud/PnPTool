import { useState } from "react";
import { useAuthFallsVorhanden } from "../auth/AuthContext";
import { Fenster } from "../shell/Fenster";
import { schluessel as key, speichereErklaerung, useErklaerungen } from "./erklaerungen";
import "./infotipp.css";

/**
 * Das Zeichen neben einem Fachbegriff, das seine Erklärung aufklappt.
 *
 * Erscheint **nur, wenn der Schalter in der oberen Leiste an ist**
 * (docs/ui-konzept.md): neben jedem Attribut, jeder Fertigkeit und jedem
 * Regelbegriff dauerhaft ein Fragezeichen zu haben, würde das Blatt
 * zukleistern. Wer die Regeln kennt, schaltet es aus und sieht nichts davon.
 *
 * Ist zu einem Begriff noch nichts hinterlegt, bleibt das Zeichen blass —
 * die Spielleitung kann den Text dann an Ort und Stelle schreiben. Genau
 * dorthin sollen später auch die überarbeiteten Regeltexte fliessen.
 */
export function InfoTipp({
  campaignId,
  schluessel: sch,
  titel,
  erzwingen,
}: {
  campaignId: string;
  /** z.B. `trait:Körperkraft` — am besten über den Helfer `schluessel`. */
  schluessel: string;
  /** Überschrift des Fensters, falls noch kein Text hinterlegt ist. */
  titel: string;
  /** Zeigt das Zeichen unabhängig vom "Erklärungen"-Schalter — für die
   *  Charaktererstellung (Mark, 19.09.2026: "am wichtigsten", "immer"). Wer
   *  neu am Tisch sitzt, kennt die Begriffe noch nicht und hat den Schalter
   *  vermutlich nie gefunden, geschweige denn eingeschaltet. */
  erzwingen?: boolean;
}) {
  const erklaerungen = useErklaerungen(campaignId);
  // Schreiben darf nur die Spielleitung. Nicht als Eigenschaft von aussen,
  // weil das Zeichen an sehr vielen Stellen sitzt und die Angabe an jeder
  // neuen wieder durchgereicht (und vergessen) werden müsste. Der Server
  // lehnt fremde Schreibversuche ohnehin ab.
  const darfSchreiben = useAuthFallsVorhanden()?.me?.role === "GM";
  const [offen, setOffen] = useState(false);
  // Eigenes Fenster für die Langfassung — dieselbe Begründung wie bei den
  // Vorlagen-Erklärungen: ein zweites Popup über dem ersten, nicht ein
  // ausklappender Block, der das erste Fenster in der Höhe springen lässt.
  const [detailOffen, setDetailOffen] = useState(false);
  const [entwurf, setEntwurf] = useState<string | null>(null);
  const [sendet, setSendet] = useState(false);

  if (!erklaerungen.an && !erzwingen) return null;

  const vorhanden = erklaerungen.zu(sch);
  const hatDetail = Boolean(vorhanden?.langtext);

  async function sichern() {
    if (entwurf === null) return;
    setSendet(true);
    try {
      await speichereErklaerung(campaignId, sch, titel, entwurf);
      setEntwurf(null);
    } finally {
      setSendet(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className={`it-zeichen${vorhanden ? "" : " it-leer"}`}
        onClick={(e) => {
          // Sonst löste die Zeile darunter zugleich ihre eigene Aktion aus
          // (Fähigkeit antippen heisst später: würfeln).
          e.stopPropagation();
          setOffen(true);
        }}
        aria-label={`Erklärung zu ${titel}`}
        title={vorhanden ? `Erklärung zu ${titel}` : `Zu ${titel} ist noch nichts hinterlegt`}
      >
        ?
      </button>

      <Fenster
        offen={offen}
        titel={vorhanden?.titel || titel}
        unterzeile={vorhanden?.quelle === "KI" ? "maschinell erzeugt, noch nicht gegengelesen" : undefined}
        kennung={`erklaerung:${sch}`}
        onSchliessen={() => {
          setOffen(false);
          setEntwurf(null);
        }}
      >
        {entwurf === null ? (
          <>
            {vorhanden?.text ? (
              <p className="it-text">{vorhanden.text}</p>
            ) : (
              <p className="it-text it-fehlt">
                Zu diesem Begriff ist noch nichts hinterlegt.
                {darfSchreiben && " Du kannst die Erklärung hier schreiben."}
              </p>
            )}
            <div className="it-fuss">
              {hatDetail && (
                <button type="button" onClick={() => setDetailOffen(true)}>
                  Detail
                </button>
              )}
              {darfSchreiben && (
                <button type="button" onClick={() => setEntwurf(vorhanden?.text ?? "")}>
                  {vorhanden?.text ? "Bearbeiten" : "Erklärung schreiben"}
                </button>
              )}
            </div>
          </>
        ) : (
          <>
            <textarea
              value={entwurf}
              onChange={(e) => setEntwurf(e.target.value)}
              rows={8}
              placeholder={`Was ${titel} bedeutet und wie es sich auswirkt.`}
              autoFocus
            />
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button type="button" onClick={sichern} disabled={sendet}>
                {sendet ? "Wird gespeichert…" : "Speichern"}
              </button>
              <button type="button" onClick={() => setEntwurf(null)}>
                Abbrechen
              </button>
              <span className="it-hinweis">Leer speichern entfernt die Erklärung wieder.</span>
            </div>
          </>
        )}
      </Fenster>

      {/* Fenster über dem Fenster — nach demselben Muster wie die
          Vorlagen-Erklärungen in der Charaktererstellung. */}
      {hatDetail && (
        <Fenster
          offen={detailOffen}
          titel={vorhanden?.titel || titel}
          unterzeile="Ausführliche Beschreibung"
          kennung={`erklaerung-detail:${sch}`}
          onSchliessen={() => setDetailOffen(false)}
        >
          <p className="it-text it-text-lang">{vorhanden?.langtext}</p>
        </Fenster>
      )}
    </>
  );
}

export { key as erklaerungsSchluessel };
