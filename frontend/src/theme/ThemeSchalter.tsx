import { useEffect, useState } from "react";
import { THEMES, THEME_LABELS, themeLesen, themeSetzen, type ThemeName } from "./theme";

/**
 * Themewechsel in der oberen Werkzeugleiste.
 *
 * Bewusst ein einfacher Durchschalter statt eines Menues: es gibt wenige
 * Themes, und der Wechsel soll wie ein Geraeteschalter wirken, nicht wie
 * eine Einstellungsseite.
 *
 * Der Wechsel wirkt sofort auf die ganze Oberflaeche, weil alles ueber
 * CSS-Tokens laeuft (theme/tokens.css). Der Graph horcht zusaetzlich auf
 * data-theme, weil Canvas keine CSS-Variablen kennt.
 */
export function ThemeSchalter() {
  const [theme, setTheme] = useState<ThemeName>("cyberpunk");

  useEffect(() => {
    const gespeichert = themeLesen();
    setTheme(gespeichert);
    themeSetzen(gespeichert);
  }, []);

  function weiter() {
    const i = THEMES.indexOf(theme);
    const naechstes = THEMES[(i + 1) % THEMES.length];
    setTheme(naechstes);
    themeSetzen(naechstes);
  }

  return (
    <button
      type="button"
      className="cl-werkzeug"
      onClick={weiter}
      title={`Aussehen: ${THEME_LABELS[theme]} — klicken zum Wechseln`}
      aria-label={`Aussehen wechseln, aktuell ${THEME_LABELS[theme]}`}
    >
      ◐
    </button>
  );
}
