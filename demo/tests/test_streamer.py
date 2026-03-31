from __future__ import annotations
import asyncio
import json
import pytest
from agentic_debate.context import DebateContext
from agentic_debate.types import (
    DebateArbitration,
    DebateChallenge,
    DebateParticipant,
    DebateVerdict,
)


def _ctx() -> DebateContext:
    return DebateContext(namespace="test")


def test_begin_rendering_format():
    from backend.streamer import begin_rendering_msg
    msg = json.loads(begin_rendering_msg("debate-surface", "debate_root"))
    assert "beginRendering" in msg
    assert msg["beginRendering"]["surfaceId"] == "debate-surface"
    assert msg["beginRendering"]["root"] == "debate_root"


def test_status_card_is_valid_surface_update():
    from backend.streamer import status_card_msg
    msg = json.loads(status_card_msg("Analyzing...", []))
    assert "surfaceUpdate" in msg
    components = {c["id"]: c for c in msg["surfaceUpdate"]["components"]}
    assert "debate_root" in components
    # debate_root must have a Column with children
    col = components["debate_root"]["component"]["Column"]
    assert "status_card" in col["children"]["explicitList"]


def test_argument_card_includes_participant_name():
    from backend.streamer import argument_card_msg
    participants = [
        DebateParticipant(
            participant_id="alice",
            label="Alice",
            role="debater",
            stance="pro",
            metadata={"accent_color": "#4F86C6"},
        ),
        DebateParticipant(
            participant_id="bob",
            label="Bob",
            role="debater",
            stance="con",
            metadata={"accent_color": "#E05A5A"},
        ),
    ]
    challenge = DebateChallenge(
        round_index=1,
        challenger_id="alice",
        target_id="bob",
        topic="ai_safety",
        challenge_text="AI poses existential risks.",
        confidence=0.8,
    )
    existing_children = ["topic_card"]
    msg = json.loads(argument_card_msg(challenge, participants, existing_children))
    raw = json.dumps(msg)
    assert "Alice" in raw
    assert "AI poses existential risks." in raw


def test_verdict_card_includes_winner_and_rationale():
    from backend.streamer import verdict_card_msg
    participants = [
        DebateParticipant(participant_id="alice", label="Alice", role="debater"),
        DebateParticipant(participant_id="bob", label="Bob", role="debater"),
    ]
    arbitration = DebateArbitration(
        verdicts=[
            DebateVerdict(
                topic="ai_safety",
                winning_participant_id="alice",
                confidence=0.85,
                rationale="Alice provided stronger evidence.",
                open_questions=["What about edge cases?"],
                consensus_level="moderate",
            )
        ],
        summary="Alice won the debate.",
        contested_topics=["ai_safety"],
    )
    existing_children = ["topic_card", "arg_r1_alice"]
    msg = json.loads(verdict_card_msg(arbitration, participants, existing_children))
    raw = json.dumps(msg)
    assert "Alice" in raw
    assert "Alice provided stronger evidence." in raw


@pytest.mark.asyncio
async def test_observer_enqueues_on_arbitration_started():
    from backend.streamer import A2UIStreamObserver
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    participants = [
        DebateParticipant(participant_id="p1", label="P1", role="debater"),
    ]
    observer = A2UIStreamObserver(queue=queue, participants=participants)
    ctx = _ctx()
    await observer.on_event("round_started", {"namespace": "test"}, ctx)
    # round_started should not enqueue anything
    assert queue.empty()

    await observer.on_event("arbitration_started", {"topic_count": 2}, ctx)
    msg = await queue.get()
    assert msg is not None
    data = json.loads(msg)
    assert "surfaceUpdate" in data
