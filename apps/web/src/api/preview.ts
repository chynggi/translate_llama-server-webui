import { apiFetch } from "./client";
import type { PreviewRequest, PreviewResult } from "../types";

export function preview(body: PreviewRequest): Promise<PreviewResult> {
  return apiFetch<PreviewResult>("/preview", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
