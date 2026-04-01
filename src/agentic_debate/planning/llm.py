"""LLM-backed planning helpers."""

from __future__ import annotations

from pydantic import BaseModel

from agentic_debate.context import DebateContext
from agentic_debate.errors import DebatePlanningError
from agentic_debate.llm.base import LlmCaller
from agentic_debate.planning.types import DebateIntent, DebatePlan, PlannedParticipant
from agentic_debate.prompts import PlanningPromptSet, load_builtin_planning_prompt_set
from agentic_debate.spec import RoundPolicy


class _RawIntentResult(BaseModel):
    reframed_topic: str
    domain: str
    controversy_level: str
    recommended_participants: int
    recommended_rounds: int


class _ParticipantRaw(BaseModel):
    participant_id: str
    label: str
    role: str
    stance: str | None = None


class _TeamResponse(BaseModel):
    participants: list[_ParticipantRaw]


def _normalize_controversy(level: str) -> str:
    normalized = level.lower()
    return normalized if normalized in {"low", "medium", "high"} else "medium"


class LlmDebatePlanner:
    """Build a runnable debate plan from a raw topic using an LLM caller."""

    def __init__(
        self,
        *,
        llm: LlmCaller,
        prompt_set: PlanningPromptSet | None = None,
    ) -> None:
        self._llm = llm
        self._prompt_set = prompt_set or load_builtin_planning_prompt_set()

    async def plan_topic(self, topic: str, *, context: DebateContext) -> DebatePlan:
        try:
            raw_intent = await self._llm.generate_structured(
                self._prompt_set.intent_prompt_template.format(topic=topic),
                _RawIntentResult,
                context=context,
            )
        except Exception as exc:
            raise DebatePlanningError(stage="intent_analysis", message=str(exc)) from exc

        intent = DebateIntent(
            reframed_topic=raw_intent.reframed_topic,
            domain=raw_intent.domain,
            controversy_level=_normalize_controversy(raw_intent.controversy_level),  # type: ignore[arg-type]
            recommended_participants=max(2, min(5, raw_intent.recommended_participants)),
            recommended_rounds=max(1, min(3, raw_intent.recommended_rounds)),
        )

        try:
            raw_team = await self._llm.generate_structured(
                self._prompt_set.team_prompt_template.format(
                    topic=topic,
                    reframed_topic=intent.reframed_topic,
                    domain=intent.domain,
                    controversy_level=intent.controversy_level,
                    participant_count=intent.recommended_participants,
                    round_count=intent.recommended_rounds,
                ),
                _TeamResponse,
                context=context,
            )
        except Exception as exc:
            raise DebatePlanningError(stage="participant_generation", message=str(exc)) from exc

        participants = [
            PlannedParticipant(
                participant_id=participant.participant_id,
                label=participant.label,
                role=participant.role,
                stance=participant.stance,
            )
            for participant in raw_team.participants[: intent.recommended_participants]
        ]
        if len(participants) < 2:
            raise DebatePlanningError(
                stage="participant_generation",
                message="at least 2 participants required, LLM returned fewer",
            )

        participant_ids = [participant.participant_id for participant in participants]
        if len(set(participant_ids)) != len(participant_ids):
            raise DebatePlanningError(
                stage="participant_generation",
                message="participant_generation requires unique participant_id values",
            )

        return DebatePlan(
            topic=topic,
            intent=intent,
            participants=participants,
            round_policy=RoundPolicy(
                mode="round_robin",
                max_rounds=intent.recommended_rounds,
            ),
        )
