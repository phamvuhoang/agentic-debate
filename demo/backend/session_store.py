from __future__ import annotations

import asyncio
from uuid import uuid4

from backend.protocol import DebateEvent, SessionActionRequest, SessionReplayResponse


class SessionStore:
    def __init__(self) -> None:
        self._events: dict[str, list[DebateEvent]] = {}
        self._listeners: dict[str, list[asyncio.Queue[DebateEvent | None]]] = {}
        self._actions: dict[str, list[SessionActionRequest]] = {}

    def create_session(self) -> str:
        session_id = uuid4().hex
        self._events[session_id] = []
        self._listeners[session_id] = []
        self._actions[session_id] = []
        return session_id

    def publish(self, event: DebateEvent) -> None:
        self._events[event.session_id].append(event)
        for queue in self._listeners[event.session_id]:
            queue.put_nowait(event)

    def subscribe(self, session_id: str) -> asyncio.Queue[DebateEvent | None]:
        queue: asyncio.Queue[DebateEvent | None] = asyncio.Queue()
        self._listeners[session_id].append(queue)
        return queue

    def unsubscribe(self, session_id: str, queue: asyncio.Queue[DebateEvent | None]) -> None:
        try:
            self._listeners[session_id].remove(queue)
        except (KeyError, ValueError):
            pass

    def get_replay(self, session_id: str) -> SessionReplayResponse:
        return SessionReplayResponse(
            session_id=session_id,
            events=self._events.get(session_id, []),
        )

    def log_action(self, session_id: str, action: SessionActionRequest) -> None:
        self._actions.setdefault(session_id, []).append(action)
