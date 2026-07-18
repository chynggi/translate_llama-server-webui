import { apiFetch } from "./client";
import type { Preset } from "../types";

export function getPresets(): Promise<{ presets: Preset[] }> {
  return apiFetch<{ presets: Preset[] }>("/presets");
}
