from __future__ import annotations

import pathlib
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from backend.protocol import (
    ActionAckResponse,
    SessionActionRequest,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionReplayResponse,
)

_FRONTEND = pathlib.Path(__file__).parent.parent / "frontend" / "dist"


def create_app(director: Any = None) -> FastAPI:
    _app = FastAPI(title="Agentic Debate Demo")

    @_app.post("/api/sessions", response_model=None)
    async def create_session(request: SessionCreateRequest) -> dict[str, str]:
        result = await director.create_session(request)
        if isinstance(result, dict):
            return result
        return result.model_dump()

    @_app.get("/api/sessions/{session_id}/events")
    async def stream_events(session_id: str) -> EventSourceResponse:
        if director is None:
            async def _empty():
                return
                yield  # make it a generator
        else:
            queue = director.store.subscribe(session_id)

            async def _stream():
                try:
                    while True:
                        event = await queue.get()
                        if event is None:
                            break
                        yield {"data": event.model_dump_json()}
                finally:
                    director.store.unsubscribe(session_id, queue)

        return EventSourceResponse(_stream() if director else _empty())

    @_app.post("/api/sessions/{session_id}/actions")
    async def post_action(
        session_id: str, request: SessionActionRequest
    ) -> ActionAckResponse:
        return await director.handle_action(session_id, request)

    @_app.get("/api/sessions/{session_id}/replay")
    async def get_replay(session_id: str) -> SessionReplayResponse:
        return director.store.get_replay(session_id)

    if _FRONTEND.exists():
        _app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="static")

    return _app


from backend.director import DebateDirector
from backend.gemini import GeminiLlmCaller
from backend.session_store import SessionStore

_store = SessionStore()
_director = DebateDirector(store=_store, llm=GeminiLlmCaller())
app = create_app(director=_director)
