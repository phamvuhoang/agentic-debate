# Agentic Debate Demo — Design Spec

**Date:** 2026-03-31  
**Status:** Approved

---

## Overview

A self-contained web demo where a user types any topic or question, and the system:
1. Analyzes intent with Gemini
2. Auto-generates a debate team (size determined by analysis)
3. Runs a structured debate (rounds determined by analysis) using the `agentic-debate` library
4. Streams the entire debate in real-time to a browser via A2UI (Lit web components)

The UI builds itself progressively — each debater's argument, status update, and final verdict appears the moment it's generated.

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Gemini (`gemini-3-flash-preview`) via `google-genai` SDK |
| Backend | FastAPI + `sse-starlette` (SSE streaming) |
| Debate engine | `agentic-debate` library (this repo) |
| Frontend | A2UI Lit (`@a2ui/lit`) — `<a2ui-surface>` web component |
| Serving | FastAPI serves static frontend files |

---

## File Structure

```
demo/
  backend/
    main.py             # FastAPI app — POST /debate SSE endpoint + static serving
    gemini.py           # GeminiLlmCaller (implements LlmCaller protocol)
                        # + intent_analysis() + generate_team() functions
    challenge_source.py # LlmChallengeSource — calls Gemini to generate each
                        # participant's argument as a DebateChallenge
    streamer.py         # A2UIStreamObserver — listens to DebateObserver events,
                        # builds A2UI JSON messages, puts them on an asyncio.Queue
  frontend/
    index.html          # Topic input bar + <a2ui-surface> mount
    main.js             # SSE client, connects surface to stream, handles restart
    style.css           # Layout + accent color overrides
    package.json        # { "@a2ui/lit": "latest" }
  requirements.txt      # fastapi, uvicorn, sse-starlette, google-genai, pydantic>=2.10
```

The `agentic-debate` library is installed as a local editable dependency from the parent directory (`pip install -e ..`).

---

## Backend: SSE Endpoint

```
POST /debate
Content-Type: application/json
Body: { "topic": "<user input>" }

Response: text/event-stream (JSONL — one A2UI message per SSE event)
```

### Stream sequence

```
1.  beginRendering            → initialize surface "debate-surface"
2.  surfaceUpdate (Card)      → "Analyzing your question..." status card
3.  [Gemini: intent analysis]
4.  surfaceUpdate (Card)      → topic reveal card with domain badge + controversy level
5.  [Gemini: team generation]
6.  surfaceUpdate (Card) ×3   → participant intro cards, staggered (100ms delay)
                                 each shows: name, role, stance label, accent color
7.  surfaceUpdate (Text)      → "Round 1" section header
8.  For each round (1–2):
      For each participant (sequential within round):
        [Gemini: generate argument]
        surfaceUpdate (Card)  → argument card:
                                  header = participant name (colored)
                                  body   = argument text
                                  footer = confidence badge + "challenges: <target>"
9.  [LlmSingleJudgeArbitrator: arbitrate]
10. surfaceUpdate (Card)      → verdict card (gold accent):
                                  winner name + rationale
                                  contested topics list
                                  open questions
11. surfaceUpdate (Button)    → "Ask another question" restart button
```

### Error handling

If any Gemini call fails, emit a `surfaceUpdate` error card with message, then close the stream. The frontend shows the error inline without crashing.

---

## Backend: Modules

### `gemini.py`

**`GeminiLlmCaller`** — implements `LlmCaller` protocol from `agentic-debate`:
- `generate_structured(prompt, response_model, *, context)` — calls Gemini with structured output (JSON mode), parses into `response_model` (Pydantic)

**`intent_analysis(topic, llm) -> IntentResult`**:
- Returns: `{reframed_topic: str, domain: str, controversy_level: "low"|"medium"|"high", recommended_participants: int, recommended_rounds: int}`
- `recommended_participants`: 2–5, chosen by Gemini based on topic complexity and how many distinct viewpoints exist
- `recommended_rounds`: 1–3, chosen based on controversy level (low → 1, medium → 2, high → 3)
- These values are passed into `DebateSpec` and drive the rest of the run — nothing else is hardcoded

**`generate_team(intent, llm) -> list[DebateParticipant]`**:
- Returns `intent.recommended_participants` participants, each with: `participant_id`, `label`, `role`, `stance`
- Accent colors assigned from a palette of 5: `#4F86C6`, `#E05A5A`, `#4CAF50`, `#F5A623`, `#9B59B6`

### `challenge_source.py`

**`LlmChallengeSource`** — implements `ChallengeSource` protocol:
- `collect(spec, context)` — for each participant, calls Gemini to generate one `DebateChallenge` targeting the next participant (round-robin)
- In round 2: prior arguments passed in context metadata so Gemini can rebut

### `streamer.py`

**`A2UIStreamObserver`** — implements `DebateObserver` protocol:
- `on_event(event_type, payload, context)` — translates debate lifecycle events into A2UI JSON messages
- Puts messages onto an `asyncio.Queue[str]`
- `main.py` consumes from queue and yields SSE events

A2UI message format used (v0.8 stable):
```json
{"type": "surfaceUpdate", "surfaceId": "debate-surface", "components": [...]}
```

### `main.py`

- Mounts `frontend/dist/` as static files
- `POST /debate`: validates body, builds `DebateSpec`, instantiates compiler + engine, runs `engine.run()` while streaming queue output as SSE

---

## Frontend

### `index.html`

```html
<div id="app">
  <header>
    <input id="topic-input" placeholder="Ask anything to debate..." />
    <button id="submit-btn">Debate</button>
  </header>
  <a2ui-surface id="debate-surface"></a2ui-surface>
</div>
```

### `main.js`

- On submit: `POST /debate` → opens SSE reader (fetch + ReadableStream)
- Each SSE event data → parsed as JSON → dispatched to `<a2ui-surface>` via its message API
- On restart button action event: clears surface, re-enables input
- Handles SSE stream close (debate complete) and errors

### `style.css`

- Dark background (`#0f0f0f`) — makes colored participant cards pop
- Cards with 1px colored left-border matching participant accent color
- Verdict card: `border: 2px solid gold`, slightly larger text
- Input bar: full-width, fixed at top, blurred glass effect
- A2UI surface fills remaining viewport height, scrollable

---

## Debate Configuration

```python
DebateSpec(
    namespace="demo",
    subject=DebateSubject(kind="open_question", title=intent.reframed_topic),
    participants=generated_team,           # N participants — from intent analysis
    round_policy=RoundPolicy(
        mode="precomputed",
        max_rounds=intent.recommended_rounds,  # 1–3 — from intent analysis
    ),
    arbitration_policy=ArbitrationPolicy(method="llm_single_judge"),
)
```

`PrecomputedChallengeSource` is replaced by `LlmChallengeSource`.  
`LlmSingleJudgeArbitrator` uses `GeminiLlmCaller`.

---

## Out-of-the-box Features

| Feature | Implementation |
|---|---|
| Auto-generated debate team | Gemini determines participant count (2–5) and generates personas |
| Progressive streaming | Every card appears the moment Gemini finishes generating it |
| Per-participant color coding | Fixed 3-color palette, consistent across all cards |
| Dynamic rounds | Gemini determines round count (1–3) based on controversy level |
| Round headers | `Text` component injected before each round |
| Confidence badges | Derived from `DebateChallenge.confidence` float |
| Arbitration verdict | `LlmSingleJudgeArbitrator` → styled verdict card |
| Contested topics | Listed in verdict card from `DebateArbitration.contested_topics` |
| Open questions | From `DebateVerdict.open_questions` |
| Restart flow | Button action event → surface cleared, input re-enabled |
| Error display | Inline error card, stream closed cleanly |

---

## Setup & Run

```bash
# Install Python deps
cd demo
pip install -r requirements.txt
pip install -e ..

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Run
GEMINI_API_KEY=<key> uvicorn backend.main:app --reload
# Open http://localhost:8000
```

---

## Out of Scope

- Auth / rate limiting
- Persistence (no debate history stored)
- Multi-language output
- Mobile-specific layout
- More than 5 participants or more than 3 rounds
