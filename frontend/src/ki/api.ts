/**
 * API für objektbezogene KI-Textgenerierung — der ✨-Knopf neben „SL-geheim"
 * im RichTextEditor (Beschreibung/Notizen jeder Entität).
 *
 * Getrennt von ideenschmiede/api.ts, weil dieser Aufruf nichts anlegt oder
 * verschiebt: er liefert nur einen Textvorschlag zurück, den das Frontend
 * bei „Übernehmen" selbst ans Editor-Ende anhängt (siehe KiTextPopup.tsx).
 */
import { api } from "../api/client";

export interface KiObjektTextInput {
  objektTyp: string;
  objektName: string;
  bisherigerText: string;
  prompt: string;
}

export async function kiObjektText(campaignId: string, input: KiObjektTextInput): Promise<string> {
  const antwort = await api.post<{ text: string }>(`/api/campaigns/${campaignId}/ki/objekt-text`, input);
  return antwort.text;
}

/** Ein einzelner Befund der Rechtschreib-/Grammatik-/Logikprüfung (siehe
 * auch ideenschmiede/api.ts — identisches Format, hier nur für den
 * seitenlosen 🔍-Knopf im generischen RichTextEditor). */
export interface PruefBefund {
  art: "rechtschreibung" | "grammatik" | "logik";
  zitat: string;
  vorschlag: string;
  begruendung: string;
}

/** Prüft ein freies Beschreibungs-/Notizen-Feld — kein Seitenbezug, kein
 * Speichern; das Übernehmen passiert lokal im Editor (siehe RichTextEditor.tsx). */
export async function kiObjektTextPruefen(campaignId: string, text: string): Promise<PruefBefund[]> {
  const antwort = await api.post<{ befunde: PruefBefund[] }>(`/api/campaigns/${campaignId}/ki/objekt-text/pruefen`, {
    text,
  });
  return antwort.befunde;
}

/** Für den 'KI-Bild generieren'-Knopf an Personen-/Orts-/Gegenstands-Bildern. */
export interface KiBildPromptInput {
  objektTyp: string;
  objektName: string;
  bisherigeBeschreibung?: string;
}

/** Schritt 1 des KI-Bild-Popups: Prompt-Vorschlag aus Name+Beschreibung. */
export async function kiBildPrompt(campaignId: string, input: KiBildPromptInput): Promise<string> {
  const antwort = await api.post<{ prompt: string }>(`/api/campaigns/${campaignId}/ki/bild-prompt`, input);
  return antwort.prompt;
}

/**
 * Schritt 2: generiert ein Bild und liefert es als Blob zur Vorschau —
 * speichert NICHTS. „Übernehmen" schickt den Blob als Datei an die jeweils
 * bestehende Bild-Upload-Route (siehe KiBildPopup.tsx).
 */
export async function kiBildGenerieren(
  campaignId: string,
  provider: "lokal" | "cloud",
  prompt: string,
): Promise<Blob> {
  const antwort = await fetch(`/api/campaigns/${campaignId}/ki/bild-generieren`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider, prompt }),
  });
  if (!antwort.ok) {
    const f = await antwort.json().catch(() => ({ detail: antwort.statusText }));
    throw new Error(f.detail ?? "Bildgenerierung fehlgeschlagen");
  }
  return antwort.blob();
}

/** Ein von der KI erkannter Verknüpfungsvorschlag (Auto-Verknüpfung). */
export interface VerknuepfungsVorschlag {
  zitat: string;
  typ: "Person" | "Ort" | "Event" | "Fraktion";
  name: string;
  /** Gesetzt, wenn der Name zu einer bestehenden Entität passt; sonst legt
   * "anwenden" einen neuen Entwurf in der Ideenschmiede an. */
  zielId: string | null;
}

/** Ein von der KI erkannter Beziehungsvorschlag zwischen zwei Entitäten
 * (echte VERBINDUNG-Kante, nicht nur ein Verweis zur Wiki-Seite). */
export interface BeziehungsVorschlag {
  typ1: "Person" | "Ort" | "Event" | "Fraktion";
  name1: string;
  zielId1: string | null;
  typ2: "Person" | "Ort" | "Event" | "Fraktion";
  name2: string;
  zielId2: string | null;
  beziehungstyp: string;
  beschreibung: string;
}

export interface VorschlaegeAntwort {
  verweise: VerknuepfungsVorschlag[];
  beziehungen: BeziehungsVorschlag[];
}

export interface AnwendenErgebnis {
  ersetzt: boolean;
  inhalt: string;
  zielId: string;
  neuAngelegt: boolean;
}

export interface BeziehungAnwendenErgebnis {
  verbindungId: string;
  zielId1: string;
  zielId2: string;
  neuAngelegt1: boolean;
  neuAngelegt2: boolean;
}

/** Auto-Verknüpfung Schritt 1: lässt die KI Erwähnungen UND Beziehungen in der Seite erkennen. */
export async function verknuepfungsVorschlaege(campaignId: string, seitenId: string): Promise<VorschlaegeAntwort> {
  return api.post<VorschlaegeAntwort>(`/api/campaigns/${campaignId}/ki/wiki/${seitenId}/verknuepfung/vorschlaege`);
}

/** Auto-Verknüpfung Schritt 2: wendet EINEN bestätigten Verweis-Vorschlag an — fügt
 * den Verweis-Chip ein (legt bei Bedarf zuerst einen Ideenschmiede-Entwurf an). */
export async function verknuepfungAnwenden(
  campaignId: string,
  seitenId: string,
  vorschlag: VerknuepfungsVorschlag,
): Promise<AnwendenErgebnis> {
  return api.post<AnwendenErgebnis>(`/api/campaigns/${campaignId}/ki/wiki/${seitenId}/verknuepfung/anwenden`, {
    zitat: vorschlag.zitat,
    typ: vorschlag.typ,
    name: vorschlag.name,
    zielId: vorschlag.zielId,
  });
}

/** Auto-Verknüpfung Schritt 2b: wendet EINEN bestätigten Beziehungs-Vorschlag
 * an — legt eine echte VERBINDUNG-Kante zwischen den zwei Entitäten an (legt
 * bei Bedarf zuerst einen Ideenschmiede-Entwurf für die fehlende Seite an). */
export async function verknuepfungBeziehungAnwenden(
  campaignId: string,
  seitenId: string,
  vorschlag: BeziehungsVorschlag,
): Promise<BeziehungAnwendenErgebnis> {
  return api.post<BeziehungAnwendenErgebnis>(`/api/campaigns/${campaignId}/ki/wiki/${seitenId}/verknuepfung/beziehung`, {
    typ1: vorschlag.typ1,
    name1: vorschlag.name1,
    zielId1: vorschlag.zielId1,
    typ2: vorschlag.typ2,
    name2: vorschlag.name2,
    zielId2: vorschlag.zielId2,
    beziehungstyp: vorschlag.beziehungstyp,
    beschreibung: vorschlag.beschreibung,
  });
}

/** Eine per Dokument-Import angelegte Wiki-Seiten-Entwurf (Auto-Verknüpfung
 * bereits gelaufen — `verknuepfungen` zählt, wie viele Vorschläge dabei
 * angewandt wurden). */
export interface ImportierteSeite {
  id: string;
  titel: string;
  parentId: string | null;
  verknuepfungen: number;
}

export interface ImportAntwort {
  seiten: ImportierteSeite[];
}

/**
 * Wiki-Import: lädt ein .docx/.pdf-Dokument hoch, die KI teilt es anhand der
 * erkannten Struktur (Überschriften/Kapitel) in Wiki-Seiten-Entwürfe auf und
 * verknüpft sie automatisch (bestehende Auto-Verknüpfungs-Logik je Seite).
 * `fetch` statt des `api`-Helfers, weil hier ein `FormData`-Body (kein JSON)
 * geschickt wird — derselbe Ansatz wie `kiBildGenerieren` oben.
 */
export async function wikiImportieren(campaignId: string, datei: File): Promise<ImportAntwort> {
  const formData = new FormData();
  formData.append("datei", datei);
  const antwort = await fetch(`/api/campaigns/${campaignId}/ki/wiki/import`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  if (!antwort.ok) {
    const f = await antwort.json().catch(() => ({ detail: antwort.statusText }));
    throw new Error(f.detail ?? "Import fehlgeschlagen");
  }
  return antwort.json();
}
