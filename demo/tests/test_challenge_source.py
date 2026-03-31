from __future__ import annotations
import json
from typing import Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock
import pytest
from agentic_debate.context import DebateContext
from agentic_debate.spec import DebateSpec, RoundPolicy
from agentic_debate.types import DebateChallenge, DebateParticipant, DebateSubject


def _make_spec(n_participants: int = 3, max_rounds: int = 2) -> DebateSpec:
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
            for i in range(n_participants)
        ],
        round_policy=RoundPolicy(mode="precomputed", max_rounds=max_rounds),
    )


def _make_caller(challenge_text: str = "My argument."):
    from backend.gemini import GeminiLlmCaller
    client = MagicMock()
    response = MagicMock()
    response.text = json.dumps({
        "challenge_text": challenge_text,
        "topic_tag": "test_topic",
        "confidence": 0.75,
    })
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return GeminiLlmCaller(client=client)


@pytest.mark.asyncio
async def test_collect_generates_n_participants_times_rounds():
    from backend.challenge_source import LlmChallengeSource
    spec = _make_spec(n_participants=3, max_rounds=2)
    source = LlmChallengeSource(llm=_make_caller())
    ctx = DebateContext(namespace="test")
    challenges = await source.collect(spec, ctx)
    assert len(challenges) == 6  # 3 participants × 2 rounds


@pytest.mark.asyncio
async def test_collect_sets_round_index():
    from backend.challenge_source import LlmChallengeSource
    spec = _make_spec(n_participants=2, max_rounds=2)
    source = LlmChallengeSource(llm=_make_caller())
    ctx = DebateContext(namespace="test")
    challenges = await source.collect(spec, ctx)
    round_indices = {c.round_index for c in challenges}
    assert round_indices == {1, 2}


@pytest.mark.asyncio
async def test_collect_uses_round_robin_targets():
    from backend.challenge_source import LlmChallengeSource
    spec = _make_spec(n_participants=3, max_rounds=1)
    source = LlmChallengeSource(llm=_make_caller())
    ctx = DebateContext(namespace="test")
    challenges = await source.collect(spec, ctx)
    # p0 challenges p1, p1 challenges p2, p2 challenges p0
    assert challenges[0].challenger_id == "p0"
    assert challenges[0].target_id == "p1"
    assert challenges[1].challenger_id == "p1"
    assert challenges[1].target_id == "p2"
    assert challenges[2].challenger_id == "p2"
    assert challenges[2].target_id == "p0"


@pytest.mark.asyncio
async def test_collect_fires_on_challenge_callback():
    from backend.challenge_source import LlmChallengeSource
    fired: list[DebateChallenge] = []

    async def on_challenge(c: DebateChallenge) -> None:
        fired.append(c)

    spec = _make_spec(n_participants=2, max_rounds=2)
    source = LlmChallengeSource(llm=_make_caller(), on_challenge=on_challenge)
    ctx = DebateContext(namespace="test")
    await source.collect(spec, ctx)
    assert len(fired) == 4  # 2 × 2
