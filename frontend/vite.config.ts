import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
// Backend-Ziel für den Proxy: lokal läuft das Backend direkt auf dem Host
// (Port 8001, siehe CLAUDE.md), im Docker-Compose-Deploy heißt der Service
// "backend" und lauscht intern auf 8000. Per Env-Var umschaltbar, damit
// vite.config.ts für beide Fälle unverändert bleibt.
const backendTarget = process.env.VITE_BACKEND_URL || "http://localhost:8001"

export default defineConfig({
  plugins: [react()],
  // Zwingt Vite, beim Serverstart den GESAMTEN Quellbaum nach Abhängigkeiten
  // zu durchsuchen und vorab zu bündeln, statt sie erst beim ersten Besuch
  // einer Seite "live" zu entdecken. Ohne das löst jeder neu betretene
  // Programmteil (z.B. das erste Öffnen der Ideenschmiede) einen vollen
  // Seiten-Reload aus ("new dependency optimized") — mitten im Tippen sehr
  // störend und wirkt wie ein Absturz zurück zur Übersicht. Kostet ein paar
  // Sekunden längeren Start, dafür danach keine Überraschungs-Reloads mehr.
  optimizeDeps: {
    entries: ["src/**/*.{ts,tsx}"],
  },
  server: {
    host: true, // auch über LAN-IP erreichbar (z.B. vom Handy), nicht nur localhost
    // Vite blockt seit v5 unbekannte Host-Header (Rebinding-Schutz). Der
    // nginx-Reverse-Proxy auf bebop reicht den Host-Header pnptool.aurielmc.cloud
    // unverändert durch, den Vite sonst als "nicht erlaubt" ablehnt (403).
    allowedHosts: ["pnptool.aurielmc.cloud"],
    proxy: {
      // Backend läuft nur auf Port 8000, der vom Handy aus per Firewall blockiert ist.
      // Deshalb API-Calls über denselben (bereits erreichbaren) Port 5173 proxyen.
      "/api": {
        target: backendTarget,
        changeOrigin: true,
        // Ohne ws:true reicht der Proxy nur HTTP weiter — die Live-Leitung
        // für SL-Popups (/api/.../mitteilungen/live) käme nie beim Backend an.
        ws: true,
      },
      // hochgeladene Gegenstands-Bilder werden vom Backend statisch ausgeliefert,
      // müssen aus demselben Grund wie /api mitgeproxyt werden
      "/uploads": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
})
