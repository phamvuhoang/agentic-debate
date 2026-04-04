from __future__ import annotations

import pytest

from backend.protocol import SessionCreateRequest


class _FakeDemoLlmCaller:
    """Minimal fake LlmCaller that returns canned structured responses."""

    async def generate_structured(self, prompt: str, response_model, *, context):
        name = getattr(response_model, "__name__", "")

        # Intent analysis (_RawIntentResult)
        if "Intent" in name or name == "_RawIntentResult":
            return response_model(
                reframed_topic="Should AI replace doctors?",
                domain="healthcare",
                controversy_level="high",
                recommended_participants=2,
                recommended_rounds=1,
            )

        # Team/participant generation (_TeamResponse)
        if "Team" in name or name == "_TeamResponse":
            # Build minimal participant objects the model accepts
            try:
                from agentic_debate.planning.llm import _ParticipantRaw
                participants = [
                    _ParticipantRaw(participant_id="p0", label="Alice", role="debater", stance="pro"),
                    _ParticipantRaw(participant_id="p1", label="Bob", role="debater", stance="con"),
                ]
            except ImportError:
                participants = []
            return response_model(participants=participants)

        # Challenge generation (_ChallengeOutput)
        if "Challenge" in name:
            return response_model(
                challenge_text="My argument.",
                topic_tag="medicine",
                confidence=0.7,
            )

        # Judge arbitration (_JudgeOutput)
        if "Judge" in name or "Output" in name:
            return response_model(
                verdicts=[{
                    "topic": "medicine",
                    "winning_participant_id": "p0",
                    "confidence": 0.8,
                    "rationale": "Alice made stronger arguments.",
                    "open_questions": [],
                    "consensus_level": "strong",
                }],
                debate_summary="Good debate.",
                contested_topics=[],
            )

        raise NotImplementedError(f"_FakeDemoLlmCaller: unhandled {response_model}")

    async def generate_text(self, prompt: str, *, context) -> str:
        return prompt[:20]


@pytest.mark.asyncio
async def test_director_publishes_stage_events_in_order() -> None:
    from backend.director import DebateDirector
    from backend.session_store import SessionStore

    director = DebateDirector(
        store=SessionStore(),
        llm=_FakeDemoLlmCaller(),
    )

    response = await director.create_session(SessionCreateRequest(topic="Should AI replace doctors?"))

    # Wait for background task to complete
    import asyncio
    await asyncio.sleep(0.5)

    replay = director.store.get_replay(response.session_id)

    event_types = [e.type for e in replay.events]
    assert event_types[0] == "debate_created"
    assert "agent_summoned" in event_types
    assert event_types[-1] == "verdict_revealed"
