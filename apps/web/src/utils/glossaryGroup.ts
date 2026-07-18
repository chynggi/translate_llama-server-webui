import type { DetectedEntry, DetectedGlossary } from "../types";

export function entriesByCategory(
  detected: DetectedGlossary
): [string, DetectedEntry[]][] {
  return Object.entries(detected.categories);
}

export function matchCount(detected: DetectedGlossary): number {
  return detected.total;
}

export function flattenDetected(detected: DetectedGlossary): DetectedEntry[] {
  return entriesByCategory(detected).flatMap(([, entries]) => entries);
}
