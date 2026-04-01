"""Planning models for topic-to-spec workflows."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from agentic_debate.spec import DebateSpec, RoundPolicy
from agentic_debate.types import DebateParticipant, DebateSubject


class DebateIntent(BaseModel):
    """Normalized planning output for a raw topic."""

    reframed_topic: str
    domain: str
    controversy_level: Literal["low", "medium", "high"]
    recommended_participants: int
    recommended_rounds: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlannedParticipant(BaseModel):
    """Participant shape used during planning before a spec is built."""

    model_config = ConfigDict(extra="forbid")

    participant_id: str
    label: str
    role: str
    stance: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebatePlan(BaseModel):
    """Resolved planning artifact that can be converted into a debate spec."""

    topic: str
    intent: DebateIntent
    participants: list[PlannedParticipant]
    round_policy: RoundPolicy
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_spec(self, namespace: str, *, subject_kind: str = "open_question") -> DebateSpec:
        """Convert the plan into a runnable debate spec."""
        participant_ids = [participant.participant_id for participant in self.participants]
        if len(set(participant_ids)) != len(participant_ids):
            raise ValueError("DebatePlan participants must have unique participant_id values")

        return DebateSpec(
            namespace=namespace,
            subject=DebateSubject(kind=subject_kind, title=self.intent.reframed_topic),
            participants=[
                DebateParticipant(
                    **participant.model_dump(
                        include={"participant_id", "label", "role", "stance", "metadata"}
                    )
                )
                for participant in self.participants
            ],
            round_policy=self.round_policy,
            metadata=dict(self.metadata),
        )
