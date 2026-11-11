import { useEffect, useState } from "react";
import { Fenster } from "../shell/Fenster";
import { kontakteApi, type Mitspieler } from "./api";
import { vorschau } from "../shell/vorschau";

/**
 * „Mitspieler anschreiben“: Kontakt zu einem anderen Spielercharakter anbieten.
 *
 * Wie bei NPC-Kontakten muss der Kontakt erst hergestellt werden — hier aber
 * ohne Spielleitung: der andere Spieler bekommt ein Popup und entscheidet
 * selbst (Verhandlungssystem, Art SPIELER_KONTAKT). Erst nach „Annehmen“
 * erscheint der Chat in beiden Kontaktlisten.
 */
export function MitspielerFenster({
  campaignId,
  onSchliessen,
}: {
  campaignId: string;
  onSchliessen: () => void;
}) {
  const [liste, setListe] = useState<Mitspieler[] | null>(null);
  const [sendetAn, setSendetAn] = useState<string | null>(null);
  const [gesendet, setGesendet] = useState<Set<string>>(new Set());
  const [fehler, setFehler] = useState<string | null>(null);

  useEffect(() => {
    kontakteApi
      .mitspieler(campaignId)
      .then(setListe)
      .catch((e) => setFehler(e instanceof Error ? e.message : "Konnte Mitspieler nicht laden"));
  }, [campaignId]);

  async function anfragen(m: Mitspieler) {
    if (sendetAn) return;
    setSendetAn(m.id);
    setFehler(null);
    try {
      await kontakteApi.spielerAnfrage(campaignId, m.id);
      setGesendet((alt) => new Set(alt).add(m.id));
    } catch (e) {
      setFehler(e instanceof Error ? e.message : "Anfrage konnte nicht gesendet werden");
    } finally {
      setSendetAn(null);
    }
  }

  return (
    <Fenster
      titel="Mitspieler anschreiben"
      unterzeile="Kontakt austauschen"
      kennung="messenger-mitspieler"
      offen={true}
      onSchliessen={onSchliessen}
    >
      <div className="msg-mitspieler">
        <p className="msg-generieren-hinweis">
          Dein Mitspieler bekommt eine Anfrage und entscheidet selbst. Nach der Zusage ist der Chat bei euch
          beiden offen.
        </p>
        {!liste && !fehler && <p className="msg-generieren-hinweis">Lädt…</p>}
        {liste?.length === 0 && <p className="msg-generieren-hinweis">Noch niemand sonst am Tisch.</p>}
        {liste?.map((m) => {
          const angefragt = gesendet.has(m.id);
          const gesperrt = m.bereitsKontakt || angefragt || sendetAn !== null;
          return (
            <button
              key={m.id}
              type="button"
              className="msg-kontakt"
              disabled={gesperrt}
              onClick={() => void anfragen(m)}
            >
              <span className="msg-portrait">
                {m.bildUrl ? <img src={vorschau(m.bildUrl, "klein")} loading="lazy" decoding="async" alt="" /> : <span className="msg-portrait-leer">?</span>}
              </span>
              <span className="msg-info">
                <span className="msg-name">{m.name}</span>
                <span className="msg-vorschau">
                  {m.bereitsKontakt
                    ? "Kontakt besteht"
                    : angefragt
                      ? "Anfrage gesendet"
                      : sendetAn === m.id
                        ? "Sendet…"
                        : "Kontakt anbieten"}
                </span>
              </span>
            </button>
          );
        })}
        {fehler && <p className="msg-generieren-fehler">{fehler}</p>}
      </div>
    </Fenster>
  );
}
