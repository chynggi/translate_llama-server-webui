import type { ConversationMessage } from "../types";

/**
 * Pure helpers over the llama.app message tree (parent/children links).
 * Mirrors the middleware's conversations.service helpers.
 */

export function indexById(
  messages: ConversationMessage[]
): Map<string, ConversationMessage> {
  return new Map(messages.map((m) => [m.id, m]));
}

export function rootOf(
  messages: ConversationMessage[]
): ConversationMessage | undefined {
  return messages.find((m) => m.parent === null) ?? messages[0];
}

/** Walk parents from `leafId` up to the root; returns root-first order. */
export function activePath(
  messages: ConversationMessage[],
  leafId: string | null | undefined
): ConversationMessage[] {
  const byId = indexById(messages);
  const path: ConversationMessage[] = [];
  const seen = new Set<string>();
  let node = leafId ? byId.get(leafId) : undefined;
  while (node && !seen.has(node.id)) {
    seen.add(node.id);
    path.push(node);
    node = node.parent ? byId.get(node.parent) : undefined;
  }
  return path.reverse();
}

/** All messages sharing the same parent (roots share parent === null). */
export function siblingsOf(
  messages: ConversationMessage[],
  nodeId: string
): ConversationMessage[] {
  const byId = indexById(messages);
  const node = byId.get(nodeId);
  if (!node) return [];
  return messages
    .filter((m) => m.parent === node.parent)
    .sort(byTimestampThenId);
}

function byTimestampThenId(
  a: ConversationMessage,
  b: ConversationMessage
): number {
  if (a.timestamp !== b.timestamp) return a.timestamp - b.timestamp;
  return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

/** 1-based position of `nodeId` among its siblings. */
export function siblingPosition(
  messages: ConversationMessage[],
  nodeId: string
): { index: number; count: number } {
  const siblings = siblingsOf(messages, nodeId);
  const index = siblings.findIndex((m) => m.id === nodeId);
  return { index: index < 0 ? 0 : index + 1, count: siblings.length };
}

/**
 * Deepest descendant of `nodeId`, preferring the newest child at each step
 * (llama webui branch-switch behaviour).
 */
export function descendToLeaf(
  messages: ConversationMessage[],
  nodeId: string
): ConversationMessage | undefined {
  const byId = indexById(messages);
  const start = byId.get(nodeId);
  if (!start) return undefined;
  let current: ConversationMessage = start;
  while (current.children.length > 0) {
    const candidates: ConversationMessage[] = current.children
      .map((id) => byId.get(id))
      .filter((m): m is ConversationMessage => m !== undefined);
    if (candidates.length === 0) break;
    current = candidates.reduce((newest, m) =>
      m.timestamp > newest.timestamp ||
      (m.timestamp === newest.timestamp && m.id > newest.id)
        ? m
        : newest
    );
  }
  return current;
}

/** Resolve the branch to display when switching to `siblingId`. */
export function leafForBranch(
  messages: ConversationMessage[],
  siblingId: string
): ConversationMessage | undefined {
  return descendToLeaf(messages, siblingId);
}
