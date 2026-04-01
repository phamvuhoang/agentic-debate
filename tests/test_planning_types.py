"""Tests for planning models and DebatePlan conversion."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentic_debate.planning.types import DebateIntent, DebatePlan, PlannedParticipant
from agentic_debate.spec import RoundPolicy


def test_debate_plan_to_spec_builds_runnable_spec() -> None:
    plan = DebatePlan(
        topic="Should AI replace doctors?",
        intent=DebateIntent(
            reframed_topic="Should AI replace doctors?",
            domain="healthcare",
            controversy_level="high",
            recommended_participants=3,
            recommended_rounds=2,
        ),
        participants=[
            PlannedParticipant(
                participant_id="doctor",
                label="Doctor",
                role="expert",
                stance="Keep humans central",
                metadata={"accent_color": "#4F86C6"},
            ),
            PlannedParticipant(
                participant_id="builder",
                label="Builder",
                role="technologist",
                stance="Automate aggressively",
            ),
        ],
        round_policy=RoundPolicy(mode="round_robin", max_rounds=2),
    )

    spec = plan.to_spec(namespace="test")

    assert spec.subject.title == "Should AI replace doctors?"
    assert spec.round_policy.mode == "round_robin"
    assert spec.round_policy.max_rounds == 2
    assert len(spec.participants) == 2
    assert spec.participants[0].metadata["accent_color"] == "#4F86C6"


def test_debate_plan_requires_unique_participant_ids() -> None:
    plan = DebatePlan(
        topic="Should AI replace doctors?",
        intent=DebateIntent(
            reframed_topic="Should AI replace doctors?",
            domain="healthcare",
            controversy_level="high",
            recommended_participants=2,
            recommended_rounds=2,
        ),
        participants=[
            PlannedParticipant(participant_id="doctor", label="Doctor A", role="expert"),
            PlannedParticipant(participant_id="doctor", label="Doctor B", role="expert"),
        ],
        round_policy=RoundPolicy(mode="round_robin", max_rounds=2),
    )

    with pytest.raises(ValueError):
        plan.to_spec(namespace="test")


def test_planned_participant_rejects_extra_top_level_fields() -> None:
    with pytest.raises(ValidationError):
        PlannedParticipant(
            participant_id="doctor",
            label="Doctor",
            role="expert",
            accent_color="#f00",
        )
