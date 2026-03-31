from __future__ import annotations
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from agentic_debate.context import DebateContext
from agentic_debate.types import DebateParticipant


def _make_caller(response_json: str):
    from backend.gemini import GeminiLlmCaller
    client = MagicMock()
    response = MagicMock()
    response.text = response_json
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return GeminiLlmCaller(client=client)


@pytest.mark.asyncio
async def test_intent_analysis_returns_intent_result():
    from backend.gemini import intent_analysis, IntentResult
    payload = {
        "reframed_topic": "Should AI replace doctors?",
        "domain": "healthcare",
        "controversy_level": "high",
        "recommended_participants": 4,
        "recommended_rounds": 3,
    }
    caller = _make_caller(json.dumps(payload))
    ctx = DebateContext(namespace="test")
    result = await intent_analysis("should AI replace doctors", caller, ctx)
    assert isinstance(result, IntentResult)
    assert result.recommended_participants == 4
    assert result.recommended_rounds == 3
    assert result.controversy_level == "high"


@pytest.mark.asyncio
async def test_intent_analysis_clamps_participants():
    from backend.gemini import intent_analysis
    # Gemini might return out-of-range values — they must be clamped
    payload = {
        "reframed_topic": "test",
        "domain": "test",
        "controversy_level": "low",
        "recommended_participants": 99,  # too high
        "recommended_rounds": 0,          # too low
    }
    caller = _make_caller(json.dumps(payload))
    ctx = DebateContext(namespace="test")
    result = await intent_analysis("test", caller, ctx)
    assert 2 <= result.recommended_participants <= 5
    assert 1 <= result.recommended_rounds <= 3

    # Also test lower bound for participants
    payload_low = {
        "reframed_topic": "test",
        "domain": "test",
        "controversy_level": "low",
        "recommended_participants": 1,  # too low
        "recommended_rounds": 5,         # too high
    }
    caller_low = _make_caller(json.dumps(payload_low))
    result_low = await intent_analysis("test", caller_low, ctx)
    assert result_low.recommended_participants == 2
    assert result_low.recommended_rounds == 3


@pytest.mark.asyncio
async def test_generate_team_returns_correct_count():
    from backend.gemini import generate_team, IntentResult
    from backend.constants import ACCENT_COLORS
    raw_participants = [
        {"participant_id": f"p{i}", "label": f"Person {i}", "role": "debater", "stance": "pro"}
        for i in range(3)
    ]
    caller = _make_caller(json.dumps({"participants": raw_participants}))
    ctx = DebateContext(namespace="test")
    intent = IntentResult(
        reframed_topic="test",
        domain="tech",
        controversy_level="medium",
        recommended_participants=3,
        recommended_rounds=2,
    )
    participants = await generate_team(intent, caller, ctx)
    assert len(participants) == 3
    assert all(isinstance(p, DebateParticipant) for p in participants)
    # Each participant's metadata has accent_color
    assert all("accent_color" in p.metadata for p in participants)
    assert participants[0].metadata["accent_color"] == ACCENT_COLORS[0]
