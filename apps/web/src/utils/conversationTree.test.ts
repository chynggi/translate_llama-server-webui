import { describe, expect, it } from "vitest";
import type { ConversationMessage } from "../types";
import {
  activePath,
  descendToLeaf,
  leafForBranch,
  rootOf,
  siblingPosition,
  siblingsOf,
} from "./conversationTree";

function msg(
  id: string,
  parent: string | null,
  role: string,
  content: string,
  timestamp: number,
  children: string[] = []
): ConversationMessage {
  return {
    id,
    convId: "conv",
    type: parent === null ? "root" : "text",
    timestamp,
    role,
    content,
    parent,
    children,
  };
}

// root -> u1 -> a1 (older)
//             \- a2 (newer) -> u2 -> a3
function sampleTree(): ConversationMessage[] {
  return [
    msg("root", null, "system", "SYS", 1, ["u1"]),
    msg("u1", "root", "user", "질문", 2, ["a1", "a2"]),
    msg("a1", "u1", "assistant", "답변 A", 3),
    msg("a2", "u1", "assistant", "답변 B", 4, ["u2"]),
    msg("u2", "a2", "user", "후속", 5, ["a3"]),
    msg("a3", "u2", "assistant", "후속 답변", 6),
  ];
}

describe("conversationTree", () => {
  it("finds the root", () => {
    expect(rootOf(sampleTree())?.id).toBe("root");
  });

  it("resolves the active path root-first", () => {
    const path = activePath(sampleTree(), "a3");
    expect(path.map((m) => m.id)).toEqual(["root", "u1", "a2", "u2", "a3"]);
  });

  it("lists siblings sorted by timestamp", () => {
    const siblings = siblingsOf(sampleTree(), "a2");
    expect(siblings.map((m) => m.id)).toEqual(["a1", "a2"]);
  });

  it("reports 1-based sibling positions", () => {
    expect(siblingPosition(sampleTree(), "a2")).toEqual({ index: 2, count: 2 });
    expect(siblingPosition(sampleTree(), "a1")).toEqual({ index: 1, count: 2 });
    expect(siblingPosition(sampleTree(), "u1")).toEqual({ index: 1, count: 1 });
  });

  it("descends to the newest leaf when switching branches", () => {
    expect(descendToLeaf(sampleTree(), "u1")?.id).toBe("a3");
    expect(leafForBranch(sampleTree(), "a1")?.id).toBe("a1");
    expect(leafForBranch(sampleTree(), "a2")?.id).toBe("a3");
  });

  it("handles dangling references gracefully", () => {
    const broken = [msg("root", null, "system", "", 1, ["ghost"])];
    expect(descendToLeaf(broken, "root")?.id).toBe("root");
    expect(activePath(broken, "ghost")).toEqual([]);
  });
});
