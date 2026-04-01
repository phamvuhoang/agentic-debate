from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from agentic_debate.context import DebateContext
from backend.constants import ACCENT_COLORS


def _make_caller(*response_payloads: dict):
    from backend.gemini import GeminiLlmCaller

    responses = []
    for payload in response_payloads:
        response = MagicMock()
        response.text = json.dumps(payload)
        responses.append(response)

    client = MagicMock()
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(side_effect=responses)
    return GeminiLlmCaller(client=client)


@pytest.mark.asyncio
async def test_build_demo_plan_uses_library_planner_with_gemini_adapter():
    from backend.planning import build_demo_plan

    intent_payload = {
        "reframed_topic": "Should AI replace doctors?",
        "domain": "healthcare",
        "controversy_level": "high",
        "recommended_participants": 3,
        "recommended_rounds": 2,
    }
    team_payload = {
        "participants": [
            {"participant_id": f"p{i}", "label": f"Person {i}", "role": "debater", "stance": "pro"}
            for i in range(3)
        ]
    }
    caller = _make_caller(intent_payload, team_payload)
    ctx = DebateContext(namespace="test")

    plan = await build_demo_plan("should AI replace doctors", caller, ctx)

    assert plan.intent.reframed_topic == "Should AI replace doctors?"
    assert len(plan.participants) == 3
    assert plan.round_policy.max_rounds == 2
    assert all("accent_color" in participant.metadata for participant in plan.participants)
    assert plan.participants[0].metadata["accent_color"] == ACCENT_COLORS[0]


@pytest.mark.asyncio
async def test_build_demo_plan_clamps_values_via_library_planner():
    from backend.planning import build_demo_plan

    intent_payload = {
        "reframed_topic": "test",
        "domain": "test",
        "controversy_level": "banana",
        "recommended_participants": 99,
        "recommended_rounds": 0,
    }
    team_payload = {
        "participants": [
            {"participant_id": f"p{i}", "label": f"Person {i}", "role": "debater", "stance": "pro"}
            for i in range(6)
        ]
    }
    caller = _make_caller(intent_payload, team_payload)
    ctx = DebateContext(namespace="test")

    plan = await build_demo_plan("test", caller, ctx)

    assert plan.intent.controversy_level == "medium"
    assert plan.intent.recommended_participants == 10
    assert len(plan.participants) == 6
    assert plan.round_policy.max_rounds == 1


@pytest.mark.asyncio
async def test_build_demo_plan_applies_demo_caps():
    from backend.planning import build_demo_plan

    intent_payload = {
        "reframed_topic": "Should AI replace doctors?",
        "domain": "healthcare",
        "controversy_level": "high",
        "recommended_participants": 5,
        "recommended_rounds": 3,
    }
    team_payload = {
        "participants": [
            {"participant_id": f"p{i}", "label": f"Person {i}", "role": "debater", "stance": "pro"}
            for i in range(5)
        ]
    }
    caller = _make_caller(intent_payload, team_payload)
    ctx = DebateContext(namespace="test")

    plan = await build_demo_plan(
        "should AI replace doctors",
        caller,
        ctx,
        max_participants=3,
        max_rounds=2,
    )

    assert len(plan.participants) == 3
    assert plan.intent.recommended_participants == 3
    assert plan.intent.recommended_rounds == 2
    assert plan.round_policy.max_rounds == 2
    assert plan.participants[0].metadata["accent_color"] == ACCENT_COLORS[0]


@pytest.mark.asyncio
async def test_build_demo_plan_honors_exact_demo_selections():
    from backend.planning import build_demo_plan

    intent_payload = {
        "reframed_topic": "Should AI replace doctors?",
        "domain": "healthcare",
        "controversy_level": "high",
        "recommended_participants": 3,
        "recommended_rounds": 1,
    }
    team_payload = {
        "participants": [
            {"participant_id": f"p{i}", "label": f"Person {i}", "role": "debater", "stance": "pro"}
            for i in range(5)
        ]
    }
    caller = _make_caller(intent_payload, team_payload)
    ctx = DebateContext(namespace="test")

    plan = await build_demo_plan(
        "should AI replace doctors",
        caller,
        ctx,
        participant_count=5,
        round_count=3,
    )

    assert len(plan.participants) == 5
    assert plan.intent.recommended_participants == 5
    assert plan.intent.recommended_rounds == 3
    assert plan.round_policy.max_rounds == 3
    assert plan.participants[0].metadata["accent_color"] == ACCENT_COLORS[0]


@pytest.mark.asyncio
async def test_build_demo_plan_supports_ten_members_and_five_rounds():
    from backend.planning import build_demo_plan

    intent_payload = {
        "reframed_topic": "Should AI replace doctors?",
        "domain": "healthcare",
        "controversy_level": "high",
        "recommended_participants": 3,
        "recommended_rounds": 1,
    }
    team_payload = {
        "participants": [
            {"participant_id": f"p{i}", "label": f"Person {i}", "role": "debater", "stance": "pro"}
            for i in range(10)
        ]
    }
    caller = _make_caller(intent_payload, team_payload)
    ctx = DebateContext(namespace="test")

    plan = await build_demo_plan(
        "should AI replace doctors",
        caller,
        ctx,
        participant_count=10,
        round_count=5,
    )

    assert len(plan.participants) == 10
    assert plan.intent.recommended_participants == 10
    assert plan.intent.recommended_rounds == 5
    assert plan.round_policy.max_rounds == 5
    assert plan.participants[0].metadata["accent_color"] == ACCENT_COLORS[0]
