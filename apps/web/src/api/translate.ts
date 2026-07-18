import { apiFetch } from "./client";
import type { TranslateRequest, TranslateResult } from "../types";

export function translate(body: TranslateRequest): Promise<TranslateResult> {
  return apiFetch<TranslateResult>("/translate", {
    method: "POST",
    body: JSON.stringify({ ...body, stream: false }),
  });
}

export { streamTranslate } from "./sse";
