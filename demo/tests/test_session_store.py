from __future__ import annotations

import pytest

from backend.protocol import DebateEvent


@pytest.mark.asyncio
async def test_session_store_replays_events_in_sequence() -> None:
    from backend.session_store import SessionStore

    store = SessionStore()
    session_id = store.create_session()
    store.publish(
        DebateEvent(
            session_id=session_id,
            sequence=1,
            type="debate_created",
            phase="idle",
            payload={"topic": "Should AI replace doctors?"},
        )
    )

    replay = store.get_replay(session_id)
    assert replay.events[0].type == "debate_created"
