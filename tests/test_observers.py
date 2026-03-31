"""Tests for InMemoryObserver."""
from __future__ import annotations

import pytest
from agentic_debate.context import DebateContext
from agentic_debate.observers.memory import InMemoryObserver


@pytest.mark.asyncio
async def test_in_memory_observer_captures_events():
    observer = InMemoryObserver()
    ctx = DebateContext(namespace="test")
    await observer.on_event("round_started", {"count": 3}, ctx)
    await observer.on_event("arbitration_started", {"topic_count": 2}, ctx)

    assert observer.event_types() == ["round_started", "arbitration_started"]
    assert observer.events[0][1] == {"count": 3}


@pytest.mark.asyncio
async def test_in_memory_observer_starts_empty():
    observer = InMemoryObserver()
    assert observer.events == []
    assert observer.event_types() == []
