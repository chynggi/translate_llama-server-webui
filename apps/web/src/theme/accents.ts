export type ThemeMode = "system" | "light" | "dark";
export type ThemeStyle =
  | "default"
  | "tokyo-night"
  | "nord"
  | "dracula"
  | "gruvbox"
  | "synthwave"
  | "soft"
  | "monochrome";
export type ChatWidthStyle = "default" | "wide" | "full";

export interface AccentDefinition {
  light: string;
  dark: string;
  glowLight: string;
  glowDark: string;
}

/** Accent palettes ported from llama.cpp glassy-modernui (lib/constants/ui.ts). */
export const ACCENT_COLORS: Record<string, AccentDefinition> = {
  default: {
    light: "oklch(0.93 0.04 220)",
    dark: "oklch(0.4 0.2 220)",
    glowLight: "oklch(0.6 0.22 220)",
    glowDark: "oklch(0.85 0.22 220)",
  },
  blue: {
    light: "oklch(0.93 0.04 250)",
    dark: "oklch(0.3 0.14 250)",
    glowLight: "oklch(0.6 0.18 250)",
    glowDark: "oklch(0.85 0.14 250)",
  },
  green: {
    light: "oklch(0.94 0.04 145)",
    dark: "oklch(0.32 0.14 145)",
    glowLight: "oklch(0.65 0.18 145)",
    glowDark: "oklch(0.85 0.14 145)",
  },
  purple: {
    light: "oklch(0.92 0.05 290)",
    dark: "oklch(0.3 0.15 290)",
    glowLight: "oklch(0.58 0.2 290)",
    glowDark: "oklch(0.82 0.15 290)",
  },
  orange: {
    light: "oklch(0.93 0.05 55)",
    dark: "oklch(0.32 0.14 55)",
    glowLight: "oklch(0.65 0.18 55)",
    glowDark: "oklch(0.85 0.14 55)",
  },
  pink: {
    light: "oklch(0.93 0.05 350)",
    dark: "oklch(0.32 0.14 350)",
    glowLight: "oklch(0.65 0.18 350)",
    glowDark: "oklch(0.85 0.14 350)",
  },
  red: {
    light: "oklch(0.92 0.05 25)",
    dark: "oklch(0.3 0.14 25)",
    glowLight: "oklch(0.6 0.18 25)",
    glowDark: "oklch(0.82 0.14 25)",
  },
};

export const ACCENT_OPTIONS = [
  { value: "default", label: "Default" },
  { value: "blue", label: "Blue" },
  { value: "green", label: "Green" },
  { value: "purple", label: "Purple" },
  { value: "orange", label: "Orange" },
  { value: "pink", label: "Pink" },
  { value: "red", label: "Red" },
] as const;

export const THEME_STYLE_OPTIONS: { value: ThemeStyle; label: string }[] = [
  { value: "default", label: "Default" },
  { value: "tokyo-night", label: "Tokyo Night" },
  { value: "nord", label: "Nord" },
  { value: "dracula", label: "Dracula" },
  { value: "gruvbox", label: "Gruvbox" },
  { value: "synthwave", label: "Synthwave '84" },
  { value: "soft", label: "Soft (Gradio)" },
  { value: "monochrome", label: "Monochrome (Gradio)" },
];

/** Browser-side preferences. Keys mirror the llama webui settings export. */
export interface Prefs {
  theme: ThemeMode;
  themeStyle: ThemeStyle;
  accentColor: string;
  chatWidthStyle: ChatWidthStyle;
  sendOnEnter: boolean;
  showMessageStats: boolean;
  showThoughtInProgress: boolean;
  autoExpandThinking: boolean;
  renderUserContentAsMarkdown: boolean;
}

/** Defaults adopted from llama_settings_2026-07-17.json. */
export const DEFAULT_PREFS: Prefs = {
  theme: "system",
  themeStyle: "dracula",
  accentColor: "blue",
  chatWidthStyle: "full",
  sendOnEnter: true,
  showMessageStats: true,
  showThoughtInProgress: true,
  autoExpandThinking: false,
  renderUserContentAsMarkdown: true,
};
