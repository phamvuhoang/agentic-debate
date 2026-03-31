"""Debate specification models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from agentic_debate.types import DebateParticipant, DebateSubject


class RoundPolicy(BaseModel):
    """Policy describing how debate rounds are constructed."""

    mode: Literal["precomputed", "round_robin", "pairwise"] = "precomputed"
    max_rounds: int = 1
    allow_self_challenge: bool = False
    min_topics_for_arbitration: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArbitrationPolicy(BaseModel):
    """Policy describing how contested topics are arbitrated."""

    method: Literal["heuristic", "llm_single_judge", "llm_panel", "weighted_vote"] = "heuristic"
    judge_count: int = 1
    confidence_threshold_contested: float = 0.6
    confidence_threshold_strong: float = 0.75
    metadata: dict[str, Any] = Field(default_factory=dict)


class SynthesisPolicy(BaseModel):
    """Policy describing how post-arbitration synthesis is handled."""

    method: str = "passthrough"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TranscriptPolicy(BaseModel):
    """Policy describing how the debate transcript should be formatted."""

    format_id: str = "default"
    include_raw_inputs: bool = True
    output_locale: str = "en"   # default "en" — backward-compatible
    metadata: dict[str, Any] = Field(default_factory=dict)


class PersistencePolicy(BaseModel):
    """Declarative persistence hints for adapters."""

    persist_rounds: bool = False
    persist_verdicts: bool = False
    persist_transcript: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebateSpec(BaseModel):
    """A fully resolved debate specification."""

    namespace: str
    subject: DebateSubject
    participants: list[DebateParticipant]
    round_policy: RoundPolicy = Field(default_factory=RoundPolicy)
    arbitration_policy: ArbitrationPolicy = Field(default_factory=ArbitrationPolicy)
    synthesis_policy: SynthesisPolicy = Field(default_factory=SynthesisPolicy)
    transcript_policy: TranscriptPolicy = Field(default_factory=TranscriptPolicy)
    persistence_policy: PersistencePolicy = Field(default_factory=PersistencePolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)
