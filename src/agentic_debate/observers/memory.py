"""In-memory observer for testing and inspection."""
from __future__ import annotations

from typing import Any

from agentic_debate.context import DebateContext


class InMemoryObserver:
    """Captures all debate lifecycle events for testing and inspection."""

    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any], DebateContext]] = []

    async def on_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        context: DebateContext,
    ) -> None:
        self.events.append((event_type, payload, context))

    def event_types(self) -> list[str]:
        return [e[0] for e in self.events]
