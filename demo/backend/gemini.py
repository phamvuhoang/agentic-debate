from __future__ import annotations

import os
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from agentic_debate.context import DebateContext
from agentic_debate.llm.base import LlmCaller  # noqa: F401 — re-exported for type checkers

T = TypeVar("T", bound=BaseModel)

MODEL = "gemini-3-flash-preview"


class GeminiLlmCaller:
    """Implements LlmCaller using google-genai async client."""

    def __init__(
        self,
        client: genai.Client | None = None,
        model: str = MODEL,
    ) -> None:
        self._client = client or genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self._model = model

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        *,
        context: DebateContext,
    ) -> T:
        _ = context
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        if response.text is None:
            raise ValueError(
                f"Gemini returned no text. "
                f"finish_reason={getattr(getattr(response, 'candidates', [{}])[0], 'finish_reason', 'unknown')!r}"
            )
        return response_model.model_validate_json(response.text)

    async def generate_text(
        self,
        prompt: str,
        *,
        context: DebateContext,
    ) -> str:
        _ = context
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        if response.text is None:
             raise ValueError("Gemini returned no text.")
        return response.text.strip()


class GeminiLocalizer:
    """Implements OutputLocalizer using Gemini."""

    def __init__(self, llm: GeminiLlmCaller) -> None:
        self._llm = llm

    async def localize(
        self,
        text: str,
        target_locale: str,
        context: DebateContext,
    ) -> str:
        if not text or target_locale == "en":
            return text
        from backend.prompts import TRANSLATION_PROMPT
        prompt = TRANSLATION_PROMPT.format(locale=target_locale, text=text)
        return await self._llm.generate_text(prompt, context=context)
