import { apiFetch } from "./client";

/** llama.cpp sampling values; null means "not sent". */
export type GenerationValues = Record<string, number | string | null>;

export interface ChatFlags {
  enable_thinking: boolean;
  exclude_reasoning_from_context: boolean;
  system_prompt_file: string;
}

export interface PublicSettings {
  llama_server: {
    base_url: string;
    default_model: string;
    request_timeout: number;
    api_key_set: boolean;
  };
  detector: {
    min_alias_length: number;
    longest_match_first: boolean;
  };
  generation: GenerationValues;
  chat: ChatFlags;
}

export interface SettingsUpdate {
  llama_server?: {
    base_url?: string;
    api_key?: string;
    default_model?: string;
    request_timeout?: number;
  };
  detector?: {
    min_alias_length?: number;
    longest_match_first?: boolean;
  };
  generation?: GenerationValues;
  chat?: Partial<ChatFlags>;
  persist?: boolean;
}

export function getSettings(): Promise<PublicSettings> {
  return apiFetch<PublicSettings>("/settings");
}

export function updateSettings(body: SettingsUpdate): Promise<PublicSettings> {
  return apiFetch<PublicSettings>("/settings", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}
