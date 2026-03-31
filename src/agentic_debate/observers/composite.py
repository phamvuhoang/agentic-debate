"""Composite observer implementation."""

from __future__ import annotations

from typing import Any

from agentic_debate.context import DebateContext
from agentic_debate.protocols import DebateObserver


class CompositeObserver:
    """Forward events to multiple underlying observers."""

    def __init__(self, observers: list[DebateObserver]) -> None:
        self._observers = list(observers)

    async def on_event(self, event_type: str, payload: dict[str, Any], context: DebateContext) -> None:
        for observer in self._observers:
            await observer.on_event(event_type, payload, context)
