import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";
import { ACCENT_COLORS, DEFAULT_PREFS } from "./accents";
import type { Prefs } from "./accents";

const STORAGE_KEY = "ts_studio_prefs";

interface PrefsContextValue {
  prefs: Prefs;
  setPref: <K extends keyof Prefs>(key: K, value: Prefs[K]) => void;
  resolvedDark: boolean;
}

const PrefsContext = createContext<PrefsContextValue | null>(null);

function loadPrefs(): Prefs {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_PREFS, ...(JSON.parse(raw) as Partial<Prefs>) };
  } catch {
    // corrupted storage -> fall back to defaults
  }
  return DEFAULT_PREFS;
}

export function PrefsProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Prefs>(loadPrefs);
  const [systemDark, setSystemDark] = useState<boolean>(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-color-scheme: dark)").matches === true
  );

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (event: MediaQueryListEvent) => setSystemDark(event.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const resolvedDark =
    prefs.theme === "dark" || (prefs.theme === "system" && systemDark);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    const root = document.documentElement;
    root.classList.toggle("dark", resolvedDark);
    for (const cls of Array.from(root.classList)) {
      if (cls.startsWith("theme-")) root.classList.remove(cls);
    }
    if (prefs.themeStyle !== "default") {
      root.classList.add(`theme-${prefs.themeStyle}`);
    }
    root.classList.toggle("wide-chat-mode", prefs.chatWidthStyle === "wide");
    root.classList.toggle("full-chat-mode", prefs.chatWidthStyle === "full");

    // Theme-style CSS owns palette + glow; only pin accent/glow inline when the
    // user picks a non-default accent or the default palette is active.
    const accent = ACCENT_COLORS[prefs.accentColor] ?? ACCENT_COLORS.default;
    const pinInline =
      prefs.accentColor !== "default" || prefs.themeStyle === "default";
    if (pinInline) {
      root.style.setProperty("--accent-light", accent.light);
      root.style.setProperty("--accent-dark", accent.dark);
      root.style.setProperty("--glow-color-light", accent.glowLight);
      root.style.setProperty("--glow-color-dark", accent.glowDark);
    } else {
      root.style.removeProperty("--accent-light");
      root.style.removeProperty("--accent-dark");
      root.style.removeProperty("--glow-color-light");
      root.style.removeProperty("--glow-color-dark");
    }
  }, [prefs, resolvedDark]);

  const setPref = useCallback(
    <K extends keyof Prefs>(key: K, value: Prefs[K]) => {
      setPrefs((current) => ({ ...current, [key]: value }));
    },
    []
  );

  const value = useMemo(
    () => ({ prefs, setPref, resolvedDark }),
    [prefs, setPref, resolvedDark]
  );

  return <PrefsContext.Provider value={value}>{children}</PrefsContext.Provider>;
}

export function usePrefs(): PrefsContextValue {
  const context = useContext(PrefsContext);
  if (!context) throw new Error("usePrefs must be used within PrefsProvider");
  return context;
}
