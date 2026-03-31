from __future__ import annotations

import os
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from agentic_debate.context import DebateContext

T = TypeVar("T", bound=BaseModel)

MODEL = "gemini-3-flash-preview"
ACCENT_COLORS = ["#4F86C6", "#E05A5A", "#4CAF50", "#F5A623", "#9B59B6"]


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
        return response_model.model_validate_json(response.text)
