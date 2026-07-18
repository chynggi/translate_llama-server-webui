from __future__ import annotations

from ..detector.service import DetectedGlossary
from .models import AssembledPrompt, Preset, PromptParts
from .templates import TemplateRepository

GLOSSARY_HEADER = "Glossary"


def format_glossary(detected: DetectedGlossary) -> str:
    """Render only the detected entries, grouped by category."""
    if detected.is_empty():
        return ""
    lines = [GLOSSARY_HEADER, ""]
    for category, entries in detected.categories.items():
        lines.append(f"[{category}]")
        for detected_entry in entries:
            lines.append(f"{detected_entry.entry.source} = {detected_entry.entry.ko}")
        lines.append("")
    return "\n".join(lines).strip()


class PromptBuilder:
    """Assembles the final chat messages in a fixed, predictable order:

    System Rules -> Preset (style) -> Detected Glossary   [system message]
    User Instruction -> Source Text                        [user message]
    """

    def __init__(self, templates: TemplateRepository):
        self._templates = templates

    def build(
        self,
        source: str,
        preset: Preset,
        detected: DetectedGlossary,
        user_instruction: str | None = None,
        model: str | None = None,
    ) -> AssembledPrompt:
        system_rules = self._templates.system_rules()
        preset_rules = preset.system_rules.strip()
        if preset_rules:
            system_rules = f"{system_rules}\n\n{preset_rules}".strip() if system_rules else preset_rules
        glossary_block = format_glossary(detected)
        style = preset.style.strip()
        system_content = "\n\n".join(p for p in (system_rules, style, glossary_block) if p)

        instruction = (user_instruction or preset.user_instruction or "").strip()
        user_content = "\n\n".join(p for p in (instruction, source.strip()) if p)

        messages: list[dict] = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})

        params: dict = {}
        for key in ("temperature", "top_p", "max_tokens"):
            value = getattr(preset, key)
            if value is not None:
                params[key] = value
        params.update(preset.params)

        parts = PromptParts(
            system_rules=system_rules,
            preset=style,
            glossary=glossary_block,
            user_instruction=instruction,
            source=source,
        )
        return AssembledPrompt(
            messages=messages,
            parts=parts,
            detected=detected.to_response(),
            model=(model or preset.model or ""),
            params=params,
        )
