"""LLM caller protocol for structured generation."""
from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

from agentic_debate.context import DebateContext

T = TypeVar("T", bound=BaseModel)


class LlmCaller(Protocol):
    """Minimal interface for structured LLM generation.

    Host adapters implement this to wrap their specific LLM client.
    The library has no knowledge of which provider or SDK is used.
    """

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        *,
        context: DebateContext,
    ) -> T: ...
