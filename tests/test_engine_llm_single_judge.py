"""Tests for LlmSingleJudgeArbitrator."""
from __future__ import annotations

import pytest
from agentic_debate.compile import DebateCompiler
from agentic_debate.context import DebateContext
from agentic_debate.engine import DebateEngine
from agentic_debate.methods.arbitration.llm_single_judge import LlmSingleJudgeArbitrator
from agentic_debate.methods.grouping import GroupByTopicStrategy
from agentic_debate.methods.rounds.precomputed import PrecomputedChallengeSource
from agentic_debate.methods.synthesis.passthrough import PassthroughSynthesizer
from agentic_debate.methods.transcript import SimpleTranscriptFormatter
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateChallenge, DebateParticipant, DebateSubject


SIMPLE_TEMPLATE = (
    "Challenges: {challenges_json}\n"
    "Participants: {participants_json}\n"
    "Options: {winning_options_json}"
)


class _FakeLlmCaller:
    """Returns a fixed structured output regardless of prompt."""

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        return response_model.model_validate({
            "verdicts": [
                {
                    "topic": "topic1",
                    "winning_participant_id": "a",
                    "confidence": 0.9,
                    "rationale": "A was more compelling",
                    "open_questions": ["Is this robust?"],
                    "consensus_level": "strong",
                }
            ],
            "debate_summary": "A won clearly.",
            "contested_topics": [],
        })


@pytest.mark.asyncio
async def test_llm_single_judge_produces_verdict():
    spec = DebateSpec(
        namespace="test",
        subject=DebateSubject(kind="test", title="Test"),
        participants=[
            DebateParticipant(participant_id="a", label="A", role="lens"),
            DebateParticipant(participant_id="b", label="B", role="lens"),
        ],
    )
    challenges = [
        DebateChallenge(
            challenger_id="a", target_id="b", topic="topic1",
            challenge_text="A challenges B", confidence=0.8,
        )
    ]
    compiler = DebateCompiler(
        challenge_source=PrecomputedChallengeSource(challenges),
        grouping=GroupByTopicStrategy(),
        arbitrator=LlmSingleJudgeArbitrator(
            llm=_FakeLlmCaller(), prompt_template=SIMPLE_TEMPLATE
        ),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
    )
    result = await DebateEngine().run(
        await compiler.compile(spec), context=DebateContext(namespace="test")
    )
    assert len(result.arbitration.verdicts) == 1
    assert result.arbitration.verdicts[0].winning_participant_id == "a"
    assert result.arbitration.verdicts[0].consensus_level == "strong"
    assert result.arbitration.metadata["source"] == "llm_single_judge"


@pytest.mark.asyncio
async def test_llm_single_judge_replaces_unknown_winner_with_unresolved():
    spec = DebateSpec(
        namespace="test",
        subject=DebateSubject(kind="test", title="Test"),
        participants=[
            DebateParticipant(participant_id="a", label="A", role="lens"),
        ],
    )

    class _BadWinnerCaller:
        async def generate_structured(self, prompt, response_model, *, context):
            return response_model.model_validate({
                "verdicts": [{
                    "topic": "t1", "winning_participant_id": "unknown_lens",
                    "confidence": 0.5, "rationale": "r", "consensus_level": "moderate",
                }],
                "debate_summary": "s", "contested_topics": [],
            })

    compiler = DebateCompiler(
        challenge_source=PrecomputedChallengeSource([
            DebateChallenge(challenger_id="a", target_id="a", topic="t1",
                            challenge_text="c", confidence=0.5)
        ]),
        grouping=GroupByTopicStrategy(),
        arbitrator=LlmSingleJudgeArbitrator(llm=_BadWinnerCaller(), prompt_template=SIMPLE_TEMPLATE),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
    )
    result = await DebateEngine().run(
        await compiler.compile(spec), context=DebateContext(namespace="test")
    )
    assert result.arbitration.verdicts[0].winning_participant_id == "unresolved"


@pytest.mark.asyncio
async def test_llm_single_judge_extra_format_vars():
    """extra_format_vars callable is called and its output merged into prompt."""
    received_vars: dict = {}

    class _CapturingCaller:
        async def generate_structured(self, prompt: str, response_model, *, context):
            received_vars["prompt"] = prompt
            return response_model.model_validate({
                "verdicts": [], "debate_summary": "s", "contested_topics": [],
            })

    def extra(spec, context):
        return {"memos_json": '["memo1"]'}

    spec = DebateSpec(
        namespace="test",
        subject=DebateSubject(kind="test", title="Test"),
        participants=[DebateParticipant(participant_id="a", label="A", role="lens")],
    )
    template = "Challenges: {challenges_json} Memos: {memos_json}"
    compiler = DebateCompiler(
        challenge_source=PrecomputedChallengeSource([]),
        grouping=GroupByTopicStrategy(),
        arbitrator=LlmSingleJudgeArbitrator(
            llm=_CapturingCaller(), prompt_template=template, extra_format_vars=extra
        ),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
    )
    await DebateEngine().run(
        await compiler.compile(spec), context=DebateContext(namespace="test")
    )
    assert '["memo1"]' in received_vars.get("prompt", "")
