"""Tests for the built-in LLM challenge source."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from agentic_debate.context import DebateContext
from agentic_debate.errors import DebateConfigurationError, DebateGenerationError
from agentic_debate.methods.rounds.llm import LlmChallengeSource
from agentic_debate.prompts import ChallengePromptSet
from agentic_debate.spec import DebateSpec, RoundPolicy
from agentic_debate.types import DebateChallenge, DebateParticipant, DebateSubject


def _make_spec(mode: str = "round_robin", max_rounds: int = 2) -> DebateSpec:
    return DebateSpec(
        namespace="test",
        subject=DebateSubject(kind="open_question", title="Test topic"),
        participants=[
            DebateParticipant(
                participant_id=f"p{i}",
                label=f"Person {i}",
                role="debater",
                stance=f"Stance {i}",
            )
            for i in range(3)
        ],
        round_policy=RoundPolicy(mode=mode, max_rounds=max_rounds),
    )


@pytest.mark.asyncio
async def test_llm_challenge_source_round_robin_generates_one_turn_per_participant() -> None:
    source = LlmChallengeSource(llm=_FakeChallengeCaller())
    challenges = await source.collect(
        _make_spec(mode="round_robin", max_rounds=2),
        DebateContext(namespace="test"),
    )

    assert len(challenges) == 6
    assert challenges[0].challenger_id == "p0"
    assert challenges[0].target_id == "p1"


@pytest.mark.asyncio
async def test_llm_challenge_source_pairwise_generates_all_pairs() -> None:
    source = LlmChallengeSource(llm=_FakeChallengeCaller())
    challenges = await source.collect(
        _make_spec(mode="pairwise", max_rounds=1),
        DebateContext(namespace="test"),
    )

    assert {(c.challenger_id, c.target_id) for c in challenges} == {
        ("p0", "p1"),
        ("p0", "p2"),
        ("p1", "p0"),
        ("p1", "p2"),
        ("p2", "p0"),
        ("p2", "p1"),
    }


@pytest.mark.asyncio
async def test_llm_challenge_source_pairwise_repeats_pairs_each_round() -> None:
    source = LlmChallengeSource(llm=_FakeChallengeCaller())
    challenges = await source.collect(
        _make_spec(mode="pairwise", max_rounds=2),
        DebateContext(namespace="test"),
    )

    assert len(challenges) == 12
    assert {c.round_index for c in challenges} == {1, 2}


@pytest.mark.asyncio
async def test_llm_challenge_source_rejects_precomputed_mode() -> None:
    with pytest.raises(DebateConfigurationError):
        await LlmChallengeSource(llm=_FakeChallengeCaller()).collect(
            _make_spec(mode="precomputed", max_rounds=1),
            DebateContext(namespace="test"),
        )


@pytest.mark.asyncio
async def test_llm_challenge_source_fires_callback() -> None:
    fired: list[DebateChallenge] = []

    async def on_challenge(challenge: DebateChallenge) -> None:
        fired.append(challenge)

    source = LlmChallengeSource(llm=_FakeChallengeCaller(), on_challenge=on_challenge)
    await source.collect(
        _make_spec(mode="round_robin", max_rounds=2),
        DebateContext(namespace="test"),
    )

    assert len(fired) == 6


@pytest.mark.asyncio
async def test_llm_challenge_source_wraps_generation_failures() -> None:
    source = LlmChallengeSource(llm=_ExplodingChallengeCaller())

    with pytest.raises(DebateGenerationError) as exc:
        await source.collect(
            _make_spec(mode="round_robin", max_rounds=1),
            DebateContext(namespace="test"),
        )

    assert exc.value.stage == "challenge_generation"


@pytest.mark.asyncio
async def test_llm_challenge_source_uses_custom_prompt_set() -> None:
    prompt_set = ChallengePromptSet(
        first_round_prompt_template="first::{challenger_label}::{challenger_stance}::{topic}::{round_index}",
        rebuttal_prompt_template=(
            "rebut::{challenger_label}::{challenger_stance}::{topic}::"
            "{target_label}::{prior_argument}::{round_index}"
        ),
    )
    caller = _CapturingChallengeCaller()
    source = LlmChallengeSource(llm=caller, prompt_set=prompt_set)

    await source.collect(
        _make_spec(mode="round_robin", max_rounds=2),
        DebateContext(namespace="test"),
    )

    assert caller.prompts[0] == "first::Person 0::Stance 0::Test topic::1"
    assert caller.prompts[3] == "rebut::Person 0::Stance 0::Test topic::Person 1::challenge 3::2"


@dataclass
class _FakeChallengeCaller:
    call_count: int = 0

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        self.call_count += 1
        return response_model.model_validate(
            {
                "challenge_text": f"challenge {self.call_count}",
                "topic_tag": "test_topic",
                "confidence": 0.75,
            }
        )


class _ExplodingChallengeCaller:
    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        raise RuntimeError("challenge failed")


@dataclass
class _CapturingChallengeCaller:
    prompts: list[str] | None = None
    call_count: int = 0

    def __post_init__(self) -> None:
        if self.prompts is None:
            self.prompts = []

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        assert self.prompts is not None
        self.prompts.append(prompt)
        self.call_count += 1
        return response_model.model_validate(
            {
                "challenge_text": f"challenge {self.call_count}",
                "topic_tag": "test_topic",
                "confidence": 0.75,
            }
        )
