"""Single LLM provider abstraction. Default to Claude (latest Anthropic models).

Add a second provider only when a real reason appears — not speculatively.
Kept import-light so the rest of the platform builds without an SDK installed.
"""
from __future__ import annotations

import os
from typing import Protocol

DEFAULT_MODEL = os.getenv("LLM_MODEL", "claude-opus-4-8")


class LLM(Protocol):
    def complete(self, system: str, prompt: str) -> str: ...


class AnthropicLLM:
    """Thin wrapper. Requires `anthropic` + ANTHROPIC_API_KEY to actually call out."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model

    def complete(self, system: str, prompt: str) -> str:
        try:
            import anthropic
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("pip install anthropic to use AnthropicLLM") from exc
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")


def get_llm() -> LLM:
    return AnthropicLLM()
