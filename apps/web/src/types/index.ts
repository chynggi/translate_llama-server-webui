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

/* ---------------------------------------------------------------------------
 * Conversations — llama.app JSONL tree format (session + messages)
 * ------------------------------------------------------------------------- */

export interface MessageTimings {
  cache_n?: number;
  prompt_n?: number;
  prompt_ms?: number;
  prompt_per_token_ms?: number;
  prompt_per_second?: number;
  predicted_n?: number;
  predicted_ms?: number;
  predicted_per_token_ms?: number;
  predicted_per_second?: number;
  draft_n?: number;
  draft_n_accepted?: number;
  [key: string]: unknown; // future llama.cpp timing keys
}

export interface MessageExtra {
  type: string;
  [key: string]: unknown;
}

export interface ConversationMessage {
  id: string;
  convId: string;
  type: string; // "root" | "text" | "system"
  timestamp: number;
  role: string; // "system" | "user" | "assistant"
  content: string;
  parent: string | null;
  children: string[];
  extra?: MessageExtra[];
  model?: string;
  completionId?: string;
  reasoningContent?: string;
  timings?: MessageTimings;
}

export interface ConversationSession {
  id: string;
  name: string;
  lastModified: number;
  currNode: string | null;
  thinkingEnabled: boolean;
  harness: string;
}

export interface ConversationDetail {
  session: ConversationSession;
  messages: ConversationMessage[];
}

export interface ConversationListResponse {
  conversations: ConversationSession[];
}

export interface AppendMessageRequest {
  parent: string;
  role: string;
  content: string;
  type?: string;
  extra?: MessageExtra[];
  model?: string;
  completionId?: string;
  reasoningContent?: string;
  timings?: MessageTimings;
  id?: string;
  timestamp?: number;
}

export interface AppendMessageResponse {
  session: ConversationSession;
  message: ConversationMessage;
}

/** Translation pipeline metadata attached to assistant messages via extra. */
export interface TranslationMeta extends MessageExtra {
  type: "TRANSLATION_META";
  preset: string;
  log_id?: string;
  detected?: DetectedGlossary;
  messages?: ChatMessage[];
  tokens?: Record<string, number>;
}

export function translationMetaOf(
  message: ConversationMessage
): TranslationMeta | undefined {
  return message.extra?.find(
    (item): item is TranslationMeta => item.type === "TRANSLATION_META"
  );
}
