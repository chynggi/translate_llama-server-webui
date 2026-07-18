from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class TranslationLogger:
    """Appends one JSONL record per translation so a translation can always be
    traced: source -> prompt -> raw output -> final output."""

    def __init__(self, logs_dir: str | Path, filename: str = "translations.jsonl"):
        self._path = Path(logs_dir) / filename
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        *,
        source: str,
        preset: str,
        model: str,
        detected: dict,
        prompt: list[dict],
        raw_output: str,
        output: str,
        tokens: dict,
    ) -> dict:
        record = {
            "id": uuid.uuid4().hex,
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "preset": preset,
            "model": model,
            "detected": detected,
            "prompt": prompt,
            "raw_output": raw_output,
            "output": output,
            "tokens": tokens,
        }
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def list(self, limit: int = 50, offset: int = 0) -> dict:
        if not self._path.exists():
            return {"items": [], "total": 0}
        records: list[dict] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        records.reverse()  # newest first
        return {"items": records[offset : offset + limit], "total": len(records)}
