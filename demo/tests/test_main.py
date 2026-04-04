from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_create_session_route_returns_session_urls() -> None:
    from backend.main import create_app

    class _FakeDirector:
        async def create_session(self, request):
            return {
                "session_id": "session-1",
                "events_url": "/api/sessions/session-1/events",
                "actions_url": "/api/sessions/session-1/actions",
                "replay_url": "/api/sessions/session-1/replay",
            }

    app = create_app(director=_FakeDirector())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/sessions", json={"topic": "test topic"})

    assert response.status_code == 200
    assert response.json()["events_url"].endswith("/events")
