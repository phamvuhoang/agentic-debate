"""Result models returned by the neutral debate engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agentic_debate.types import DebateArbitration, DebateChallenge, DebateTopicGroup


class DebateRoundResult(BaseModel):
    """Output of the challenge collection and grouping stage."""

    challenges: list[DebateChallenge] = Field(default_factory=list)
    topic_groups: list[DebateTopicGroup] = Field(default_factory=list)


class DebateRunResult(BaseModel):
    """Output of the full arbitration stage."""

    round_result: DebateRoundResult
    arbitration: DebateArbitration = Field(default_factory=DebateArbitration)
    synthesis: dict[str, Any] = Field(default_factory=dict)
    transcript: dict[str, Any] = Field(default_factory=dict)
