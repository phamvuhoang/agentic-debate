from __future__ import annotations
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_debate_endpoint_returns_sse_stream():
    intent_payload = json.dumps({
        "reframed_topic": "Test topic",
        "domain": "test",
        "controversy_level": "low",
        "recommended_participants": 2,
        "recommended_rounds": 1,
    })
    team_payload = json.dumps({
        "participants": [
            {"participant_id": "p0", "label": "Alice", "role": "debater", "stance": "pro"},
            {"participant_id": "p1", "label": "Bob", "role": "debater", "stance": "con"},
        ]
    })
    challenge_payload = json.dumps({"challenge_text": "My arg.", "topic_tag": "topic", "confidence": 0.7})
    judge_payload = json.dumps({
        "verdicts": [{"topic": "topic", "winning_participant_id": "p0", "confidence": 0.8,
                      "rationale": "P0 won.", "open_questions": [], "consensus_level": "strong"}],
        "debate_summary": "Good debate.",
        "contested_topics": [],
    })

    responses = [intent_payload, team_payload, challenge_payload, challenge_payload, judge_payload]
    call_count = 0

    async def fake_generate(*args, **kwargs):
        nonlocal call_count
        resp = MagicMock()
        resp.text = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return resp

    mock_client = MagicMock()
    mock_client.aio = MagicMock()
    mock_client.aio.models = MagicMock()
    mock_client.aio.models.generate_content = fake_generate

    with patch("backend.gemini.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            async with ac.stream("POST", "/debate", json={"topic": "test topic"}) as resp:
                assert resp.status_code == 200
                assert "text/event-stream" in resp.headers["content-type"]
                lines = []
                async for line in resp.aiter_lines():
                    lines.append(line)
                    if len(lines) > 5:
                        break
                data_lines = [l for l in lines if l.startswith("data:")]
                assert len(data_lines) >= 1
                first = json.loads(data_lines[0].removeprefix("data:").strip())
                assert "beginRendering" in first


@pytest.mark.asyncio
async def test_debate_endpoint_honors_selected_team_and_round_counts():
    intent_payload = json.dumps({
        "reframed_topic": "Test topic",
        "domain": "test",
        "controversy_level": "low",
        "recommended_participants": 3,
        "recommended_rounds": 1,
    })
    team_payload = json.dumps({
        "participants": [
            {"participant_id": f"p{i}", "label": f"Person {i}", "role": "debater", "stance": "pro"}
            for i in range(10)
        ]
    })
    challenge_payload = json.dumps({"challenge_text": "My arg.", "topic_tag": "topic", "confidence": 0.7})
    judge_payload = json.dumps({
        "verdicts": [{"topic": "topic", "winning_participant_id": "p0", "confidence": 0.8,
                      "rationale": "P0 won.", "open_questions": [], "consensus_level": "strong"}],
        "debate_summary": "Good debate.",
        "contested_topics": [],
    })

    responses = [intent_payload, team_payload, *([challenge_payload] * 50), judge_payload]
    call_count = 0

    async def fake_generate(*args, **kwargs):
        nonlocal call_count
        resp = MagicMock()
        resp.text = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return resp

    mock_client = MagicMock()
    mock_client.aio = MagicMock()
    mock_client.aio.models = MagicMock()
    mock_client.aio.models.generate_content = fake_generate

    with patch("backend.gemini.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            async with ac.stream(
                "POST",
                "/debate",
                json={"topic": "test topic", "participant_count": 10, "round_count": 5},
            ) as resp:
                assert resp.status_code == 200
                async for _line in resp.aiter_lines():
                    pass

    assert call_count == 53


def test_debate_request_accepts_legacy_max_field_aliases():
    from backend.main import DebateRequest

    request = DebateRequest.model_validate(
        {"topic": "test topic", "max_participants": 10, "max_rounds": 5}
    )

    assert request.participant_count == 10
    assert request.round_count == 5
