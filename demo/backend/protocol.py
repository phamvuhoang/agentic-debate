from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DebateEventType = Literal[
    "debate_created",
    "agent_summoned",
    "speaker_activated",
    "argument_started",
    "argument_completed",
    "challenge_issued",
    "rebuttal_started",
    "consensus_shifted",
    "judge_intervened",
    "round_closed",
    "verdict_requested",
    "verdict_revealed",
    "debate_paused",
    "debate_resumed",
    "error_raised",
    "action_acknowledged",
]

DebatePhase = Literal["idle", "summoning", "debate", "clash", "verdict", "complete", "error"]
SessionActionType = Literal[
    "pause_debate",
    "resume_debate",
    "focus_agent",
    "inject_challenge",
    "redirect_debate",
    "advance_round",
    "request_verdict",
    "move_camera",
]


class SessionCreateRequest(BaseModel):
    topic: str
    output_locale: str = "en"
    participant_count: int | None = Field(default=None, ge=2, le=10)
    round_count: int | None = Field(default=None, ge=1, le=5)


class SessionCreateResponse(BaseModel):
    session_id: str
    events_url: str
    actions_url: str
    replay_url: str


class DebateEvent(BaseModel):
    session_id: str
    sequence: int
    type: DebateEventType
    phase: DebatePhase
    payload: dict[str, Any] = Field(default_factory=dict)


class SessionActionRequest(BaseModel):
    action: SessionActionType
    payload: dict[str, Any] = Field(default_factory=dict)


class ActionAckResponse(BaseModel):
    session_id: str
    accepted: bool
    action: SessionActionType
    sequence: int


class SessionReplayResponse(BaseModel):
    session_id: str
    events: list[DebateEvent]
