import { api } from "../api/client";

/**
 * Fertigkeiten-Spezialisierungen: Slots, die automatisch bei
 * Fertigkeit-Rating 4 (ein Slot) und 6 (ein zweiter) entstehen, oder
 * jederzeit ab Rating 4 für 4 EP zusätzlich gekauft werden — siehe
 * backend/app/spezialisierungen/repository.py.
 *
 * Gilt NUR für Fertigkeiten (die 30 Kern-Fertigkeiten + die sechs
 * NeuroWeaving-Fertigkeiten) — nie für Attribute oder Sphären (siehe
 * Moduldocstring im Backend).
 */
export interface Spezialisierung {
  id: string;
  campaignId: string;
  personId: string;
  traitDefId: string;
  /** Leer = noch unbenannter Slot. */
  text: string;
  quelle: "automatisch" | "gekauft";
  /** War die zuletzt gesetzte Benennung ein Spieler (true) oder die SL
   * (false)? Rein informativ fürs Popup, keine Zugriffslogik. */
  benanntVonSpieler: boolean;
  erstelltAm: string;
}

function basis(cid: string, personId: string) {
  return `/api/campaigns/${cid}/personen/${personId}/spezialisierungen`;
}

export const spezialisierungenApi = {
  /** Alle Slots dieser Person, benannt wie unbenannt — das Charakterblatt
   * gruppiert clientseitig nach traitDefId. */
  vonPerson: (cid: string, personId: string) =>
    api.get<Spezialisierung[]>(basis(cid, personId)),
  /**
   * Einen Slot (be)nennen. Ein noch leerer Slot darf vom Spieler ODER der
   * SL einmalig benannt werden; danach ändert nur noch die SL ihn (403
   * sonst) — siehe backend/app/spezialisierungen/routes.py::benennen.
   */
  benennen: (cid: string, personId: string, spezialisierungId: string, text: string) =>
    api.post<Spezialisierung>(`${basis(cid, personId)}/${spezialisierungId}/benennen`, { text }),
  /** Einen zusätzlichen Slot für 4 EP kaufen (ab Fertigkeitsrating 4). */
  kaufen: (cid: string, personId: string, traitDefId: string) =>
    api.post<Spezialisierung>(`${basis(cid, personId)}/kaufen`, { traitDefId }),
};
