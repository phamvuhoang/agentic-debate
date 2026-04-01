"""Tests for the built-in LLM planner and prompt helpers."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from agentic_debate.context import DebateContext
from agentic_debate.errors import DebatePlanningError
from agentic_debate.planning.llm import LlmDebatePlanner
from agentic_debate.prompts import (
    PlanningPromptSet,
    load_builtin_judge_prompt,
    load_builtin_planning_prompt_set,
)


def test_builtin_planning_prompt_set_exposes_required_templates() -> None:
    prompt_set = load_builtin_planning_prompt_set()

    assert "{topic}" in prompt_set.intent_prompt_template
    assert "{topic}" in prompt_set.team_prompt_template
    assert "{reframed_topic}" in prompt_set.team_prompt_template
    assert "{domain}" in prompt_set.team_prompt_template
    assert "{controversy_level}" in prompt_set.team_prompt_template
    assert "{participant_count}" in prompt_set.team_prompt_template
    assert "{round_count}" in prompt_set.team_prompt_template
    assert "{winning_options_json}" in load_builtin_judge_prompt()


@pytest.mark.asyncio
async def test_llm_debate_planner_normalizes_intent_and_returns_plan() -> None:
    # _FakePlannerCaller returns an invalid controversy level so normalization
    # to "medium" is covered by the test rather than assumed.
    planner = LlmDebatePlanner(llm=_FakePlannerCaller())
    plan = await planner.plan_topic(
        "should ai replace doctors",
        context=DebateContext(namespace="test"),
    )

    assert plan.intent.controversy_level == "medium"
    assert len(plan.participants) == 5
    assert plan.round_policy.max_rounds == 1
    assert plan.round_policy.mode == "round_robin"


@pytest.mark.asyncio
async def test_llm_debate_planner_wraps_intent_failures() -> None:
    planner = LlmDebatePlanner(llm=_ExplodingCaller())

    with pytest.raises(DebatePlanningError) as exc:
        await planner.plan_topic("topic", context=DebateContext(namespace="test"))

    assert exc.value.stage == "intent_analysis"


@pytest.mark.asyncio
async def test_llm_debate_planner_wraps_participant_generation_failures() -> None:
    planner = LlmDebatePlanner(llm=_IntentThenExplodeCaller())

    with pytest.raises(DebatePlanningError) as exc:
        await planner.plan_topic("topic", context=DebateContext(namespace="test"))

    assert exc.value.stage == "participant_generation"


@pytest.mark.asyncio
async def test_llm_debate_planner_rejects_too_few_participants() -> None:
    planner = LlmDebatePlanner(llm=_TooFewParticipantsCaller())

    with pytest.raises(DebatePlanningError) as exc:
        await planner.plan_topic("topic", context=DebateContext(namespace="test"))

    assert exc.value.stage == "participant_generation"
    assert "at least 2 participants" in str(exc.value)


@pytest.mark.asyncio
async def test_llm_debate_planner_rejects_duplicate_participant_ids() -> None:
    planner = LlmDebatePlanner(llm=_DuplicateParticipantsCaller())

    with pytest.raises(DebatePlanningError) as exc:
        await planner.plan_topic("topic", context=DebateContext(namespace="test"))

    assert exc.value.stage == "participant_generation"
    assert "unique participant_id" in str(exc.value)


@pytest.mark.asyncio
async def test_llm_debate_planner_uses_custom_prompt_set() -> None:
    prompt_set = PlanningPromptSet(
        intent_prompt_template="intent::{topic}",
        team_prompt_template=(
            "team::{topic}::{reframed_topic}::{domain}::"
            "{controversy_level}::{participant_count}::{round_count}"
        ),
    )
    caller = _CapturingPlannerCaller()
    planner = LlmDebatePlanner(llm=caller, prompt_set=prompt_set)

    await planner.plan_topic("custom topic", context=DebateContext(namespace="test"))

    assert caller.prompts == [
        "intent::custom topic",
        "team::custom topic::Topic::general::low::2::1",
    ]


@dataclass
class _FakePlannerCaller:
    call_count: int = 0

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        self.call_count += 1
        if self.call_count == 1:
            return response_model.model_validate(
                {
                    "reframed_topic": "Should AI replace doctors?",
                    "domain": "healthcare",
                    "controversy_level": "banana",
                    "recommended_participants": 99,
                    "recommended_rounds": 0,
                }
            )

        return response_model.model_validate(
            {
                "participants": [
                    {"participant_id": f"p{i}", "label": f"Person {i}", "role": "expert", "stance": "stance"}
                    for i in range(6)
                ]
            }
        )


class _ExplodingCaller:
    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        raise RuntimeError("intent failed")


@dataclass
class _IntentThenExplodeCaller:
    call_count: int = 0

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        self.call_count += 1
        if self.call_count == 1:
            return response_model.model_validate(
                {
                    "reframed_topic": "Topic",
                    "domain": "general",
                    "controversy_level": "low",
                    "recommended_participants": 3,
                    "recommended_rounds": 1,
                }
            )
        raise RuntimeError("team failed")


@dataclass
class _TooFewParticipantsCaller:
    call_count: int = 0

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        self.call_count += 1
        if self.call_count == 1:
            return response_model.model_validate(
                {
                    "reframed_topic": "Topic",
                    "domain": "general",
                    "controversy_level": "low",
                    "recommended_participants": 2,
                    "recommended_rounds": 1,
                }
            )

        return response_model.model_validate(
            {
                "participants": [
                    {"participant_id": "only_one", "label": "Only One", "role": "expert", "stance": "stance"}
                ]
            }
        )


@dataclass
class _DuplicateParticipantsCaller:
    call_count: int = 0

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        self.call_count += 1
        if self.call_count == 1:
            return response_model.model_validate(
                {
                    "reframed_topic": "Topic",
                    "domain": "general",
                    "controversy_level": "low",
                    "recommended_participants": 2,
                    "recommended_rounds": 1,
                }
            )

        return response_model.model_validate(
            {
                "participants": [
                    {"participant_id": "dup", "label": "Person A", "role": "expert", "stance": "stance"},
                    {"participant_id": "dup", "label": "Person B", "role": "expert", "stance": "stance"},
                ]
            }
        )


@dataclass
class _CapturingPlannerCaller:
    prompts: list[str] | None = None
    call_count: int = 0

    def __post_init__(self) -> None:
        if self.prompts is None:
            self.prompts = []

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        assert self.prompts is not None
        self.prompts.append(prompt)
        self.call_count += 1
        if self.call_count == 1:
            return response_model.model_validate(
                {
                    "reframed_topic": "Topic",
                    "domain": "general",
                    "controversy_level": "low",
                    "recommended_participants": 2,
                    "recommended_rounds": 1,
                }
            )
        return response_model.model_validate(
            {
                "participants": [
                    {"participant_id": "a", "label": "A", "role": "expert", "stance": "stance"},
                    {"participant_id": "b", "label": "B", "role": "expert", "stance": "stance"},
                ]
            }
        )
