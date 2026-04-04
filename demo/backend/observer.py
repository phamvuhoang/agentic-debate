from __future__ import annotations

from typing import Any, Callable

from agentic_debate.context import DebateContext


class DebateStageObserver:
    """Maps engine lifecycle events to typed session events."""

    def __init__(
        self,
        publish: Callable[[str, str, dict[str, Any]], None],
    ) -> None:
        self._publish = publish

    async def on_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        context: DebateContext,
    ) -> None:
        _ = context
        if event_type == "arbitration_started":
            self._publish("judge_intervened", "verdict", {"reason": "arbitration_started"})
        elif event_type == "arbitration_completed":
            self._publish("verdict_requested", "verdict", {})
