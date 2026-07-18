import { apiFetch } from "./client";
import type { LogsResponse } from "../types";

export function getLogs(limit = 50, offset = 0): Promise<LogsResponse> {
  return apiFetch<LogsResponse>(`/logs?limit=${limit}&offset=${offset}`);
}
