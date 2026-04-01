"""Smoke coverage for the installable package happy path."""
from __future__ import annotations

from pathlib import Path

import pytest

from agentic_debate import (
    DebateCompiler,
    DebateContext,
    DebateEngine,
    GroupByTopicStrategy,
    LlmChallengeSource,
    LlmDebatePlanner,
    LlmSingleJudgeArbitrator,
    PassthroughSynthesizer,
    SimpleTranscriptFormatter,
)
from agentic_debate.prompts import load_builtin_judge_prompt


@pytest.mark.asyncio
async def test_installable_topic_to_runnable_debate_flow() -> None:
    llm = _SequenceFakeLlmCaller(
        [
            {
                "reframed_topic": "Is nuclear power safe?",
                "domain": "energy",
                "controversy_level": "high",
                "recommended_participants": 3,
                "recommended_rounds": 2,
            },
            {
                "participants": [
                    {
                        "participant_id": "engineer",
                        "label": "Engineer",
                        "role": "expert",
                        "stance": "Nuclear is scalable",
                    },
                    {
                        "participant_id": "activist",
                        "label": "Activist",
                        "role": "critic",
                        "stance": "Nuclear risk is underestimated",
                    },
                    {
                        "participant_id": "economist",
                        "label": "Economist",
                        "role": "analyst",
                        "stance": "Cost decides viability",
                    },
                ]
            },
            *[
                {
                    "challenge_text": f"challenge {i}",
                    "topic_tag": "safety_cost",
                    "confidence": 0.75,
                }
                for i in range(1, 7)
            ],
            {
                "verdicts": [
                    {
                        "topic": "safety_cost",
                        "winning_participant_id": "engineer",
                        "confidence": 0.8,
                        "rationale": "Engineering argument carried the round.",
                        "open_questions": [],
                        "consensus_level": "moderate",
                    }
                ],
                "debate_summary": "Engineer leads.",
                "contested_topics": [],
            },
        ]
    )
    ctx = DebateContext(namespace="test")

    plan = await LlmDebatePlanner(llm=llm).plan_topic(
        "Is nuclear power safe?",
        context=ctx,
    )
    spec = plan.to_spec(namespace="test")

    compiler = DebateCompiler(
        challenge_source=LlmChallengeSource(llm=llm),
        grouping=GroupByTopicStrategy(),
        arbitrator=LlmSingleJudgeArbitrator(
            llm=llm,
            prompt_template=load_builtin_judge_prompt(),
        ),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
    )

    result = await DebateEngine().run(await compiler.compile(spec), context=ctx)

    assert result.arbitration.verdicts
    assert result.arbitration.verdicts[0].winning_participant_id == "engineer"


class _SequenceFakeLlmCaller:
    def __init__(self, responses: list[dict]) -> None:
        self._responses = iter(responses)

    async def generate_structured(self, prompt: str, response_model: type, *, context: DebateContext):
        try:
            payload = next(self._responses)
        except StopIteration as exc:
            raise AssertionError("Unexpected extra LLM call in smoke test") from exc

        return response_model.model_validate(payload)


def test_readme_does_not_reference_demo_backend_imports() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    assert "from backend.gemini" not in text
    assert "LlmDebatePlanner" in text
    assert "LlmChallengeSource" in text
