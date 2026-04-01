from __future__ import annotations

import os
from typing import Literal, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from agentic_debate.context import DebateContext
from agentic_debate.llm.base import LlmCaller  # noqa: F401 — re-exported for type checkers
from agentic_debate.types import DebateParticipant
from backend.constants import ACCENT_COLORS as ACCENT_COLORS  # re-export
from backend.prompts import INTENT_PROMPT, TEAM_PROMPT

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


class _RawIntentResult(BaseModel):
    reframed_topic: str
    domain: str
    controversy_level: str
    recommended_participants: int
    recommended_rounds: int


class IntentResult(BaseModel):
    reframed_topic: str
    domain: str
    controversy_level: Literal["low", "medium", "high"]
    recommended_participants: int = Field(ge=2, le=5)
    recommended_rounds: int = Field(ge=1, le=3)


class _ParticipantRaw(BaseModel):
    participant_id: str
    label: str
    role: str
    stance: str


class _TeamResponse(BaseModel):
    participants: list[_ParticipantRaw]


async def intent_analysis(
    topic: str,
    llm: GeminiLlmCaller,
    context: DebateContext,
) -> IntentResult:
    prompt = INTENT_PROMPT.format(topic=topic)
    raw = await llm.generate_structured(prompt, _RawIntentResult, context=context)
    # Normalize controversy_level to valid values
    valid_levels = {"low", "medium", "high"}
    controversy = raw.controversy_level.lower() if raw.controversy_level.lower() in valid_levels else "medium"
    return IntentResult(
        reframed_topic=raw.reframed_topic,
        domain=raw.domain,
        controversy_level=controversy,  # type: ignore[arg-type]
        recommended_participants=max(2, min(5, raw.recommended_participants)),
        recommended_rounds=max(1, min(3, raw.recommended_rounds)),
    )


async def generate_team(
    intent: IntentResult,
    llm: GeminiLlmCaller,
    context: DebateContext,
) -> list[DebateParticipant]:
    prompt = TEAM_PROMPT.format(
        topic=intent.reframed_topic,
        domain=intent.domain,
        n=intent.recommended_participants,
    )
    raw = await llm.generate_structured(prompt, _TeamResponse, context=context)
    participants = raw.participants[: intent.recommended_participants]
    return [
        DebateParticipant(
            participant_id=p.participant_id,
            label=p.label,
            role=p.role,
            stance=p.stance,
            metadata={"accent_color": ACCENT_COLORS[i % len(ACCENT_COLORS)]},
        )
        for i, p in enumerate(participants)
    ]
