import { describe, expect, it } from "vitest";
import { parseSseBuffer } from "./sse";

describe("parseSseBuffer", () => {
  it("parses JSON data with LF and preserves incomplete events", () => {
    const result = parseSseBuffer('data: {"type":"delta","content":"안녕"}\n\n' + "data: {");
    expect(result.events).toEqual([{ type: "delta", content: "안녕" }]);
    expect(result.rest).toBe("data: {");
  });

  it("parses CRLF events and joins multiple data lines", () => {
    const result = parseSseBuffer('data: {"type":"delta",\r\ndata: "content":"content"}\r\n\r\n');
    expect(result.events).toEqual([{ type: "delta", content: "content" }]);
  });
});
