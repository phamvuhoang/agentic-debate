"""Core value models for the neutral debate package."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DebateSubject(BaseModel):
    """What is being debated."""

    subject_id: str | None = None
    kind: str
    title: str
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebateParticipant(BaseModel):
    """A lens, role, agent, or human participant in the debate."""

    participant_id: str
    label: str
    role: str
    stance: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebateEvidence(BaseModel):
    """Optional evidence object usable by richer debate methods."""

    evidence_id: str | None = None
    kind: str
    summary: str
    content: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebateChallenge(BaseModel):
    """A structured challenge raised by one participant against another."""

    challenge_id: str | None = None
    round_index: int = 1
    challenger_id: str
    target_id: str
    topic: str
    challenge_text: str
    confidence: float = 0.5
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebateTopicGroup(BaseModel):
    """A set of challenges grouped under the same topic."""

    topic: str
    challenges: list[DebateChallenge] = Field(default_factory=list)


class DebateVerdict(BaseModel):
    """Arbitrated verdict for a contested topic."""

    topic: str
    winning_participant_id: str
    confidence: float
    rationale: str
    open_questions: list[str] = Field(default_factory=list)
    consensus_level: Literal["strong", "moderate", "contested"] = "moderate"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebateArbitration(BaseModel):
    """Complete arbitration output across all contested topics."""

    verdicts: list[DebateVerdict] = Field(default_factory=list)
    summary: str = ""
    contested_topics: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
