from __future__ import annotations

import json
from typing import Any


def compact_json(data: Any, *, limit: int = 5000) -> str:
    text = json.dumps(data, ensure_ascii=False, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "... [truncated]"


def recent_chat_history(turns: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Chọn các cặp user/assistant mới nhất trong giới hạn provider-safe."""
    selected: list[dict[str, Any]] = []
    total_chars = 0
    for turn in reversed(turns):
        user_content = str(turn.get("user_content") or "")
        assistant_content = str(turn.get("assistant_content") or "")
        if not user_content or not assistant_content:
            continue
        pair_chars = len(user_content) + len(assistant_content)
        if len(selected) >= 5 or total_chars + pair_chars > 12_000:
            break
        selected.append(turn)
        total_chars += pair_chars

    messages: list[dict[str, str]] = []
    for turn in reversed(selected):
        messages.append({"role": "user", "content": str(turn["user_content"])})
        messages.append(
            {"role": "assistant", "content": str(turn["assistant_content"])}
        )
    return messages
