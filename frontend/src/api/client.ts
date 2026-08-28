// Relative URL: läuft über den Vite-Dev-Proxy (siehe vite.config.ts), damit Backend-Traffic
// über denselben Port wie das Frontend läuft (wichtig für LAN-Zugriff, z.B. vom Handy,
// wo Port 8000 durch die Windows-Firewall blockiert ist, Port 5173 aber nicht).
const API_BASE = "";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// SL-Vorschau ("Sehen wie Spieler X"): ist hier eine Person-ID gesetzt, hängt
// jeder GET automatisch ?alsSpieler= an und bekommt die gefilterte Antwort.
// Bewusst Modul-Zustand statt Prop-Drilling durch jede Komponente: der Wert
// wird im Event-Handler synchron gesetzt, also lange bevor ein davon
// abhängiger Effect feuert — kein Wettlauf mit dem React-Render.
// Schreibzugriffe bleiben unberührt, die Vorschau ändert nie etwas.
let viewAsPersonId: string | null = null;

export function setViewAs(personId: string | null) {
  viewAsPersonId = personId;
}

export function getViewAs(): string | null {
  return viewAsPersonId;
}

function withViewAs(path: string): string {
  if (!viewAsPersonId) return path;
  return `${path}${path.includes("?") ? "&" : "?"}alsSpieler=${encodeURIComponent(viewAsPersonId)}`;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? "Unbekannter Fehler");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(withViewAs(path)),
  // Umgeht die Vorschau bewusst. Nötig für die Charakter-Auswahl des
  // Umschalters selbst: würde die Personenliste mitgefiltert, verschwände
  // womöglich genau der Charakter, den man gerade betrachtet, aus dem
  // Dropdown — und man käme nicht mehr zurück zur SL-Sicht.
  getAsGm: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
