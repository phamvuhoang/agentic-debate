"""Protocols for neutral debate execution components."""

from __future__ import annotations

from typing import Any, Protocol

from agentic_debate.context import DebateContext
from agentic_debate.result import DebateRoundResult
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateArbitration, DebateChallenge, DebateTopicGroup


class ChallengeSource(Protocol):
    """Supplies challenges for a debate run."""

    async def collect(self, spec: DebateSpec, context: DebateContext) -> list[DebateChallenge]: ...


class GroupingStrategy(Protocol):
    """Groups challenges into topics for arbitration."""

    async def group(
        self,
        challenges: list[DebateChallenge],
        spec: DebateSpec,
        context: DebateContext,
    ) -> list[DebateTopicGroup]: ...


class Arbitrator(Protocol):
    """Arbitrates grouped debate challenges."""

    async def arbitrate(
        self,
        groups: list[DebateTopicGroup],
        spec: DebateSpec,
        context: DebateContext,
    ) -> DebateArbitration: ...


class Synthesizer(Protocol):
    """Produces optional post-arbitration synthesis payloads."""

    async def synthesize(
        self,
        *,
        spec: DebateSpec,
        round_result: DebateRoundResult,
        arbitration: DebateArbitration,
        context: DebateContext,
    ) -> dict[str, Any]: ...


class TranscriptFormatter(Protocol):
    """Formats a transcript object for the host application."""

    async def build(
        self,
        *,
        spec: DebateSpec,
        round_result: DebateRoundResult,
        arbitration: DebateArbitration,
        synthesis: dict[str, Any],
        context: DebateContext,
    ) -> dict[str, Any]: ...


class DebateObserver(Protocol):
    """Receives lifecycle events during debate execution."""

    async def on_event(self, event_type: str, payload: dict[str, Any], context: DebateContext) -> None: ...
