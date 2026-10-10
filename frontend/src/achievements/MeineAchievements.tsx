import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { achievementsApi, type Verleihung } from "./api";
import "./achievements.css";

/**
 * Spieler-Ansicht: eigene erhaltene Achievements, neuestes zuerst (Marks
 * Vorgabe 27.09.2026). Jeder Eintrag lässt sich erneut öffnen, um den vollen
 * Text nochmal zu lesen — nicht nur eine einmalige Toast-Meldung.
 */
export function MeineAchievements({
  campaignId,
  offen,
  onSchliessen,
}: {
  campaignId: string;
  offen: boolean;
  onSchliessen: () => void;
}) {
  const [liste, setListe] = useState<Verleihung[]>([]);
  const [laedt, setLaedt] = useState(true);
  const [offeneId, setOffeneId] = useState<string | null>(null);

  useEffect(() => {
    if (!offen) return;
    setLaedt(true);
    achievementsApi
      .meine(campaignId)
      .then(setListe)
      .catch(() => setListe([]))
      .finally(() => setLaedt(false));
  }, [offen, campaignId]);

  return (
    <Fenster offen={offen} titel="🏆 Achievements" unterzeile="Deine Erfolge, neueste zuerst" kennung="achievements-meine" onSchliessen={onSchliessen}>
      <div className="ac-spieler-liste">
        {laedt && <p style={{ color: "var(--text-leise)" }}>Lade Achievements…</p>}
        {!laedt && liste.length === 0 && <p className="ac-leer">Noch keine Achievements erhalten.</p>}
        {liste.map((v) => (
          <button key={v.id} type="button" className="ac-eintrag" onClick={() => setOffeneId(v.id === offeneId ? null : v.id)}>
            <div className="ac-eintrag-kopf">
              <span className="ac-eintrag-icon" aria-hidden="true">
                {v.achievementIcon || "🏆"}
              </span>
              <span className="ac-eintrag-name">{v.achievementName}</span>
              <span className="ac-eintrag-zeit">{new Date(v.zeitpunkt).toLocaleDateString("de-AT")}</span>
            </div>
            {offeneId === v.id && (
              <p className="ac-eintrag-text">{v.text || v.achievementBeschreibung || "(kein Text hinterlegt)"}</p>
            )}
          </button>
        ))}
      </div>
    </Fenster>
  );
}
