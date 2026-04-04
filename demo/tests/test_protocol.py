from pydantic import ValidationError
import pytest


def test_debate_event_accepts_supported_stage_types() -> None:
    from backend.protocol import DebateEvent

    event = DebateEvent(
        session_id="session-1",
        sequence=1,
        type="speaker_activated",
        phase="debate",
        payload={"speaker_id": "economist"},
    )

    assert event.type == "speaker_activated"
    assert event.payload["speaker_id"] == "economist"


def test_debate_event_rejects_unknown_type() -> None:
    from backend.protocol import DebateEvent

    with pytest.raises(ValidationError):
        DebateEvent(
            session_id="session-1",
            sequence=1,
            type="banana",
            phase="debate",
            payload={},
        )


def test_session_action_request_requires_known_action() -> None:
    from backend.protocol import SessionActionRequest

    action = SessionActionRequest(action="request_verdict", payload={})
    assert action.action == "request_verdict"
