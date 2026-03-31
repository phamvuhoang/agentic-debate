"""Tests for the neutral debate engine using the heuristic arbitrator."""
from __future__ import annotations

import pytest

from agentic_debate.compile import DebateCompiler
from agentic_debate.context import DebateContext
from agentic_debate.engine import DebateEngine
from agentic_debate.methods.arbitration.heuristic import HeuristicArbitrator
from agentic_debate.methods.grouping import GroupByTopicStrategy
from agentic_debate.methods.rounds.precomputed import PrecomputedChallengeSource
from agentic_debate.methods.synthesis.passthrough import PassthroughSynthesizer
from agentic_debate.methods.transcript import SimpleTranscriptFormatter
from agentic_debate.observers.memory import InMemoryObserver
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateChallenge, DebateParticipant, DebateSubject


def _make_compiler(challenges: list[DebateChallenge], observer: InMemoryObserver | None = None) -> DebateCompiler:
    return DebateCompiler(
        challenge_source=PrecomputedChallengeSource(challenges),
        grouping=GroupByTopicStrategy(),
        arbitrator=HeuristicArbitrator(),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
        observers=[observer] if observer else [],
    )


def _make_spec() -> DebateSpec:
    return DebateSpec(
        namespace="test.analysis",
        subject=DebateSubject(kind="workflow_debate", title="Analysis Debate"),
        participants=[
            DebateParticipant(participant_id="operations", label="operations", role="lens"),
            DebateParticipant(participant_id="culture", label="culture", role="lens"),
            DebateParticipant(participant_id="strategy", label="strategy", role="lens"),
            DebateParticipant(participant_id="quantitative", label="quantitative", role="lens"),
        ],
    )


@pytest.mark.asyncio
async def test_engine_groups_topics_and_marks_contested():
    challenges = [
        DebateChallenge(
            challenger_id="operations", target_id="culture",
            topic="communication_breakdown", challenge_text="Ops challenge", confidence=0.72,
        ),
        DebateChallenge(
            challenger_id="culture", target_id="operations",
            topic="communication_breakdown", challenge_text="Culture challenge", confidence=0.66,
        ),
        DebateChallenge(
            challenger_id="quantitative", target_id="strategy",
            topic="leadership_alignment", challenge_text="Quant challenge", confidence=0.45,
        ),
    ]
    compiler = _make_compiler(challenges)
    result = await DebateEngine().run(
        await compiler.compile(_make_spec()),
        context=DebateContext(namespace="test.analysis"),
    )

    topics = {g.topic for g in result.round_result.topic_groups}
    assert topics == {"communication_breakdown", "leadership_alignment"}
    assert "leadership_alignment" in result.arbitration.contested_topics


@pytest.mark.asyncio
async def test_engine_fires_lifecycle_events():
    observer = InMemoryObserver()
    challenges = [
        DebateChallenge(
            challenger_id="a", target_id="b", topic="t1",
            challenge_text="c", confidence=0.7,
        )
    ]
    compiler = _make_compiler(challenges, observer)
    await DebateEngine().run(
        await compiler.compile(_make_spec()),
        context=DebateContext(namespace="test.analysis"),
    )

    event_types = observer.event_types()
    assert "round_started" in event_types
    assert "challenges_collected" in event_types
    assert "arbitration_started" in event_types
    assert "transcript_built" in event_types


@pytest.mark.asyncio
async def test_engine_skips_localization_for_english():
    """Engine with no localizer produces a transcript without raising."""
    challenges = [
        DebateChallenge(
            challenger_id="a", target_id="b", topic="t1",
            challenge_text="challenge", confidence=0.8,
        )
    ]
    result = await DebateEngine().run(
        await _make_compiler(challenges).compile(_make_spec()),
        context=DebateContext(namespace="test"),
    )
    assert result.transcript["namespace"] == "test.analysis"
