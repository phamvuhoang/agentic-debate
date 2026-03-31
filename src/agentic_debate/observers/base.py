"""Basic observer implementations."""

from __future__ import annotations

from typing import Any

from agentic_debate.context import DebateContext


class NoopObserver:
    """Observer that ignores all events."""

    async def on_event(self, event_type: str, payload: dict[str, Any], context: DebateContext) -> None:
        _ = (event_type, payload, context)
