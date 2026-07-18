from __future__ import annotations


class Postprocessor:
    """Minimal MVP post-processing. Kept deliberately conservative so it never
    alters translation content — only removes LLM framing artifacts."""

    def process(self, text: str | None) -> str:
        if not text:
            return ""
        result = text.strip()
        result = self._strip_code_fence(result)
        return result

    def _strip_code_fence(self, text: str) -> str:
        if not text.startswith("```"):
            return text
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
