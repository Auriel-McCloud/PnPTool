import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // auch über LAN-IP erreichbar (z.B. vom Handy), nicht nur localhost
    proxy: {
      // Backend läuft nur auf Port 8000, der vom Handy aus per Firewall blockiert ist.
      // Deshalb API-Calls über denselben (bereits erreichbaren) Port 5173 proxyen.
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      // hochgeladene Gegenstands-Bilder werden vom Backend statisch ausgeliefert,
      // müssen aus demselben Grund wie /api mitgeproxyt werden
      "/uploads": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
