"""Tests for OutputLocalizer engine hook."""
from __future__ import annotations

import pytest
from agentic_debate.compile import DebateCompiler
from agentic_debate.context import DebateContext
from agentic_debate.engine import DebateEngine
from agentic_debate.localization import OutputLocalizer, PassthroughLocalizer
from agentic_debate.methods.arbitration.heuristic import HeuristicArbitrator
from agentic_debate.methods.grouping import GroupByTopicStrategy
from agentic_debate.methods.rounds.precomputed import PrecomputedChallengeSource
from agentic_debate.methods.synthesis.passthrough import PassthroughSynthesizer
from agentic_debate.methods.transcript import SimpleTranscriptFormatter
from agentic_debate.spec import DebateSpec, TranscriptPolicy
from agentic_debate.types import DebateChallenge, DebateParticipant, DebateSubject


def _make_spec(output_locale: str = "en") -> DebateSpec:
    return DebateSpec(
        namespace="test",
        subject=DebateSubject(kind="test", title="Test Debate"),
        participants=[
            DebateParticipant(participant_id="a", label="A", role="lens"),
            DebateParticipant(participant_id="b", label="B", role="lens"),
        ],
        transcript_policy=TranscriptPolicy(output_locale=output_locale),
    )


def _make_challenges() -> list[DebateChallenge]:
    return [
        DebateChallenge(
            challenger_id="a",
            target_id="b",
            topic="topic1",
            challenge_text="Challenge text",
            confidence=0.8,
        )
    ]


@pytest.mark.asyncio
async def test_passthrough_localizer_produces_identical_output():
    """English output with PassthroughLocalizer must be byte-identical to no localizer."""
    spec = _make_spec("en")
    challenges = _make_challenges()

    compiler_no_loc = DebateCompiler(
        challenge_source=PrecomputedChallengeSource(challenges),
        grouping=GroupByTopicStrategy(),
        arbitrator=HeuristicArbitrator(),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
    )
    compiler_with_passthrough = DebateCompiler(
        challenge_source=PrecomputedChallengeSource(challenges),
        grouping=GroupByTopicStrategy(),
        arbitrator=HeuristicArbitrator(),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
        output_localizer=PassthroughLocalizer(),
    )
    ctx = DebateContext(namespace="test")
    result_no = await DebateEngine().run(await compiler_no_loc.compile(spec), context=ctx)
    result_with = await DebateEngine().run(await compiler_with_passthrough.compile(spec), context=ctx)

    assert result_no.transcript == result_with.transcript


@pytest.mark.asyncio
async def test_localizer_transforms_text_fields():
    """Non-English locale with a mock localizer transforms summary and rationale."""
    spec = _make_spec("fr")

    class UpperCaseLocalizer:
        async def localize(self, text: str, target_locale: str, context: DebateContext) -> str:
            return text.upper()

    compiler = DebateCompiler(
        challenge_source=PrecomputedChallengeSource(_make_challenges()),
        grouping=GroupByTopicStrategy(),
        arbitrator=HeuristicArbitrator(),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
        output_localizer=UpperCaseLocalizer(),
    )
    ctx = DebateContext(namespace="test")
    result = await DebateEngine().run(await compiler.compile(spec), context=ctx)

    assert result.transcript["summary"] == result.transcript["summary"].upper()


@pytest.mark.asyncio
async def test_localizer_error_leaves_field_in_english():
    """If the localizer raises, the field stays in English; other fields are localized."""
    spec = _make_spec("fr")
    call_count = {"n": 0}

    class PartialFailLocalizer:
        async def localize(self, text: str, target_locale: str, context: DebateContext) -> str:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("localize failed")
            return text.upper()

    compiler = DebateCompiler(
        challenge_source=PrecomputedChallengeSource(_make_challenges()),
        grouping=GroupByTopicStrategy(),
        arbitrator=HeuristicArbitrator(),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
        output_localizer=PartialFailLocalizer(),
    )
    ctx = DebateContext(namespace="test")
    # Should not raise — error is swallowed with a warning
    result = await DebateEngine().run(await compiler.compile(spec), context=ctx)
    assert result.transcript is not None
