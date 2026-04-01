"""Protocols for planning debate specifications."""

from __future__ import annotations

from typing import Protocol

from agentic_debate.context import DebateContext
from agentic_debate.planning.types import DebatePlan


class DebatePlanner(Protocol):
    """Provider-neutral contract for turning a topic into a debate plan."""

    async def plan_topic(self, topic: str, *, context: DebateContext) -> DebatePlan: ...
