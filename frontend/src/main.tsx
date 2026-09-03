import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
// Stellt das Vollbild nach dem Entsperren wieder her (siehe dort).
import "./shell/vollbild";
import { themeLesen, themeSetzen } from './theme/theme'

// Theme setzen, bevor React rendert — sonst blitzt kurz das Standardtheme auf.
themeSetzen(themeLesen())

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
