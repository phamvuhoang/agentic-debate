"""LLM-backed single-judge arbitrator."""
from __future__ import annotations

import json
from typing import Any, Callable

from pydantic import BaseModel

from agentic_debate.context import DebateContext
from agentic_debate.llm.base import LlmCaller
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateArbitration, DebateTopicGroup, DebateVerdict


class _VerdictItem(BaseModel):
    topic: str
    winning_participant_id: str
    confidence: float
    rationale: str
    open_questions: list[str] = []
    consensus_level: str = "moderate"


class _JudgeOutput(BaseModel):
    verdicts: list[_VerdictItem]
    debate_summary: str
    contested_topics: list[str] = []


class LlmSingleJudgeArbitrator:
    """LLM-backed arbitrator using a single judge model call.

    Standard prompt template variables:
      {challenges_json}       — serialized challenge list
      {participants_json}     — serialized participant list
      {winning_options_json}  — valid winning_participant_id values

    Additional variables can be injected via extra_format_vars, a callable
    that receives (spec, context) and returns extra {key: value} pairs to
    merge before formatting the prompt. Use this to inject host-specific
    context (e.g., memos) without modifying the library API.
    """

    def __init__(
        self,
        llm: LlmCaller,
        prompt_template: str,
        extra_format_vars: Callable[
            [DebateSpec, DebateContext], dict[str, Any]
        ] | None = None,
    ) -> None:
        self._llm = llm
        self._prompt_template = prompt_template
        self._extra_format_vars = extra_format_vars

    async def arbitrate(
        self,
        groups: list[DebateTopicGroup],
        spec: DebateSpec,
        context: DebateContext,
    ) -> DebateArbitration:
        participant_ids = {p.participant_id for p in spec.participants}
        winning_options = sorted(participant_ids) + ["unresolved"]
        challenge_dicts = [
            {
                "topic": c.topic,
                "challenger_id": c.challenger_id,
                "target_id": c.target_id,
                "challenge_text": c.challenge_text,
                "confidence": c.confidence,
            }
            for group in groups
            for c in group.challenges
        ]
        format_vars: dict[str, Any] = {
            "challenges_json": json.dumps(challenge_dicts),
            "participants_json": json.dumps([p.model_dump() for p in spec.participants]),
            "winning_options_json": json.dumps(winning_options),
        }
        if self._extra_format_vars is not None:
            format_vars.update(self._extra_format_vars(spec, context))

        prompt = self._prompt_template.format(**format_vars)
        output: _JudgeOutput = await self._llm.generate_structured(
            prompt, _JudgeOutput, context=context
        )
        verdicts = [
            DebateVerdict(
                topic=item.topic,
                winning_participant_id=(
                    item.winning_participant_id
                    if item.winning_participant_id in participant_ids
                    or item.winning_participant_id == "unresolved"
                    else "unresolved"
                ),
                confidence=item.confidence,
                rationale=item.rationale,
                open_questions=list(item.open_questions),
                consensus_level=item.consensus_level,  # type: ignore[arg-type]
            )
            for item in output.verdicts
        ]
        contested = [v.topic for v in verdicts if v.consensus_level == "contested"]
        return DebateArbitration(
            verdicts=verdicts,
            summary=output.debate_summary,
            contested_topics=contested,
            metadata={"source": "llm_single_judge", "namespace": spec.namespace},
        )
