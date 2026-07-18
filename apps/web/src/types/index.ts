export interface GlossaryEntry {
  source: string;
  ko: string;
  aliases: string[];
}

export interface GlossaryCategory {
  name: string;
  entries: GlossaryEntry[];
}

export interface GlossaryResponse {
  categories: GlossaryCategory[];
  total_entries: number;
}

export interface DetectedEntry {
  source: string;
  ko: string;
  aliases: string[];
  occurrences: number;
}

export interface DetectedGlossary {
  categories: Record<string, DetectedEntry[]>;
  total: number;
}

export interface Preset {
  id: string;
  name: string;
  description: string;
  system_rules: string;
  style: string;
  user_instruction: string;
  model: string;
  temperature: number | null;
  top_p: number | null;
  max_tokens: number | null;
  params: Record<string, unknown>;
}

export interface ChatMessage {
  role: string;
  content: string;
}

export interface TranslateRequest {
  source: string;
  preset: string;
  glossary_set?: string[] | null;
  user_instruction?: string | null;
  model?: string | null;
  stream?: boolean;
  params?: Record<string, unknown>;
}

export interface TranslateResult {
  id: string;
  output: string;
  raw_output: string;
  detected: DetectedGlossary;
  messages?: ChatMessage[];
  model: string;
  preset: string;
  tokens: Record<string, number>;
}

export interface PreviewRequest {
  source: string;
  preset: string;
  glossary_set?: string[] | null;
  user_instruction?: string | null;
  model?: string | null;
}

export interface PromptParts {
  system_rules: string;
  preset: string;
  glossary: string;
  user_instruction: string;
  source: string;
}

export interface PreviewResult {
  messages: ChatMessage[];
  parts: PromptParts;
  detected: DetectedGlossary;
  token_count: number;
  model: string;
  preset: string;
}

export interface LogRecord {
  id: string;
  ts: string;
  source: string;
  preset: string;
  model: string;
  detected: DetectedGlossary;
  prompt: ChatMessage[];
  raw_output: string;
  output: string;
  tokens: Record<string, number>;
}

export interface LogsResponse {
  items: LogRecord[];
  total: number;
}

export interface ModelList {
  data: { id: string; object: string }[];
}
