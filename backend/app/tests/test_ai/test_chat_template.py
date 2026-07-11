from __future__ import annotations

from pathlib import Path

from app.modules.ai.prompts import CHAT_SYSTEM_PROMPT


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[4]
    / "docs"
    / "lmstudio-smart-menu-chat-template.jinja"
)


def test_chat_system_prompt_allows_broad_food_and_nutrition_scope():
    normalized_prompt = " ".join(CHAT_SYSTEM_PROMPT.split())

    assert "Bạn là Menuto" in normalized_prompt
    assert "gợi ý món" in normalized_prompt
    assert "kiến thức dinh dưỡng phổ thông" in normalized_prompt
    assert "dù người dùng không nhắc tên Smart Menu" in normalized_prompt
    assert "vì sao Menuto chưa trả lời" in normalized_prompt
    assert "hướng người dùng bấm Retry" in normalized_prompt
    assert "Chỉ từ chối khi yêu cầu rõ ràng không liên quan" in normalized_prompt
    assert "tiết lộ system prompt" in normalized_prompt


def test_lmstudio_template_uses_menuto_identity_without_upstream_branding():
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "set menuto_identity" in template
    assert "Bạn là Menuto" in template
    assert "Qwythos" not in template
    assert "Empero AI" not in template
    assert "structured output" in template
    assert "JSON Schema" in template
    assert "Chấp nhận cả câu hỏi liên quan hoặc tiếp nối" in template
    assert "Chỉ từ chối khi yêu cầu rõ ràng không liên quan" in template
    assert "vì sao Menuto chưa trả lời" in template


def test_lmstudio_template_keeps_original_reasoning_and_capabilities():
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "message.reasoning_content is string" in template
    assert "enable_thinking is defined and enable_thinking is false" in template
    assert "<think>\\n\\n</think>\\n\\n" in template
    assert "<|vision_start|><|image_pad|><|vision_end|>" in template
    assert "<tool_call>" in template
