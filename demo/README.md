# Agentic Debate Demo — Setup & Run

This directory contains a self-contained web demo of the `agentic-debate` package. The demo is intentionally thin: it uses the installable planning and challenge-generation APIs from `src/agentic_debate` and adds only the Gemini adapter, a session-oriented debate director, typed SSE events, and a Three.js chamber UI.

## Architecture

The demo is split into three layers:

- **Package layer**: `LlmDebatePlanner`, `LlmChallengeSource`, `DebateCompiler`, and `DebateEngine`
- **Demo backend adapters**: Gemini adapter, session-oriented debate director, typed SSE events, replay endpoints
- **Demo frontend**: TypeScript + Three.js chamber scene with DOM overlays and fallback shell

```mermaid
graph TD
    Topic([User topic]) --> API["POST /api/sessions"]
    API --> Director["DebateDirector"]
    Director --> Gemini["GeminiLlmCaller"]
    Gemini --> Planner["LlmDebatePlanner (package)"]
    Planner --> Decorator["build_demo_plan()"]
    Decorator --> Spec["DebateSpec"]
    Gemini --> ChallengeSource["LlmChallengeSource (package)"]
    Spec --> Compiler["DebateCompiler"]
    ChallengeSource --> Compiler
    Compiler --> Engine["DebateEngine"]
    Engine --> Observer["DebateStageObserver"]
    Observer --> Store["SessionStore (SSE fanout)"]
    Store --> Browser["Three.js chamber frontend"]
```

### Backend Responsibilities

- `backend/gemini.py`: provider adapter and translation/localization helper
- `backend/planning.py`: calls package `LlmDebatePlanner` and adds seat index, accent color, and emblem metadata
- `backend/protocol.py`: Pydantic models for typed debate events and session actions
- `backend/session_store.py`: in-memory session registry with SSE queue fanout and replay buffers
- `backend/observer.py`: maps engine lifecycle events to typed stage events
- `backend/director.py`: session orchestration over planner/compiler/engine + event publication
- `backend/main.py`: FastAPI app factory with session routes and static serving

### API Routes

- `POST /api/sessions` — create a new debate session, returns session URLs
- `GET /api/sessions/{session_id}/events` — SSE stream of typed `DebateEvent` objects
- `POST /api/sessions/{session_id}/actions` — send a director action (pause, verdict, etc.)
- `GET /api/sessions/{session_id}/replay` — fetch full event replay for a session

### Frontend Responsibilities

- `src/main.ts`: app entrypoint
- `src/app/bootstrap.ts`: assemble transport, store, scene, overlay, fallback
- `src/app/session-controller.ts`: start sessions, subscribe to events, send actions, hydrate replay
- `src/state/event-reducer.ts`: canonical event reducer
- `src/scene/`: Three.js chamber scene runtime (renderer, camera, seats, table, atmosphere)
- `src/overlay/`: DOM overlay surfaces (prompt bar, speaker banner, captions, director dock)
- `src/fallback/`: 2D presentation when WebGL is unavailable

## Using `agentic-debate` in Another Codebase

This demo is not the public API. If you want to embed the debate system in another codebase, import from `agentic_debate`, not from `demo/backend/*`.

The integration pattern is:

1. implement `LlmCaller` for your provider
2. call `LlmDebatePlanner` to convert a topic into a `DebatePlan`
3. call `plan.to_spec(namespace=...)`
4. compile with `LlmChallengeSource`, grouping, arbitrator, synthesizer, and transcript formatter
5. run with `DebateEngine`

Minimal example:

```python
from agentic_debate import (
    DebateCompiler,
    DebateContext,
    DebateEngine,
    GroupByTopicStrategy,
    LlmChallengeSource,
    LlmDebatePlanner,
    LlmSingleJudgeArbitrator,
    PassthroughSynthesizer,
    SimpleTranscriptFormatter,
)
from agentic_debate.prompts import load_builtin_judge_prompt

ctx = DebateContext(namespace="my-app")
llm = MyLlmCaller()

plan = await LlmDebatePlanner(llm=llm).plan_topic(
    "Should AI replace doctors?",
    context=ctx,
)
spec = plan.to_spec(namespace="my-app")

compiler = DebateCompiler(
    challenge_source=LlmChallengeSource(llm=llm),
    grouping=GroupByTopicStrategy(),
    arbitrator=LlmSingleJudgeArbitrator(
        llm=llm,
        prompt_template=load_builtin_judge_prompt(),
    ),
    synthesizer=PassthroughSynthesizer(),
    transcript_formatter=SimpleTranscriptFormatter(),
)

result = await DebateEngine().run(await compiler.compile(spec), context=ctx)
```

## Prerequisites

- **Python 3.12+**
- **Node.js & npm** (for building the frontend)
- **Gemini API Key**: You need a valid API key from Google AI Studio.

## Step-by-Step Setup

### 1. Configure the Backend

Navigate to the `demo` directory and install the Python dependencies:

```bash
cd demo
pip install -r requirements.txt
pip install -e ..
```

### 2. Build the Frontend

Vite is used to build the TypeScript + Three.js frontend assets. These are served as static files by FastAPI.

```bash
cd frontend
npm install
npm run build
cd ..
```

### 3. Set Environment Variables

Export your Gemini API key:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 4. Run the Application

Start the FastAPI server using `uvicorn`:

```bash
uvicorn backend.main:app --reload
```

The application will be available at [http://localhost:8000](http://localhost:8000).

## 🛠️ Development Mode

For a better development experience with hot-reloading for both backend and frontend:

1. **Start Backend**: in one terminal, run `uvicorn backend.main:app --reload` in the `demo` directory
2. **Start Frontend**: in another terminal, run `npm run dev` in the `demo/frontend` directory
3. **Access**: open [http://localhost:5173](http://localhost:5173); the frontend proxies `/api` to the backend on port 8000

> [!NOTE]
> If you get an `Address already in use` error for port 8000, find and kill the process using:
> `lsof -i :8000` then `kill -9 <PID>`

## 🧪 Running Tests

To verify the backend implementation, you can run the test suite:

```bash
cd demo
python -m pytest tests/
```

## Features Demonstrated

- **Package-native planning**: topic -> `DebatePlan` -> `DebateSpec`
- **Package-native challenge generation**: generated opening arguments and rebuttals
- **Typed session events**: all debate lifecycle events modelled as `DebateEvent` with phase tracking
- **Session-oriented API**: create/replay/stream sessions; send director control actions
- **Three.js chamber scene**: cinematic round-table with seat states, camera presets, and motion rules
- **DOM overlays**: prompt bar, speaker banner, caption panel, timeline rail, director dock
- **Reduced-motion support**: orchestrator respects `prefers-reduced-motion` and `userReading` state
- **2D fallback shell**: graceful degradation when WebGL is unavailable
- **LLM-backed arbitration**: final verdict generated from the package judge flow
