import { describe, expect, it } from "vitest";
import { entriesByCategory, flattenDetected, matchCount } from "./glossaryGroup";
import type { DetectedGlossary } from "../types";

const sample: DetectedGlossary = {
  total: 2,
  categories: {
    students: [{ source: "空崎ヒナ", ko: "소라사키 히나", aliases: ["ヒナ"], occurrences: 1 }],
    locations: [{ source: "ゲヘナ", ko: "게헨나", aliases: [], occurrences: 1 }],
  },
};

describe("glossary grouping helpers", () => {
  it("lists categories in object order", () => {
    expect(entriesByCategory(sample).map(([name]) => name)).toEqual([
      "students",
      "locations",
    ]);
  });

  it("reports total match count", () => {
    expect(matchCount(sample)).toBe(2);
  });

  it("flattens entries across categories", () => {
    expect(flattenDetected(sample).map((e) => e.source)).toEqual([
      "空崎ヒナ",
      "ゲヘナ",
    ]);
  });
});
