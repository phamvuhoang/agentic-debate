# Cinematic Round Table UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current A2UI card-stream demo with a desktop-first, interactive Three.js chamber that renders debate sessions from a typed event protocol and supports live directing controls.

**Architecture:** Convert the demo backend from UI-fragment streaming to a session-oriented event API. A `DebateDirector` publishes typed debate events into an in-memory session store with replay markers and action acknowledgements. The frontend becomes a Vite + TypeScript + Three.js application with a reducer-driven session store; both the scene runtime and DOM overlays consume the same canonical event state so the chamber stays cinematic while readable text remains precise.

**Tech Stack:** Python 3.12, FastAPI, sse-starlette, Pydantic v2, google-genai, agentic-debate package APIs, TypeScript, Vite, Three.js, Vitest, jsdom, CSS custom properties

---

## File Map

```text
demo/backend/
  constants.py                    # chamber palette, event/action constants, seat metadata defaults
  gemini.py                       # GeminiLlmCaller + GeminiLocalizer (keep as provider adapter)
  planning.py                     # attach chamber-specific participant metadata (seat index, accent, emblem)
  protocol.py                     # request/response/event/action/replay models
  session_store.py                # in-memory session registry, SSE fanout, replay buffers, action log
  observer.py                     # engine observer that maps arbitration lifecycle to stage events
  director.py                     # session orchestration over planner/compiler/engine + event publication
  main.py                         # FastAPI app factory, session routes, static serving
  streamer.py                     # delete after typed-event migration

demo/frontend/
  index.html                      # root mount only; no fixed toolbar markup
  package.json                    # add Three.js, TypeScript, Vitest; remove A2UI/Lit runtime dependency
  package-lock.json               # updated lockfile after dependency change
  tsconfig.json                   # TypeScript compiler config
  vite.config.js                  # proxy `/api/*` routes and Vitest config
  main.js                         # delete after TS migration
  style.css                       # delete after CSS module migration
  src/
    main.ts                       # app entrypoint
    app/
      bootstrap.ts                # assemble transport, store, scene, overlay, fallback
      session-controller.ts       # start sessions, subscribe to events, send actions, hydrate replay
      preferences.ts              # reduced-motion, desktop/mobile, WebGL capability checks
    transport/
      protocol.ts                 # frontend mirror of backend event/action shapes
      live-session-client.ts      # create session, connect SSE stream, send control actions
      replay-client.ts            # request timeline replay/snapshots
    state/
      types.ts                    # session state types
      event-reducer.ts            # canonical event reducer
      store.ts                    # subscribe/dispatch wrapper
      selectors.ts                # scene/overlay selectors
    scene/
      renderer.ts                 # owns WebGL renderer lifecycle
      chamber-scene.ts            # scene graph root and object composition
      camera-controller.ts        # named camera presets and transitions
      animation-orchestrator.ts   # motion priority rules + cue resolution
      objects/
        round-table.ts            # center table mesh + state-driven visual cues
        speaker-seat.ts           # seat mesh + focus/challenge/idle states
        atmosphere.ts             # ambient particles, fog, and room lighting helpers
    overlay/
      prompt-bar.ts               # idle-state invocation console
      speaker-banner.ts           # active speaker label + thesis
      caption-panel.ts            # readable current text / verdict copy
      timeline-rail.ts            # key-beat scrubber
      director-dock.ts            # pause, challenge, redirect, verdict, camera controls
    fallback/
      fallback-shell.ts           # 2D presentation when WebGL is unavailable
    styles/
      tokens.css                  # visual tokens
      app.css                     # layout, overlays, responsive behavior

demo/tests/
  test_protocol.py                # protocol model validation
  test_session_store.py           # queue fanout, replay buffers, action acknowledgement
  test_director.py                # event sequence emitted from real debate orchestration
  test_main.py                    # FastAPI routes and SSE contract
  test_streamer.py                # delete; obsolete after A2UI removal
  test_frontend_controls.py       # delete; replaced by frontend Vitest coverage

demo/frontend/src/
  transport/protocol.test.ts
  state/event-reducer.test.ts
  app/session-controller.test.ts
  app/bootstrap.test.ts
  scene/animation-orchestrator.test.ts
  overlay/director-dock.test.ts

README.md                         # update demo description from Lit + A2UI to Three.js chamber demo
demo/README.md                    # update setup/run instructions and architecture notes
docs/superpowers/specs/2026-04-03-cinematic-round-table-ui-design.md
```

---

### Task 1: Define the typed demo protocol

**Files:**
- Create: `demo/backend/protocol.py`
- Create: `demo/tests/test_protocol.py`

- [ ] **Step 1: Write the failing protocol tests**

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd demo && python -m pytest tests/test_protocol.py -v`  
Expected: `ModuleNotFoundError: No module named 'backend.protocol'`

- [ ] **Step 3: Implement the protocol models**

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd demo && python -m pytest tests/test_protocol.py -v`  
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add demo/backend/protocol.py demo/tests/test_protocol.py
git commit -m "feat(demo): add typed debate session protocol"
```

---

### Task 2: Add a session store and app factory around the new protocol

**Files:**
- Create: `demo/backend/session_store.py`
- Modify: `demo/backend/main.py`
- Create: `demo/tests/test_session_store.py`
- Modify: `demo/tests/test_main.py`

- [ ] **Step 1: Write the failing store and route tests**

```python
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.protocol import DebateEvent


@pytest.mark.asyncio
async def test_session_store_replays_events_in_sequence() -> None:
    from backend.session_store import SessionStore

    store = SessionStore()
    session_id = store.create_session()
    store.publish(
        DebateEvent(
            session_id=session_id,
            sequence=1,
            type="debate_created",
            phase="idle",
            payload={"topic": "Should AI replace doctors?"},
        )
    )

    replay = store.get_replay(session_id)
    assert replay.events[0].type == "debate_created"


@pytest.mark.asyncio
async def test_create_session_route_returns_session_urls() -> None:
    from backend.main import create_app

    class _FakeDirector:
        async def create_session(self, request):
            return {
                "session_id": "session-1",
                "events_url": "/api/sessions/session-1/events",
                "actions_url": "/api/sessions/session-1/actions",
                "replay_url": "/api/sessions/session-1/replay",
            }

    app = create_app(director=_FakeDirector())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/sessions", json={"topic": "test topic"})

    assert response.status_code == 200
    assert response.json()["events_url"].endswith("/events")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd demo && python -m pytest tests/test_session_store.py tests/test_main.py -v`  
Expected: import failures for `SessionStore` and `create_app`

- [ ] **Step 3: Implement the store and app factory**

```python
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

    def get_replay(self, session_id: str) -> SessionReplayResponse:
        return SessionReplayResponse(session_id=session_id, events=self._events[session_id])
```

```python
def create_app(director: DebateDirector | None = None) -> FastAPI:
    app = FastAPI(title="Agentic Debate Demo")

    @app.post("/api/sessions")
    async def create_session(request: SessionCreateRequest) -> SessionCreateResponse:
        return await director.create_session(request)

    @app.get("/api/sessions/{session_id}/events")
    async def stream_events(session_id: str) -> EventSourceResponse:
        return EventSourceResponse(_stream_session_events(session_id))

    @app.post("/api/sessions/{session_id}/actions")
    async def post_action(session_id: str, request: SessionActionRequest) -> ActionAckResponse:
        return await director.handle_action(session_id, request)

    return app
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd demo && python -m pytest tests/test_session_store.py tests/test_main.py -v`  
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add demo/backend/session_store.py demo/backend/main.py demo/tests/test_session_store.py demo/tests/test_main.py
git commit -m "feat(demo): add session store and session routes"
```

---

### Task 3: Replace A2UI streaming with a typed debate director

**Files:**
- Create: `demo/backend/observer.py`
- Create: `demo/backend/director.py`
- Modify: `demo/backend/planning.py`
- Modify: `demo/backend/constants.py`
- Modify: `demo/backend/main.py`
- Delete: `demo/backend/streamer.py`
- Create: `demo/tests/test_director.py`
- Delete: `demo/tests/test_streamer.py`

- [ ] **Step 1: Write the failing director tests**

```python
from __future__ import annotations

import pytest

from backend.protocol import SessionCreateRequest


@pytest.mark.asyncio
async def test_director_publishes_stage_events_in_order() -> None:
    from backend.director import DebateDirector
    from backend.session_store import SessionStore

    director = DebateDirector(
        store=SessionStore(),
        llm=_FakeDemoLlmCaller(),
    )

    response = await director.create_session(SessionCreateRequest(topic="Should AI replace doctors?"))
    replay = director.store.get_replay(response.session_id)

    assert replay.events[0].type == "debate_created"
    assert replay.events[1].type == "agent_summoned"
    assert replay.events[-1].type == "verdict_revealed"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd demo && python -m pytest tests/test_director.py -v`  
Expected: import failures for `DebateDirector`

- [ ] **Step 3: Implement the debate director and observer**

```python
class DebateStageObserver:
    def __init__(self, publish: Callable[[str, str, dict[str, Any]], None]) -> None:
        self._publish = publish

    async def on_event(self, event_type: str, payload: dict[str, Any], context: DebateContext) -> None:
        if event_type == "arbitration_started":
            self._publish("judge_intervened", "verdict", {"reason": "arbitration_started"})
```

```python
class DebateDirector:
    async def create_session(self, request: SessionCreateRequest) -> SessionCreateResponse:
        session_id = self.store.create_session()
        asyncio.create_task(self._run_session(session_id, request))
        return SessionCreateResponse(
            session_id=session_id,
            events_url=f"/api/sessions/{session_id}/events",
            actions_url=f"/api/sessions/{session_id}/actions",
            replay_url=f"/api/sessions/{session_id}/replay",
        )

    async def _run_session(self, session_id: str, request: SessionCreateRequest) -> None:
        self._publish(session_id, "debate_created", "idle", {"topic": request.topic})
        plan = await build_demo_plan(...)
        for participant in plan.participants:
            self._publish(session_id, "agent_summoned", "summoning", participant.metadata)
        # use on_challenge + observer hooks to publish round and verdict events
```

- [ ] **Step 4: Attach chamber metadata during planning**

```python
for index, participant in enumerate(decorated.participants):
    participant.metadata.setdefault("seat_index", index)
    participant.metadata.setdefault("accent_color", ACCENT_COLORS[index % len(ACCENT_COLORS)])
    participant.metadata.setdefault("emblem", f"sigil-{index + 1}")
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd demo && python -m pytest tests/test_director.py tests/test_main.py -v`  
Expected: all tests PASS and no imports reference `backend.streamer`

- [ ] **Step 6: Commit**

```bash
git add demo/backend/observer.py demo/backend/director.py demo/backend/planning.py demo/backend/constants.py demo/backend/main.py demo/tests/test_director.py demo/tests/test_main.py
git rm demo/backend/streamer.py demo/tests/test_streamer.py
git commit -m "feat(demo): publish typed debate events for chamber UI"
```

---

### Task 4: Migrate the frontend from A2UI to TypeScript + Three.js scaffolding

**Files:**
- Modify: `demo/frontend/package.json`
- Modify: `demo/frontend/package-lock.json`
- Modify: `demo/frontend/index.html`
- Modify: `demo/frontend/vite.config.js`
- Create: `demo/frontend/tsconfig.json`
- Create: `demo/frontend/src/main.ts`
- Create: `demo/frontend/src/transport/protocol.ts`
- Create: `demo/frontend/src/transport/protocol.test.ts`
- Delete: `demo/frontend/main.js`
- Delete: `demo/frontend/style.css`
- Delete: `demo/tests/test_frontend_controls.py`

- [ ] **Step 1: Write the failing frontend protocol test**

```ts
import { describe, expect, it } from 'vitest';
import { parseDebateEvent } from './protocol';

describe('parseDebateEvent', () => {
  it('accepts supported typed events', () => {
    const event = parseDebateEvent({
      session_id: 'session-1',
      sequence: 1,
      type: 'speaker_activated',
      phase: 'debate',
      payload: { speaker_id: 'economist' },
    });

    expect(event.type).toBe('speaker_activated');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd demo/frontend && npm run test -- src/transport/protocol.test.ts --run`  
Expected: missing script and/or missing module failures

- [ ] **Step 3: Update the frontend toolchain**

```json
{
  "name": "agentic-debate-demo",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "three": "^0.175.0"
  },
  "devDependencies": {
    "@types/three": "^0.175.0",
    "jsdom": "^26.0.0",
    "typescript": "^5.8.0",
    "vite": "^6.0.0",
    "vitest": "^3.1.0"
  }
}
```

```ts
export type DebateEventType =
  | 'debate_created'
  | 'agent_summoned'
  | 'speaker_activated'
  | 'argument_started'
  | 'argument_completed'
  | 'challenge_issued'
  | 'rebuttal_started'
  | 'consensus_shifted'
  | 'judge_intervened'
  | 'round_closed'
  | 'verdict_requested'
  | 'verdict_revealed'
  | 'debate_paused'
  | 'debate_resumed'
  | 'error_raised'
  | 'action_acknowledged';
```

- [ ] **Step 4: Create the minimal HTML and entrypoint**

```html
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
```

- [ ] **Step 5: Install dependencies and run the tests**

Run:

```bash
cd demo/frontend
npm install
npm run test -- src/transport/protocol.test.ts --run
npm run build
```

Expected: targeted test PASS and build succeeds

- [ ] **Step 6: Commit**

```bash
git add demo/frontend/package.json demo/frontend/package-lock.json demo/frontend/index.html demo/frontend/vite.config.js demo/frontend/tsconfig.json demo/frontend/src/main.ts demo/frontend/src/transport/protocol.ts demo/frontend/src/transport/protocol.test.ts
git rm demo/frontend/main.js demo/frontend/style.css demo/tests/test_frontend_controls.py
git commit -m "refactor(demo): migrate frontend shell to TypeScript and Three.js"
```

---

### Task 5: Implement the frontend reducer, selectors, and session controller

**Files:**
- Create: `demo/frontend/src/state/types.ts`
- Create: `demo/frontend/src/state/event-reducer.ts`
- Create: `demo/frontend/src/state/store.ts`
- Create: `demo/frontend/src/state/selectors.ts`
- Create: `demo/frontend/src/transport/live-session-client.ts`
- Create: `demo/frontend/src/transport/replay-client.ts`
- Create: `demo/frontend/src/app/session-controller.ts`
- Create: `demo/frontend/src/state/event-reducer.test.ts`
- Create: `demo/frontend/src/app/session-controller.test.ts`

- [ ] **Step 1: Write the failing reducer and controller tests**

```ts
import { describe, expect, it } from 'vitest';
import { reduceEvent, createInitialSessionState } from './event-reducer';

describe('reduceEvent', () => {
  it('tracks summoned agents, active speaker, and verdict state', () => {
    let state = createInitialSessionState();

    state = reduceEvent(state, {
      session_id: 'session-1',
      sequence: 1,
      type: 'agent_summoned',
      phase: 'summoning',
      payload: { participant_id: 'economist', label: 'Economist' },
    });
    state = reduceEvent(state, {
      session_id: 'session-1',
      sequence: 2,
      type: 'speaker_activated',
      phase: 'debate',
      payload: { speaker_id: 'economist' },
    });

    expect(state.participants).toHaveLength(1);
    expect(state.activeSpeakerId).toBe('economist');
  });
});
```

```ts
it('creates a session and subscribes to the event stream', async () => {
  const controller = new SessionController({
    liveClient: new FakeLiveSessionClient(),
    replayClient: new FakeReplayClient(),
    store,
  });

  await controller.startDebate('Should AI replace doctors?');

  expect(store.getState().sessionId).toBe('session-1');
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
cd demo/frontend
npm run test -- src/state/event-reducer.test.ts src/app/session-controller.test.ts --run
```

Expected: module import failures

- [ ] **Step 3: Implement the reducer and controller**

```ts
export interface SessionState {
  sessionId: string | null;
  phase: DebatePhase;
  participants: DebateParticipantView[];
  activeSpeakerId: string | null;
  captions: string[];
  timeline: TimelineBeat[];
  verdict: VerdictView | null;
}

export function reduceEvent(state: SessionState, event: DebateEvent): SessionState {
  switch (event.type) {
    case 'agent_summoned':
      return { ...state, phase: 'summoning', participants: [...state.participants, event.payload as DebateParticipantView] };
    case 'speaker_activated':
      return { ...state, phase: 'debate', activeSpeakerId: String(event.payload.speaker_id) };
    case 'verdict_revealed':
      return { ...state, phase: 'complete', verdict: event.payload as VerdictView };
    default:
      return state;
  }
}
```

```ts
export class SessionController {
  async startDebate(topic: string): Promise<void> {
    const session = await this.liveClient.createSession({ topic });
    this.store.dispatchSessionCreated(session.session_id);
    await this.hydrateReplay(session.replay_url);
    await this.liveClient.connect(session.events_url, (event) => this.store.dispatch(event));
  }

  async sendAction(action: SessionActionRequest): Promise<void> {
    await this.liveClient.sendAction(this.store.getState().sessionId!, action);
  }
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
cd demo/frontend
npm run test -- src/state/event-reducer.test.ts src/app/session-controller.test.ts --run
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add demo/frontend/src/state demo/frontend/src/transport/live-session-client.ts demo/frontend/src/transport/replay-client.ts demo/frontend/src/app/session-controller.ts demo/frontend/src/state/event-reducer.test.ts demo/frontend/src/app/session-controller.test.ts
git commit -m "feat(demo): add frontend session state and transport controller"
```

---

### Task 6: Build the chamber scene runtime and motion priority rules

**Files:**
- Create: `demo/frontend/src/scene/renderer.ts`
- Create: `demo/frontend/src/scene/chamber-scene.ts`
- Create: `demo/frontend/src/scene/camera-controller.ts`
- Create: `demo/frontend/src/scene/animation-orchestrator.ts`
- Create: `demo/frontend/src/scene/objects/round-table.ts`
- Create: `demo/frontend/src/scene/objects/speaker-seat.ts`
- Create: `demo/frontend/src/scene/objects/atmosphere.ts`
- Create: `demo/frontend/src/scene/animation-orchestrator.test.ts`

- [ ] **Step 1: Write the failing motion-priority test**

```ts
import { describe, expect, it } from 'vitest';
import { resolveCuePlan } from './animation-orchestrator';

describe('resolveCuePlan', () => {
  it('chooses a centered verdict lock instead of a camera flourish during verdict reveal', () => {
    const cue = resolveCuePlan(
      { type: 'verdict_revealed', phase: 'verdict', payload: {} },
      { reducedMotion: false, userReading: true }
    );

    expect(cue.cameraPreset).toBe('verdict-center');
    expect(cue.overlayMotion).toBe('minimal');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd demo/frontend && npm run test -- src/scene/animation-orchestrator.test.ts --run`  
Expected: module import failures

- [ ] **Step 3: Implement the scene runtime**

```ts
export function resolveCuePlan(event: DebateEvent, context: MotionContext): SceneCuePlan {
  if (event.type === 'verdict_revealed') {
    return {
      cameraPreset: 'verdict-center',
      tableMode: 'converged',
      seatMode: 'audience',
      overlayMotion: context.userReading ? 'minimal' : 'measured',
    };
  }

  if (event.type === 'challenge_issued') {
    return {
      cameraPreset: 'challenge-confrontation',
      tableMode: 'directional',
      seatMode: 'tension',
      overlayMotion: 'minimal',
    };
  }

  return {
    cameraPreset: 'speaker-focus',
    tableMode: 'focused',
    seatMode: 'active-speaker',
    overlayMotion: 'normal',
  };
}
```

```ts
export class ChamberScene {
  constructor(private readonly mount: HTMLElement) {
    this.scene = new THREE.Scene();
    this.table = createRoundTable();
    this.seats = [];
    this.scene.add(this.table.group);
  }

  applyState(view: SceneViewModel): void {
    this.table.apply(view.table);
    this.cameraController.applyPreset(view.cameraPreset);
    this.seats.forEach((seat) => seat.apply(view.seats[seat.id]));
  }
}
```

- [ ] **Step 4: Run the tests and a build**

Run:

```bash
cd demo/frontend
npm run test -- src/scene/animation-orchestrator.test.ts --run
npm run build
```

Expected: test PASS and build succeeds

- [ ] **Step 5: Commit**

```bash
git add demo/frontend/src/scene demo/frontend/src/scene/animation-orchestrator.test.ts
git commit -m "feat(demo): add chamber scene runtime and motion rules"
```

---

### Task 7: Build the overlay surfaces and director dock

**Files:**
- Create: `demo/frontend/src/overlay/prompt-bar.ts`
- Create: `demo/frontend/src/overlay/speaker-banner.ts`
- Create: `demo/frontend/src/overlay/caption-panel.ts`
- Create: `demo/frontend/src/overlay/timeline-rail.ts`
- Create: `demo/frontend/src/overlay/director-dock.ts`
- Create: `demo/frontend/src/styles/tokens.css`
- Create: `demo/frontend/src/styles/app.css`
- Create: `demo/frontend/src/overlay/director-dock.test.ts`

- [ ] **Step 1: Write the failing overlay test**

```ts
import { describe, expect, it, vi } from 'vitest';
import { renderDirectorDock } from './director-dock';

describe('renderDirectorDock', () => {
  it('emits a request_verdict action when the verdict button is clicked', () => {
    const onAction = vi.fn();
    const dock = renderDirectorDock({ onAction });

    dock.querySelector('[data-action="request_verdict"]')?.dispatchEvent(new MouseEvent('click'));

    expect(onAction).toHaveBeenCalledWith({ action: 'request_verdict', payload: {} });
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd demo/frontend && npm run test -- src/overlay/director-dock.test.ts --run`  
Expected: module import failure

- [ ] **Step 3: Implement the overlays**

```ts
export function renderDirectorDock(props: { onAction: (action: SessionActionRequest) => void }): HTMLElement {
  const root = document.createElement('aside');
  root.className = 'director-dock';

  for (const action of ['pause_debate', 'inject_challenge', 'advance_round', 'request_verdict'] as const) {
    const button = document.createElement('button');
    button.dataset.action = action;
    button.addEventListener('click', () => props.onAction({ action, payload: {} }));
    root.append(button);
  }

  return root;
}
```

```css
:root {
  --bg: #0b0908;
  --surface: rgba(22, 18, 16, 0.86);
  --border: rgba(206, 177, 116, 0.28);
  --text: #f3ead8;
  --accent: #d5a44a;
  --danger: #d35f5f;
}

.director-dock {
  position: absolute;
  right: 24px;
  bottom: 24px;
  display: grid;
  gap: 10px;
}
```

- [ ] **Step 4: Run the tests**

Run: `cd demo/frontend && npm run test -- src/overlay/director-dock.test.ts --run`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add demo/frontend/src/overlay demo/frontend/src/styles demo/frontend/src/overlay/director-dock.test.ts
git commit -m "feat(demo): add overlay surfaces and director controls"
```

---

### Task 8: Wire bootstrap, replay hydration, reduced motion, and the 2D fallback

**Files:**
- Create: `demo/frontend/src/app/bootstrap.ts`
- Create: `demo/frontend/src/app/preferences.ts`
- Create: `demo/frontend/src/fallback/fallback-shell.ts`
- Create: `demo/frontend/src/app/bootstrap.test.ts`
- Modify: `demo/frontend/src/main.ts`
- Modify: `demo/frontend/src/app/session-controller.ts`
- Modify: `demo/frontend/src/scene/renderer.ts`
- Modify: `demo/frontend/src/overlay/*`

- [ ] **Step 1: Write the failing bootstrap test**

```ts
import { describe, expect, it, vi } from 'vitest';
import { bootstrapApp } from './bootstrap';

describe('bootstrapApp', () => {
  it('falls back to the 2D shell when WebGL is unavailable', async () => {
    const mount = document.createElement('div');
    const result = await bootstrapApp(mount, { hasWebGL: false });

    expect(result.mode).toBe('fallback');
    expect(mount.textContent).toContain('Debate chamber unavailable');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd demo/frontend && npm run test -- src/app/bootstrap.test.ts --run`  
Expected: module import failure

- [ ] **Step 3: Implement bootstrap and fallback wiring**

```ts
export async function bootstrapApp(
  mount: HTMLElement,
  env: Partial<AppEnvironment> = {},
): Promise<{ mode: 'scene' | 'fallback' }> {
  const preferences = detectPreferences(env);

  if (!preferences.hasWebGL) {
    renderFallbackShell(mount);
    return { mode: 'fallback' };
  }

  const controller = new SessionController(...);
  const scene = new SceneRenderer(mount, preferences);
  const overlays = buildOverlayLayer(mount, controller);

  controller.subscribe((state) => {
    scene.render(selectSceneView(state, preferences));
    overlays.render(selectOverlayView(state));
  });

  return { mode: 'scene' };
}
```

- [ ] **Step 4: Run the tests and build**

Run:

```bash
cd demo/frontend
npm run test -- src/app/bootstrap.test.ts src/app/session-controller.test.ts src/scene/animation-orchestrator.test.ts src/overlay/director-dock.test.ts --run
npm run build
```

Expected: all targeted tests PASS and build succeeds

- [ ] **Step 5: Commit**

```bash
git add demo/frontend/src/app demo/frontend/src/fallback demo/frontend/src/main.ts demo/frontend/src/scene/renderer.ts demo/frontend/src/overlay
git commit -m "feat(demo): wire chamber app bootstrap with fallback behavior"
```

---

### Task 9: Update documentation, clean up old references, and run full verification

**Files:**
- Modify: `README.md`
- Modify: `demo/README.md`
- Modify: `demo/tests/conftest.py` (only if fixtures need updates for new routes)
- Modify: `demo/tests/test_gemini.py` / `demo/tests/test_intent.py` / `demo/tests/test_localization.py` as needed for renamed imports

- [ ] **Step 1: Update the demo documentation**

```md
- **Demo backend adapters**: Gemini adapter, session-oriented debate director, typed SSE events, replay endpoints
- **Demo frontend**: TypeScript + Three.js chamber scene with DOM overlays and fallback shell
```

Include these route changes in `demo/README.md`:

- `POST /api/sessions`
- `GET /api/sessions/{session_id}/events`
- `POST /api/sessions/{session_id}/actions`
- `GET /api/sessions/{session_id}/replay`

- [ ] **Step 2: Run the full Python test suite**

Run:

```bash
cd demo
python -m pytest tests -v
cd ..
python -m pytest tests -v
```

Expected: all demo and package tests PASS

- [ ] **Step 3: Run the full frontend verification**

Run:

```bash
cd demo/frontend
npm run test
npm run build
```

Expected: all Vitest suites PASS and production build succeeds

- [ ] **Step 4: Do a manual demo smoke test**

Run:

```bash
cd demo
uvicorn backend.main:app --reload
```

Manual checks:

- open the demo in a desktop browser
- start a debate and confirm idle -> summoning -> debate -> verdict transitions
- focus a speaker and request verdict from the director dock
- verify reduced-motion mode via browser dev tools or system preference
- confirm the 2D fallback renders if WebGL is disabled

- [ ] **Step 5: Commit**

```bash
git add README.md demo/README.md demo/tests
git commit -m "docs(demo): document cinematic round table experience"
```

---

## Notes For Execution

- Treat backend protocol changes and frontend shell replacement as one migration. Do not try to preserve the old `/debate` A2UI payload contract in parallel unless a hard requirement appears.
- Keep the reducer canonical. The scene and overlay should derive from selectors, not mutate each other directly.
- Favor testable pure functions for motion resolution, replay shaping, and event parsing. WebGL-heavy code should stay thin and state-driven.
- Do not bring React into this rewrite. Vite + TypeScript + Three.js + small DOM modules are sufficient here.
- Keep commits small and reversible. This is a large redesign, so checkpoint quality matters.
