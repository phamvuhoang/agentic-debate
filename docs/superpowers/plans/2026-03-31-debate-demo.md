# Agentic Debate Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained web demo where a user types any topic, Gemini dynamically generates a debate team and runs a structured debate using the `agentic-debate` library, streamed in real-time via A2UI Lit web components.

**Architecture:** FastAPI backend exposes a `POST /debate` SSE endpoint. A custom `LlmChallengeSource` generates arguments via Gemini one at a time, pushing each to an async queue. An `A2UIStreamObserver` (plus an `on_challenge` callback) translates debate events into A2UI JSON messages that the queue yields as SSE events. A Vite-built Lit frontend feeds each message to an A2UI `SignalMessageProcessor` connected to `<a2ui-surface>`, which renders the debate UI progressively.

**Tech Stack:** Python 3.12, FastAPI, sse-starlette, google-genai, agentic-debate (local editable), A2UI Lit (`@a2ui/lit`), Vite

---

## File Map

```
demo/
  backend/
    __init__.py          # empty
    gemini.py            # GeminiLlmCaller + IntentResult + intent_analysis() + generate_team()
    challenge_source.py  # LlmChallengeSource (ChallengeSource protocol)
    streamer.py          # A2UIStreamObserver + A2UI message builder helpers
    prompts.py           # All LLM prompt templates as string constants
    main.py              # FastAPI app — POST /debate SSE + static serving
  frontend/
    index.html           # <a2ui-surface> mount + input bar
    main.js              # SSE client + A2UI processor wiring + restart handler
    style.css            # Dark theme, glass input, verdict card gold border
    package.json         # @a2ui/lit, lit, vite
    vite.config.js       # Vite build config (outDir: dist)
  tests/
    __init__.py          # empty
    conftest.py          # shared fixtures: mock_llm_caller, sample_intent, sample_participants
    test_gemini.py       # GeminiLlmCaller + intent_analysis + generate_team
    test_challenge_source.py  # LlmChallengeSource
    test_streamer.py     # A2UI message format correctness
    test_main.py         # FastAPI SSE endpoint smoke test
  requirements.txt
```

---

## A2UI Message Format Reference (v0.8)

Every SSE `data:` payload is one of these JSON objects:

```json
// 1. Init surface (send first)
{"beginRendering": {"surfaceId": "debate-surface", "root": "debate_root"}}

// 2. Add/update components (send repeatedly to build UI progressively)
{
  "surfaceUpdate": {
    "surfaceId": "debate-surface",
    "components": [
      {"id": "debate_root", "component": {"Column": {"children": {"explicitList": ["card_a", "card_b"]}}}},
      {"id": "card_a", "component": {"Card": {"child": "card_a_col"}}},
      {"id": "card_a_col", "component": {"Column": {"children": {"explicitList": ["card_a_title", "card_a_body"]}}}},
      {"id": "card_a_title", "component": {"Text": {"text": {"literalString": "Hello"}, "usageHint": "h2"}}},
      {"id": "card_a_body", "component": {"Text": {"text": {"literalString": "World"}}}}
    ]
  }
}
```

**Progressive update pattern:** Each `surfaceUpdate` includes ALL currently visible root children in `debate_root`'s `explicitList`. Components already sent (identified by `id`) are replaced with the new definition if re-sent, or kept if omitted.

---

## Task 1: Demo project scaffold

**Files:**
- Create: `demo/backend/__init__.py`
- Create: `demo/tests/__init__.py`
- Create: `demo/requirements.txt`
- Create: `demo/frontend/package.json`
- Create: `demo/frontend/vite.config.js`

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p demo/backend demo/tests demo/frontend
touch demo/backend/__init__.py demo/tests/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

```
# demo/requirements.txt
fastapi>=0.115
uvicorn[standard]>=0.30
sse-starlette>=2.1
google-genai>=1.0
pydantic>=2.10
pytest>=8.0
pytest-asyncio>=0.24
httpx>=0.27
```

- [ ] **Step 3: Write frontend/package.json**

```json
{
  "name": "agentic-debate-demo",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@a2ui/lit": "latest",
    "lit": "^3.0.0"
  },
  "devDependencies": {
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 4: Write frontend/vite.config.js**

```js
// demo/frontend/vite.config.js
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: 'index.html',
    },
  },
})
```

- [ ] **Step 5: Install Python deps and verify agentic-debate installs**

```bash
cd demo
pip install -r requirements.txt
pip install -e ..
python -c "import agentic_debate; print('ok')"
```

Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add demo/
git commit -m "chore: scaffold demo project structure"
```

---

## Task 2: GeminiLlmCaller

**Files:**
- Create: `demo/backend/gemini.py`
- Create: `demo/tests/test_gemini.py`

- [ ] **Step 1: Write the failing test**

```python
# demo/tests/test_gemini.py
from __future__ import annotations
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from pydantic import BaseModel
from agentic_debate.context import DebateContext


class _SampleModel(BaseModel):
    name: str
    value: int


@pytest.fixture
def mock_genai_client():
    client = MagicMock()
    response = MagicMock()
    response.text = json.dumps({"name": "test", "value": 42})
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


@pytest.mark.asyncio
async def test_gemini_llm_caller_returns_parsed_model(mock_genai_client):
    from backend.gemini import GeminiLlmCaller
    caller = GeminiLlmCaller(client=mock_genai_client)
    ctx = DebateContext(namespace="test")
    result = await caller.generate_structured("prompt", _SampleModel, context=ctx)
    assert isinstance(result, _SampleModel)
    assert result.name == "test"
    assert result.value == 42


@pytest.mark.asyncio
async def test_gemini_llm_caller_passes_model_name(mock_genai_client):
    from backend.gemini import GeminiLlmCaller
    caller = GeminiLlmCaller(client=mock_genai_client, model="gemini-3-flash-preview")
    ctx = DebateContext(namespace="test")
    await caller.generate_structured("my prompt", _SampleModel, context=ctx)
    call_kwargs = mock_genai_client.aio.models.generate_content.call_args
    assert call_kwargs.kwargs["model"] == "gemini-3-flash-preview"
    assert call_kwargs.kwargs["contents"] == "my prompt"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd demo
python -m pytest tests/test_gemini.py -v
```

Expected: `ImportError: cannot import name 'GeminiLlmCaller' from 'backend.gemini'`

- [ ] **Step 3: Implement GeminiLlmCaller**

```python
# demo/backend/gemini.py
from __future__ import annotations

import os
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

from agentic_debate.context import DebateContext
from agentic_debate.llm.base import LlmCaller  # noqa: F401 (re-exported for type checkers)

T = TypeVar("T", bound=BaseModel)

MODEL = "gemini-3-flash-preview"
ACCENT_COLORS = ["#4F86C6", "#E05A5A", "#4CAF50", "#F5A623", "#9B59B6"]


class GeminiLlmCaller:
    """Implements LlmCaller using google-genai async client."""

    def __init__(
        self,
        client: genai.Client | None = None,
        model: str = MODEL,
    ) -> None:
        self._client = client or genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self._model = model

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        *,
        context: DebateContext,
    ) -> T:
        _ = context
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return response_model.model_validate_json(response.text)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd demo
python -m pytest tests/test_gemini.py -v
```

Expected: 2 PASSED

- [ ] **Step 5: Commit**

```bash
git add demo/backend/gemini.py demo/tests/test_gemini.py
git commit -m "feat(demo): add GeminiLlmCaller wrapping google-genai async client"
```

---

## Task 3: IntentResult, intent_analysis, generate_team

**Files:**
- Modify: `demo/backend/gemini.py` (add models + functions)
- Create: `demo/backend/prompts.py`
- Create: `demo/tests/test_intent.py`

- [ ] **Step 1: Write the failing tests**

```python
# demo/tests/test_intent.py
from __future__ import annotations
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from agentic_debate.context import DebateContext
from agentic_debate.types import DebateParticipant


def _make_caller(response_json: str):
    from backend.gemini import GeminiLlmCaller
    client = MagicMock()
    response = MagicMock()
    response.text = response_json
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return GeminiLlmCaller(client=client)


@pytest.mark.asyncio
async def test_intent_analysis_returns_intent_result():
    from backend.gemini import intent_analysis, IntentResult
    payload = {
        "reframed_topic": "Should AI replace doctors?",
        "domain": "healthcare",
        "controversy_level": "high",
        "recommended_participants": 4,
        "recommended_rounds": 3,
    }
    caller = _make_caller(json.dumps(payload))
    ctx = DebateContext(namespace="test")
    result = await intent_analysis("should AI replace doctors", caller, ctx)
    assert isinstance(result, IntentResult)
    assert result.recommended_participants == 4
    assert result.recommended_rounds == 3
    assert result.controversy_level == "high"


@pytest.mark.asyncio
async def test_intent_analysis_clamps_participants():
    from backend.gemini import intent_analysis
    # Gemini might return out-of-range values — they must be clamped
    payload = {
        "reframed_topic": "test",
        "domain": "test",
        "controversy_level": "low",
        "recommended_participants": 99,  # too high
        "recommended_rounds": 0,          # too low
    }
    caller = _make_caller(json.dumps(payload))
    ctx = DebateContext(namespace="test")
    result = await intent_analysis("test", caller, ctx)
    assert 2 <= result.recommended_participants <= 5
    assert 1 <= result.recommended_rounds <= 3


@pytest.mark.asyncio
async def test_generate_team_returns_correct_count():
    from backend.gemini import generate_team, IntentResult, ACCENT_COLORS
    raw_participants = [
        {"participant_id": f"p{i}", "label": f"Person {i}", "role": "debater", "stance": "pro"}
        for i in range(3)
    ]
    caller = _make_caller(json.dumps({"participants": raw_participants}))
    ctx = DebateContext(namespace="test")
    from backend.gemini import IntentResult
    intent = IntentResult(
        reframed_topic="test",
        domain="tech",
        controversy_level="medium",
        recommended_participants=3,
        recommended_rounds=2,
    )
    participants = await generate_team(intent, caller, ctx)
    assert len(participants) == 3
    assert all(isinstance(p, DebateParticipant) for p in participants)
    # Each participant's metadata has accent_color
    assert all("accent_color" in p.metadata for p in participants)
    assert participants[0].metadata["accent_color"] == ACCENT_COLORS[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd demo
python -m pytest tests/test_intent.py -v
```

Expected: `ImportError: cannot import name 'IntentResult' from 'backend.gemini'`

- [ ] **Step 3: Write prompts.py**

```python
# demo/backend/prompts.py

INTENT_PROMPT = """\
Analyze the following topic and return a JSON object with these fields:
- reframed_topic (str): a clear, debate-ready restatement of the topic
- domain (str): the primary domain (e.g. "healthcare", "politics", "technology", "ethics")
- controversy_level (str): one of "low", "medium", "high"
- recommended_participants (int): how many distinct viewpoints exist (between 2 and 5)
- recommended_rounds (int): how many debate rounds are appropriate (1 for low controversy, 2 for medium, 3 for high)

Topic: {topic}

Return only valid JSON.
"""

TEAM_PROMPT = """\
Generate a debate team for this topic: "{topic}"
Domain: {domain}
Number of participants: {n}

Return a JSON object with a "participants" array. Each participant has:
- participant_id (str): snake_case unique identifier (e.g. "climate_scientist")
- label (str): short display name (e.g. "Climate Scientist")
- role (str): their role in the debate (e.g. "expert", "advocate", "skeptic", "moderator")
- stance (str): their position on the topic in one sentence

Ensure participants represent genuinely different and interesting viewpoints.
Return only valid JSON.
"""

CHALLENGE_PROMPT = """\
You are {challenger_label} ({challenger_stance}).

Topic being debated: "{topic}"

Your opponent ({target_label}) has argued:
{prior_argument}

Write a compelling challenge or rebuttal in 2-4 sentences. Be direct, specific, and intellectually sharp.
Also assign:
- a "topic_tag" (str): a 2-5 word snake_case label for the sub-topic being challenged
- a "confidence" (float 0.0-1.0): how confident you are in your argument

Return JSON with fields: challenge_text, topic_tag, confidence
"""

FIRST_ROUND_CHALLENGE_PROMPT = """\
You are {challenger_label} ({challenger_stance}).

Topic being debated: "{topic}"

Open the debate by making your strongest argument in 2-4 sentences. Be direct and intellectually sharp.
Also assign:
- a "topic_tag" (str): a 2-5 word snake_case label for the sub-topic you are raising
- a "confidence" (float 0.0-1.0): how confident you are in your argument

Return JSON with fields: challenge_text, topic_tag, confidence
"""

JUDGE_PROMPT = """\
You are an impartial arbitrator evaluating an adversarial debate.

Participants:
{participants_json}

Challenges raised:
{challenges_json}

Valid winning_participant_id values (use exactly one of these per verdict):
{winning_options_json}

For each contested topic, return a verdict with:
- topic: the topic string
- winning_participant_id: one of the valid values above, or "unresolved"
- confidence: float 0.0-1.0
- rationale: explanation of the decision (2-3 sentences)
- open_questions: list of unresolved questions (0-3 items)
- consensus_level: "strong", "moderate", or "contested"

Return a JSON object with fields: verdicts, debate_summary, contested_topics.
"""
```

- [ ] **Step 4: Extend gemini.py with IntentResult, intent_analysis, generate_team**

```python
# demo/backend/gemini.py  — append after GeminiLlmCaller class
from __future__ import annotations

import os
from typing import Literal, TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from agentic_debate.context import DebateContext
from agentic_debate.types import DebateParticipant

T = TypeVar("T", bound=BaseModel)

MODEL = "gemini-3-flash-preview"
ACCENT_COLORS = ["#4F86C6", "#E05A5A", "#4CAF50", "#F5A623", "#9B59B6"]


class GeminiLlmCaller:
    """Implements LlmCaller using google-genai async client."""

    def __init__(
        self,
        client: genai.Client | None = None,
        model: str = MODEL,
    ) -> None:
        self._client = client or genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self._model = model

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        *,
        context: DebateContext,
    ) -> T:
        _ = context
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return response_model.model_validate_json(response.text)


class IntentResult(BaseModel):
    reframed_topic: str
    domain: str
    controversy_level: Literal["low", "medium", "high"]
    recommended_participants: int = Field(ge=2, le=5)
    recommended_rounds: int = Field(ge=1, le=3)


class _TeamResponse(BaseModel):
    participants: list[_ParticipantRaw]


class _ParticipantRaw(BaseModel):
    participant_id: str
    label: str
    role: str
    stance: str


async def intent_analysis(
    topic: str,
    llm: GeminiLlmCaller,
    context: DebateContext,
) -> IntentResult:
    from backend.prompts import INTENT_PROMPT
    prompt = INTENT_PROMPT.format(topic=topic)
    raw = await llm.generate_structured(prompt, IntentResult, context=context)
    # Clamp in case Gemini ignores bounds
    return IntentResult(
        reframed_topic=raw.reframed_topic,
        domain=raw.domain,
        controversy_level=raw.controversy_level,
        recommended_participants=max(2, min(5, raw.recommended_participants)),
        recommended_rounds=max(1, min(3, raw.recommended_rounds)),
    )


async def generate_team(
    intent: IntentResult,
    llm: GeminiLlmCaller,
    context: DebateContext,
) -> list[DebateParticipant]:
    from backend.prompts import TEAM_PROMPT
    prompt = TEAM_PROMPT.format(
        topic=intent.reframed_topic,
        domain=intent.domain,
        n=intent.recommended_participants,
    )
    raw = await llm.generate_structured(prompt, _TeamResponse, context=context)
    participants = raw.participants[: intent.recommended_participants]
    return [
        DebateParticipant(
            participant_id=p.participant_id,
            label=p.label,
            role=p.role,
            stance=p.stance,
            metadata={"accent_color": ACCENT_COLORS[i % len(ACCENT_COLORS)]},
        )
        for i, p in enumerate(participants)
    ]
```

> Note: The `_ParticipantRaw` and `_TeamResponse` classes must be defined BEFORE `generate_team` in the file. Full replacement of `gemini.py` with the complete file is required — do not patch incrementally.

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd demo
python -m pytest tests/test_gemini.py tests/test_intent.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add demo/backend/gemini.py demo/backend/prompts.py demo/tests/test_intent.py
git commit -m "feat(demo): add IntentResult, intent_analysis, generate_team"
```

---

## Task 4: LlmChallengeSource

**Files:**
- Create: `demo/backend/challenge_source.py`
- Create: `demo/tests/test_challenge_source.py`

- [ ] **Step 1: Write the failing tests**

```python
# demo/tests/test_challenge_source.py
from __future__ import annotations
import json
from typing import Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock
import pytest
from agentic_debate.context import DebateContext
from agentic_debate.spec import DebateSpec, RoundPolicy
from agentic_debate.types import DebateChallenge, DebateParticipant, DebateSubject


def _make_spec(n_participants: int = 3, max_rounds: int = 2) -> DebateSpec:
    return DebateSpec(
        namespace="test",
        subject=DebateSubject(kind="open_question", title="Test topic"),
        participants=[
            DebateParticipant(
                participant_id=f"p{i}",
                label=f"Person {i}",
                role="debater",
                stance=f"Stance {i}",
            )
            for i in range(n_participants)
        ],
        round_policy=RoundPolicy(mode="precomputed", max_rounds=max_rounds),
    )


def _make_caller(challenge_text: str = "My argument."):
    from backend.gemini import GeminiLlmCaller
    client = MagicMock()
    response = MagicMock()
    response.text = json.dumps({
        "challenge_text": challenge_text,
        "topic_tag": "test_topic",
        "confidence": 0.75,
    })
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return GeminiLlmCaller(client=client)


@pytest.mark.asyncio
async def test_collect_generates_n_participants_times_rounds():
    from backend.challenge_source import LlmChallengeSource
    spec = _make_spec(n_participants=3, max_rounds=2)
    source = LlmChallengeSource(llm=_make_caller())
    ctx = DebateContext(namespace="test")
    challenges = await source.collect(spec, ctx)
    assert len(challenges) == 6  # 3 participants × 2 rounds


@pytest.mark.asyncio
async def test_collect_sets_round_index():
    from backend.challenge_source import LlmChallengeSource
    spec = _make_spec(n_participants=2, max_rounds=2)
    source = LlmChallengeSource(llm=_make_caller())
    ctx = DebateContext(namespace="test")
    challenges = await source.collect(spec, ctx)
    round_indices = {c.round_index for c in challenges}
    assert round_indices == {1, 2}


@pytest.mark.asyncio
async def test_collect_uses_round_robin_targets():
    from backend.challenge_source import LlmChallengeSource
    spec = _make_spec(n_participants=3, max_rounds=1)
    source = LlmChallengeSource(llm=_make_caller())
    ctx = DebateContext(namespace="test")
    challenges = await source.collect(spec, ctx)
    # p0 challenges p1, p1 challenges p2, p2 challenges p0
    assert challenges[0].challenger_id == "p0"
    assert challenges[0].target_id == "p1"
    assert challenges[1].challenger_id == "p1"
    assert challenges[1].target_id == "p2"
    assert challenges[2].challenger_id == "p2"
    assert challenges[2].target_id == "p0"


@pytest.mark.asyncio
async def test_collect_fires_on_challenge_callback():
    from backend.challenge_source import LlmChallengeSource
    fired: list[DebateChallenge] = []

    async def on_challenge(c: DebateChallenge) -> None:
        fired.append(c)

    spec = _make_spec(n_participants=2, max_rounds=2)
    source = LlmChallengeSource(llm=_make_caller(), on_challenge=on_challenge)
    ctx = DebateContext(namespace="test")
    await source.collect(spec, ctx)
    assert len(fired) == 4  # 2 × 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd demo
python -m pytest tests/test_challenge_source.py -v
```

Expected: `ImportError: cannot import name 'LlmChallengeSource'`

- [ ] **Step 3: Implement LlmChallengeSource**

```python
# demo/backend/challenge_source.py
from __future__ import annotations

from typing import Awaitable, Callable
from pydantic import BaseModel

from agentic_debate.context import DebateContext
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateChallenge


class _ChallengeOutput(BaseModel):
    challenge_text: str
    topic_tag: str
    confidence: float


class LlmChallengeSource:
    """Generates DebateChallenge objects via Gemini, one per participant per round."""

    def __init__(
        self,
        llm: object,  # GeminiLlmCaller — avoids circular import
        on_challenge: Callable[[DebateChallenge], Awaitable[None]] | None = None,
    ) -> None:
        self._llm = llm
        self._on_challenge = on_challenge

    async def collect(self, spec: DebateSpec, context: DebateContext) -> list[DebateChallenge]:
        from backend.prompts import CHALLENGE_PROMPT, FIRST_ROUND_CHALLENGE_PROMPT

        participants = spec.participants
        n = len(participants)
        max_rounds = spec.round_policy.max_rounds
        challenges: list[DebateChallenge] = []
        # prior_args[participant_id] = last argument text they received
        prior_args: dict[str, str] = {}

        for round_idx in range(1, max_rounds + 1):
            for i, challenger in enumerate(participants):
                target = participants[(i + 1) % n]
                prior = prior_args.get(challenger.participant_id, "")

                if round_idx == 1 or not prior:
                    prompt = FIRST_ROUND_CHALLENGE_PROMPT.format(
                        challenger_label=challenger.label,
                        challenger_stance=challenger.stance or "neutral",
                        topic=spec.subject.title,
                    )
                else:
                    prompt = CHALLENGE_PROMPT.format(
                        challenger_label=challenger.label,
                        challenger_stance=challenger.stance or "neutral",
                        topic=spec.subject.title,
                        target_label=target.label,
                        prior_argument=prior,
                    )

                output: _ChallengeOutput = await self._llm.generate_structured(
                    prompt, _ChallengeOutput, context=context
                )
                challenge = DebateChallenge(
                    round_index=round_idx,
                    challenger_id=challenger.participant_id,
                    target_id=target.participant_id,
                    topic=output.topic_tag,
                    challenge_text=output.challenge_text,
                    confidence=max(0.0, min(1.0, output.confidence)),
                )
                challenges.append(challenge)
                prior_args[target.participant_id] = output.challenge_text

                if self._on_challenge is not None:
                    await self._on_challenge(challenge)

        return challenges
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd demo
python -m pytest tests/test_challenge_source.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add demo/backend/challenge_source.py demo/tests/test_challenge_source.py
git commit -m "feat(demo): add LlmChallengeSource generating arguments via Gemini"
```

---

## Task 5: A2UI message builders + A2UIStreamObserver

**Files:**
- Create: `demo/backend/streamer.py`
- Create: `demo/tests/test_streamer.py`

- [ ] **Step 1: Write the failing tests**

```python
# demo/tests/test_streamer.py
from __future__ import annotations
import asyncio
import json
import pytest
from agentic_debate.context import DebateContext
from agentic_debate.types import (
    DebateArbitration,
    DebateChallenge,
    DebateParticipant,
    DebateVerdict,
)


def _ctx() -> DebateContext:
    return DebateContext(namespace="test")


def test_begin_rendering_format():
    from backend.streamer import begin_rendering_msg
    msg = json.loads(begin_rendering_msg("debate-surface", "debate_root"))
    assert "beginRendering" in msg
    assert msg["beginRendering"]["surfaceId"] == "debate-surface"
    assert msg["beginRendering"]["root"] == "debate_root"


def test_status_card_is_valid_surface_update():
    from backend.streamer import status_card_msg
    msg = json.loads(status_card_msg("Analyzing...", ["debate_root"]))
    assert "surfaceUpdate" in msg
    components = {c["id"]: c for c in msg["surfaceUpdate"]["components"]}
    assert "debate_root" in components
    # debate_root must have a Column with children
    col = components["debate_root"]["component"]["Column"]
    assert "status_card" in col["children"]["explicitList"]


def test_argument_card_includes_participant_name():
    from backend.streamer import argument_card_msg
    participants = [
        DebateParticipant(
            participant_id="alice",
            label="Alice",
            role="debater",
            stance="pro",
            metadata={"accent_color": "#4F86C6"},
        ),
        DebateParticipant(
            participant_id="bob",
            label="Bob",
            role="debater",
            stance="con",
            metadata={"accent_color": "#E05A5A"},
        ),
    ]
    challenge = DebateChallenge(
        round_index=1,
        challenger_id="alice",
        target_id="bob",
        topic="ai_safety",
        challenge_text="AI poses existential risks.",
        confidence=0.8,
    )
    existing_children = ["topic_card"]
    msg = json.loads(argument_card_msg(challenge, participants, existing_children))
    raw = json.dumps(msg)
    assert "Alice" in raw
    assert "AI poses existential risks." in raw


def test_verdict_card_includes_winner_and_rationale():
    from backend.streamer import verdict_card_msg
    participants = [
        DebateParticipant(participant_id="alice", label="Alice", role="debater"),
        DebateParticipant(participant_id="bob", label="Bob", role="debater"),
    ]
    arbitration = DebateArbitration(
        verdicts=[
            DebateVerdict(
                topic="ai_safety",
                winning_participant_id="alice",
                confidence=0.85,
                rationale="Alice provided stronger evidence.",
                open_questions=["What about edge cases?"],
                consensus_level="moderate",
            )
        ],
        summary="Alice won the debate.",
        contested_topics=["ai_safety"],
    )
    existing_children = ["topic_card", "arg_r1_alice"]
    msg = json.loads(verdict_card_msg(arbitration, participants, existing_children))
    raw = json.dumps(msg)
    assert "Alice" in raw
    assert "Alice provided stronger evidence." in raw


@pytest.mark.asyncio
async def test_observer_enqueues_on_event():
    from backend.streamer import A2UIStreamObserver
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    participants = [
        DebateParticipant(participant_id="p1", label="P1", role="debater"),
    ]
    observer = A2UIStreamObserver(queue=queue, participants=participants)
    ctx = _ctx()
    await observer.on_event("round_started", {"namespace": "test"}, ctx)
    # round_started should not enqueue anything (it's handled differently)
    assert queue.empty()

    await observer.on_event("arbitration_started", {"topic_count": 2}, ctx)
    msg = await queue.get()
    assert msg is not None
    data = json.loads(msg)
    assert "surfaceUpdate" in data
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd demo
python -m pytest tests/test_streamer.py -v
```

Expected: `ImportError: cannot import name 'begin_rendering_msg'`

- [ ] **Step 3: Implement streamer.py**

```python
# demo/backend/streamer.py
from __future__ import annotations

import asyncio
import json
from typing import Any

from agentic_debate.context import DebateContext
from agentic_debate.types import (
    DebateArbitration,
    DebateChallenge,
    DebateParticipant,
    DebateVerdict,
)

SURFACE_ID = "debate-surface"
ROOT_ID = "debate_root"


# ── Low-level component helpers ───────────────────────────────────────────────

def _text(uid: str, text: str, hint: str = "body") -> dict[str, Any]:
    return {"id": uid, "component": {"Text": {"text": {"literalString": text}, "usageHint": hint}}}


def _column(uid: str, children: list[str]) -> dict[str, Any]:
    return {"id": uid, "component": {"Column": {"children": {"explicitList": children}}}}


def _card(uid: str, child_id: str) -> dict[str, Any]:
    return {"id": uid, "component": {"Card": {"child": child_id}}}


def _button(uid: str, label: str, action_name: str, child_id: str) -> dict[str, Any]:
    return {
        "id": uid,
        "component": {
            "Button": {
                "child": child_id,
                "action": {"name": action_name, "context": []},
            }
        },
    }


def _surface_update(components: list[dict[str, Any]]) -> str:
    return json.dumps({"surfaceUpdate": {"surfaceId": SURFACE_ID, "components": components}})


# ── Public message builders ───────────────────────────────────────────────────

def begin_rendering_msg(surface_id: str, root_id: str) -> str:
    return json.dumps({"beginRendering": {"surfaceId": surface_id, "root": root_id}})


def status_card_msg(text: str, existing_children: list[str]) -> str:
    children = [c for c in existing_children if c != "status_card"] + ["status_card"]
    return _surface_update([
        _column(ROOT_ID, children),
        _card("status_card", "status_text"),
        _text("status_text", text, "h3"),
    ])


def topic_card_msg(
    reframed_topic: str,
    domain: str,
    controversy_level: str,
    existing_children: list[str],
) -> str:
    children = [c for c in existing_children if c not in ("status_card", "topic_card")] + ["topic_card"]
    controversy_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(controversy_level, "⚪")
    meta = f"{controversy_emoji} {controversy_level.capitalize()} controversy · {domain.capitalize()}"
    return _surface_update([
        _column(ROOT_ID, children),
        _card("topic_card", "topic_col"),
        _column("topic_col", ["topic_title", "topic_meta"]),
        _text("topic_title", reframed_topic, "h2"),
        _text("topic_meta", meta, "body"),
    ])


def participant_intro_card_msg(
    participant: DebateParticipant,
    existing_children: list[str],
) -> str:
    uid = f"p_intro_{participant.participant_id}"
    children = existing_children + [uid]
    color = participant.metadata.get("accent_color", "#888")
    label = f"{color_emoji(color)} {participant.label}"
    stance_text = participant.stance or "—"
    return _surface_update([
        _column(ROOT_ID, children),
        _card(uid, f"{uid}_col"),
        _column(f"{uid}_col", [f"{uid}_name", f"{uid}_role", f"{uid}_stance"]),
        _text(f"{uid}_name", label, "h3"),
        _text(f"{uid}_role", participant.role.capitalize(), "body"),
        _text(f"{uid}_stance", f'"{stance_text}"', "body"),
    ])


def round_header_msg(round_index: int, existing_children: list[str]) -> str:
    uid = f"round_{round_index}_hdr"
    children = existing_children + [uid]
    return _surface_update([
        _column(ROOT_ID, children),
        _text(uid, f"── Round {round_index} ──", "h2"),
    ])


def argument_card_msg(
    challenge: DebateChallenge,
    participants: list[DebateParticipant],
    existing_children: list[str],
) -> str:
    uid = f"arg_r{challenge.round_index}_{challenge.challenger_id}"
    children = existing_children + [uid]
    pid_map = {p.participant_id: p for p in participants}
    challenger = pid_map.get(challenge.challenger_id)
    target = pid_map.get(challenge.target_id)
    color = challenger.metadata.get("accent_color", "#888") if challenger else "#888"
    name = challenger.label if challenger else challenge.challenger_id
    target_name = target.label if target else challenge.target_id
    conf_pct = int(challenge.confidence * 100)
    footer = f"→ challenges {target_name}  ·  {conf_pct}% confidence"
    return _surface_update([
        _column(ROOT_ID, children),
        _card(uid, f"{uid}_col"),
        _column(f"{uid}_col", [f"{uid}_name", f"{uid}_body", f"{uid}_footer"]),
        _text(f"{uid}_name", f"{color_emoji(color)} {name}", "h3"),
        _text(f"{uid}_body", challenge.challenge_text, "body"),
        _text(f"{uid}_footer", footer, "body"),
    ])


def arbitrating_msg(existing_children: list[str]) -> str:
    children = existing_children + ["arbitrating_card"]
    return _surface_update([
        _column(ROOT_ID, children),
        _card("arbitrating_card", "arbitrating_text"),
        _text("arbitrating_text", "⚖️ Judge is deliberating…", "h3"),
    ])


def verdict_card_msg(
    arbitration: DebateArbitration,
    participants: list[DebateParticipant],
    existing_children: list[str],
) -> str:
    pid_map = {p.participant_id: p for p in participants}
    children = [c for c in existing_children if c != "arbitrating_card"] + ["verdict_card"]

    verdict_child_ids = ["verdict_summary"]
    components: list[dict[str, Any]] = [
        _text("verdict_summary", f"📋 {arbitration.summary}", "h3"),
    ]
    for i, v in enumerate(arbitration.verdicts):
        vid = f"verdict_item_{i}"
        winner = pid_map.get(v.winning_participant_id)
        winner_name = winner.label if winner else v.winning_participant_id
        conf_pct = int(v.confidence * 100)
        verdict_text = f"🏆 {winner_name} ({conf_pct}%) — {v.rationale}"
        verdict_child_ids.append(vid)
        components.append(_text(vid, verdict_text, "body"))
        for j, q in enumerate(v.open_questions):
            qid = f"verdict_item_{i}_q{j}"
            verdict_child_ids.append(qid)
            components.append(_text(qid, f"❓ {q}", "body"))

    if arbitration.contested_topics:
        cid = "verdict_contested"
        verdict_child_ids.append(cid)
        components.append(_text(cid, "⚡ Contested: " + ", ".join(arbitration.contested_topics), "body"))

    btn_uid = "restart_btn"
    btn_label_uid = "restart_btn_label"
    verdict_child_ids.append(btn_uid)
    components.append(_button(btn_uid, "Ask another question", "restart_debate", btn_label_uid))
    components.append(_text(btn_label_uid, "Ask another question", "body"))

    return _surface_update([
        _column(ROOT_ID, children),
        _card("verdict_card", "verdict_col"),
        _column("verdict_col", verdict_child_ids),
        *components,
    ])


def error_card_msg(message: str, existing_children: list[str]) -> str:
    children = existing_children + ["error_card"]
    return _surface_update([
        _column(ROOT_ID, children),
        _card("error_card", "error_text"),
        _text("error_text", f"❌ {message}", "h3"),
    ])


def color_emoji(hex_color: str) -> str:
    mapping = {
        "#4F86C6": "🔵",
        "#E05A5A": "🔴",
        "#4CAF50": "🟢",
        "#F5A623": "🟡",
        "#9B59B6": "🟣",
    }
    return mapping.get(hex_color, "⚪")


# ── Observer ──────────────────────────────────────────────────────────────────

class A2UIStreamObserver:
    """Translates engine lifecycle events into A2UI messages on an asyncio queue."""

    def __init__(
        self,
        queue: asyncio.Queue[str | None],
        participants: list[DebateParticipant],
    ) -> None:
        self._queue = queue
        self._participants = participants
        self._children: list[str] = []

    def _enqueue(self, msg: str) -> None:
        self._queue.put_nowait(msg)

    async def on_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        context: DebateContext,
    ) -> None:
        _ = (payload, context)
        if event_type == "arbitration_started":
            msg = arbitrating_msg(self._children)
            self._children = list(json.loads(msg)["surfaceUpdate"]["components"][0]["component"]["Column"]["children"]["explicitList"])
            self._enqueue(msg)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd demo
python -m pytest tests/test_streamer.py -v
```

Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add demo/backend/streamer.py demo/tests/test_streamer.py
git commit -m "feat(demo): add A2UI message builders and A2UIStreamObserver"
```

---

## Task 6: FastAPI SSE endpoint

**Files:**
- Create: `demo/backend/main.py`
- Create: `demo/tests/test_main.py`
- Create: `demo/tests/conftest.py`

- [ ] **Step 1: Write conftest.py and failing test**

```python
# demo/tests/conftest.py
from __future__ import annotations
import json
import os
import pytest

os.environ.setdefault("GEMINI_API_KEY", "test-key")
```

```python
# demo/tests/test_main.py
from __future__ import annotations
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_debate_endpoint_returns_sse_stream():
    # Patch GeminiLlmCaller to avoid real API calls
    intent_payload = json.dumps({
        "reframed_topic": "Test topic",
        "domain": "test",
        "controversy_level": "low",
        "recommended_participants": 2,
        "recommended_rounds": 1,
    })
    team_payload = json.dumps({
        "participants": [
            {"participant_id": "p0", "label": "Alice", "role": "debater", "stance": "pro"},
            {"participant_id": "p1", "label": "Bob", "role": "debater", "stance": "con"},
        ]
    })
    challenge_payload = json.dumps({"challenge_text": "My arg.", "topic_tag": "topic", "confidence": 0.7})
    judge_payload = json.dumps({
        "verdicts": [{"topic": "topic", "winning_participant_id": "p0", "confidence": 0.8,
                      "rationale": "P0 won.", "open_questions": [], "consensus_level": "strong"}],
        "debate_summary": "Good debate.",
        "contested_topics": [],
    })

    responses = [intent_payload, team_payload, challenge_payload, challenge_payload, judge_payload]
    call_count = 0

    async def fake_generate(*args, **kwargs):
        nonlocal call_count
        resp = MagicMock()
        resp.text = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return resp

    mock_client = MagicMock()
    mock_client.aio = MagicMock()
    mock_client.aio.models = MagicMock()
    mock_client.aio.models.generate_content = fake_generate

    with patch("backend.main.genai") as mock_genai:
        mock_genai.Client.return_value = mock_client
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            async with ac.stream("POST", "/debate", json={"topic": "test topic"}) as resp:
                assert resp.status_code == 200
                assert "text/event-stream" in resp.headers["content-type"]
                lines = []
                async for line in resp.aiter_lines():
                    lines.append(line)
                    if len(lines) > 5:
                        break
                data_lines = [l for l in lines if l.startswith("data:")]
                assert len(data_lines) >= 1
                first = json.loads(data_lines[0].removeprefix("data:").strip())
                assert "beginRendering" in first
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd demo
python -m pytest tests/test_main.py -v
```

Expected: `ImportError: cannot import name 'app'` or similar

- [ ] **Step 3: Implement main.py**

```python
# demo/backend/main.py
from __future__ import annotations

import asyncio
import json
import logging
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from google import genai

from agentic_debate.compile import DebateCompiler
from agentic_debate.context import DebateContext
from agentic_debate.engine import DebateEngine
from agentic_debate.methods.grouping import GroupByTopicStrategy
from agentic_debate.methods.synthesis.passthrough import PassthroughSynthesizer
from agentic_debate.methods.transcript import SimpleTranscriptFormatter
from agentic_debate.methods.arbitration.llm_single_judge import LlmSingleJudgeArbitrator
from agentic_debate.spec import ArbitrationPolicy, DebateSpec, RoundPolicy
from agentic_debate.types import DebateChallenge, DebateSubject

from backend.gemini import GeminiLlmCaller, intent_analysis, generate_team
from backend.challenge_source import LlmChallengeSource
from backend.streamer import (
    A2UIStreamObserver,
    SURFACE_ID,
    ROOT_ID,
    begin_rendering_msg,
    status_card_msg,
    topic_card_msg,
    participant_intro_card_msg,
    round_header_msg,
    argument_card_msg,
    verdict_card_msg,
    error_card_msg,
)
from backend.prompts import JUDGE_PROMPT

_logger = logging.getLogger(__name__)
_FRONTEND = pathlib.Path(__file__).parent.parent / "frontend" / "dist"

app = FastAPI(title="Agentic Debate Demo")


class DebateRequest(BaseModel):
    topic: str


@app.post("/debate")
async def debate(request: DebateRequest) -> EventSourceResponse:
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def run() -> None:
        children: list[str] = []

        def enqueue(msg: str) -> None:
            queue.put_nowait(msg)
            nonlocal children
            parsed = json.loads(msg)
            if "surfaceUpdate" in parsed:
                root_comp = next(
                    (c for c in parsed["surfaceUpdate"]["components"] if c["id"] == ROOT_ID),
                    None,
                )
                if root_comp and "Column" in root_comp["component"]:
                    children = list(
                        root_comp["component"]["Column"]["children"]["explicitList"]
                    )

        try:
            # Init surface
            enqueue(begin_rendering_msg(SURFACE_ID, ROOT_ID))
            enqueue(status_card_msg("Analyzing your question…", children))

            llm = GeminiLlmCaller()
            ctx = DebateContext(namespace="demo")

            # Intent analysis
            intent = await intent_analysis(request.topic, llm, ctx)
            enqueue(topic_card_msg(
                intent.reframed_topic, intent.domain, intent.controversy_level, children
            ))

            # Team generation
            enqueue(status_card_msg("Assembling debate team…", children))
            participants = await generate_team(intent, llm, ctx)
            for participant in participants:
                enqueue(participant_intro_card_msg(participant, children))
                await asyncio.sleep(0.1)  # stagger reveal

            # Track round for headers
            current_round = 0

            async def on_challenge(challenge: DebateChallenge) -> None:
                nonlocal current_round
                if challenge.round_index != current_round:
                    current_round = challenge.round_index
                    enqueue(round_header_msg(current_round, children))
                enqueue(argument_card_msg(challenge, participants, children))

            # Build and run debate
            observer = A2UIStreamObserver(queue=queue, participants=participants)
            observer._children = children  # share children state

            challenge_source = LlmChallengeSource(llm=llm, on_challenge=on_challenge)
            compiler = DebateCompiler(
                challenge_source=challenge_source,
                grouping=GroupByTopicStrategy(),
                arbitrator=LlmSingleJudgeArbitrator(llm=llm, prompt_template=JUDGE_PROMPT),
                synthesizer=PassthroughSynthesizer(),
                transcript_formatter=SimpleTranscriptFormatter(),
                observers=[observer],
            )
            spec = DebateSpec(
                namespace="demo",
                subject=DebateSubject(kind="open_question", title=intent.reframed_topic),
                participants=participants,
                round_policy=RoundPolicy(mode="precomputed", max_rounds=intent.recommended_rounds),
                arbitration_policy=ArbitrationPolicy(method="llm_single_judge"),
            )
            compiled = await compiler.compile(spec, context=ctx)
            run_result = await DebateEngine().run(compiled, context=ctx)

            enqueue(verdict_card_msg(run_result.arbitration, participants, children))

        except Exception as exc:
            _logger.exception("debate_run_failed")
            queue.put_nowait(error_card_msg(str(exc), children))
        finally:
            queue.put_nowait(None)  # sentinel

    asyncio.create_task(run())

    async def stream():
        while True:
            msg = await queue.get()
            if msg is None:
                break
            yield {"data": msg}

    return EventSourceResponse(stream())


# Serve built frontend (only if dist exists)
if _FRONTEND.exists():
    app.mount("/", StaticFiles(directory=str(_FRONTEND), html=True), name="static")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd demo
python -m pytest tests/test_main.py -v
```

Expected: PASSED

- [ ] **Step 5: Commit**

```bash
git add demo/backend/main.py demo/tests/test_main.py demo/tests/conftest.py
git commit -m "feat(demo): add FastAPI SSE endpoint wiring full debate pipeline"
```

---

## Task 7: Frontend HTML + CSS

**Files:**
- Create: `demo/frontend/index.html`
- Create: `demo/frontend/style.css`

- [ ] **Step 1: Write index.html**

```html
<!-- demo/frontend/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Agentic Debate</title>
  <link rel="stylesheet" href="/style.css" />
</head>
<body>
  <div id="app">
    <header id="header">
      <div id="header-inner">
        <span id="logo">⚔️ Agentic Debate</span>
        <div id="input-row">
          <input
            id="topic-input"
            type="text"
            placeholder="Ask anything — the debate team will be auto-assembled…"
            autocomplete="off"
          />
          <button id="submit-btn">Debate</button>
        </div>
      </div>
    </header>
    <main id="surface-container">
      <a2ui-surface id="debate-surface"></a2ui-surface>
    </main>
  </div>
  <script type="module" src="/main.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write style.css**

```css
/* demo/frontend/style.css */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0f0f0f;
  --surface: #1a1a1a;
  --border: #2a2a2a;
  --text: #e8e8e8;
  --muted: #888;
  --accent: #4F86C6;
  --gold: #f0c040;
  --header-h: 72px;
  --radius: 10px;
}

html, body { height: 100%; background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; }

#app { display: flex; flex-direction: column; height: 100%; }

/* ── Header ── */
#header {
  position: fixed; top: 0; left: 0; right: 0; height: var(--header-h);
  background: rgba(15,15,15,0.80);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  z-index: 100;
}
#header-inner {
  max-width: 860px; margin: 0 auto; height: 100%;
  display: flex; align-items: center; gap: 16px; padding: 0 16px;
}
#logo { font-size: 1.1rem; font-weight: 700; white-space: nowrap; }

#input-row { display: flex; gap: 8px; flex: 1; }

#topic-input {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 0.95rem;
  padding: 10px 14px;
  outline: none;
  transition: border-color 0.2s;
}
#topic-input:focus { border-color: var(--accent); }

#submit-btn {
  background: var(--accent);
  border: none;
  border-radius: var(--radius);
  color: #fff;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  padding: 10px 20px;
  transition: opacity 0.2s;
  white-space: nowrap;
}
#submit-btn:hover { opacity: 0.88; }
#submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── Surface container ── */
#surface-container {
  margin-top: var(--header-h);
  flex: 1;
  overflow-y: auto;
  padding: 24px 16px 48px;
  max-width: 860px;
  width: 100%;
  align-self: center;
}

/* ── A2UI overrides ── */
a2ui-surface { display: block; }

/* Cards */
a2ui-card {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  margin-bottom: 12px !important;
  padding: 16px !important;
}

/* Verdict card — golden border */
a2ui-card[id="verdict_card"] {
  border-color: var(--gold) !important;
  border-width: 2px !important;
}

/* Text sizing */
a2ui-text[usage-hint="h2"] { font-size: 1.2rem; font-weight: 700; margin-bottom: 6px; }
a2ui-text[usage-hint="h3"] { font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
a2ui-text[usage-hint="body"] { font-size: 0.9rem; color: var(--muted); line-height: 1.5; }

/* Buttons */
a2ui-button {
  margin-top: 12px !important;
  background: var(--accent) !important;
  border-radius: var(--radius) !important;
  cursor: pointer !important;
}
```

- [ ] **Step 3: Commit**

```bash
git add demo/frontend/index.html demo/frontend/style.css
git commit -m "feat(demo): add frontend HTML and dark theme CSS"
```

---

## Task 8: Frontend JS (main.js)

**Files:**
- Create: `demo/frontend/main.js`

- [ ] **Step 1: Verify @a2ui/lit processor API after npm install**

```bash
cd demo/frontend
npm install
node -e "import('@a2ui/lit').then(m => console.log(Object.keys(m)))"
```

Look for the processor factory. Common names: `createSignalA2uiMessageProcessor`, `Data`, `MessageProcessor`.
Adjust the `PROCESSOR_FACTORY` constant in the next step if needed.

- [ ] **Step 2: Write main.js**

```js
// demo/frontend/main.js
import * as a2ui from '@a2ui/lit';

// Register A2UI custom elements (auto-registers a2ui-surface, a2ui-card, etc.)
// The import above registers elements as a side-effect.

const SURFACE_ID = 'debate-surface';

// Create the reactive message processor
// NOTE: verify exact factory name from npm install output above
const processor = a2ui.Data
  ? a2ui.Data.createSignalA2uiMessageProcessor()
  : a2ui.createSignalA2uiMessageProcessor
    ? a2ui.createSignalA2uiMessageProcessor()
    : new a2ui.A2uiMessageProcessor();

// Wire processor to <a2ui-surface>
const surfaceEl = document.getElementById(SURFACE_ID);
surfaceEl.processor = processor;
surfaceEl.surfaceId = SURFACE_ID;

const topicInput = document.getElementById('topic-input');
const submitBtn = document.getElementById('submit-btn');

function setRunning(running) {
  submitBtn.disabled = running;
  topicInput.disabled = running;
}

function resetSurface() {
  if (processor.clearSurfaces) processor.clearSurfaces();
  else if (processor.reset) processor.reset();
}

async function startDebate(topic) {
  setRunning(true);
  resetSurface();

  let response;
  try {
    response = await fetch('/debate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic }),
    });
  } catch (err) {
    console.error('fetch failed', err);
    setRunning(false);
    return;
  }

  if (!response.ok) {
    console.error('debate endpoint error', response.status);
    setRunning(false);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line

      for (const line of lines) {
        if (!line.startsWith('data:')) continue;
        const raw = line.slice(5).trim();
        if (!raw || raw === '[DONE]') continue;
        try {
          const msg = JSON.parse(raw);
          // Feed into A2UI processor
          if (processor.processMessage) processor.processMessage(msg);
          else if (processor.process) processor.process(msg);
          else processor.onMessage?.(msg);
        } catch (e) {
          console.warn('failed to parse SSE message', raw, e);
        }
      }
    }
  } finally {
    setRunning(false);
  }
}

// Submit handler
submitBtn.addEventListener('click', () => {
  const topic = topicInput.value.trim();
  if (!topic) return;
  startDebate(topic);
});

topicInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') submitBtn.click();
});

// Handle A2UI action events (e.g., restart button)
surfaceEl.addEventListener('a2uiaction', (event) => {
  const { name } = event.detail || {};
  if (name === 'restart_debate') {
    topicInput.value = '';
    topicInput.focus();
    resetSurface();
    setRunning(false);
  }
});
```

- [ ] **Step 3: Commit**

```bash
git add demo/frontend/main.js
git commit -m "feat(demo): add frontend JS with SSE client and A2UI surface wiring"
```

---

## Task 9: Build, run, and smoke test

**Files:** No new files — integration verification

- [ ] **Step 1: Run all backend tests**

```bash
cd demo
python -m pytest tests/ -v
```

Expected: all PASSED

- [ ] **Step 2: Build frontend**

```bash
cd demo/frontend
npm run build
ls dist/
```

Expected: `dist/` contains `index.html`, `assets/*.js`, `assets/*.css`

- [ ] **Step 3: Start the server**

```bash
cd demo
GEMINI_API_KEY=<your_key> uvicorn backend.main:app --reload --port 8000
```

Expected: `Uvicorn running on http://127.0.0.1:8000`

- [ ] **Step 4: Smoke test the SSE endpoint via curl**

```bash
curl -s -N -X POST http://localhost:8000/debate \
  -H "Content-Type: application/json" \
  -d '{"topic":"Should remote work be permanent?"}' | head -30
```

Expected output (first few lines):
```
data: {"beginRendering": {"surfaceId": "debate-surface", "root": "debate_root"}}

data: {"surfaceUpdate": {"surfaceId": "debate-surface", "components": [...]}}

data: {"surfaceUpdate": ...}
```

- [ ] **Step 5: Open browser and test end-to-end**

Open `http://localhost:8000` in a browser.
- Type any topic (e.g., "Is social media good for democracy?")
- Click **Debate**
- UI should build progressively: status → topic reveal → participant cards → argument cards → verdict

- [ ] **Step 6: Fix any A2UI processor API mismatches found in Step 5**

If the surface does not render, open browser DevTools → Console. Common fixes:
- Wrong processor factory: check `Object.keys(a2ui)` in the console and update `main.js`
- Wrong message method: check A2UI source in `node_modules/@a2ui/lit/` for `processMessage` vs `process`

- [ ] **Step 7: Final commit**

```bash
git add demo/
git commit -m "feat(demo): complete agentic debate demo with A2UI progressive streaming"
```

---

## Self-Review Checklist

| Spec requirement | Covered by |
|---|---|
| User types topic | Task 7 (index.html input) + Task 8 (submitBtn handler) |
| Intent analyzed by Gemini | Task 3 (intent_analysis) |
| Debate team auto-generated (dynamic count 2–5) | Task 3 (generate_team) |
| Dynamic round count (1–3) | Task 3 (IntentResult) + Task 6 (DebateSpec) |
| LlmChallengeSource generates arguments | Task 4 |
| Streaming via SSE | Task 6 (EventSourceResponse) + Task 8 (ReadableStream) |
| Progressive A2UI rendering | Task 5 (message builders) + Task 8 (processMessage) |
| Per-participant color coding | Task 5 (color_emoji + accent_color metadata) |
| Round headers | Task 5 (round_header_msg) + Task 6 (on_challenge) |
| Confidence badges | Task 5 (argument_card_msg footer) |
| LlmSingleJudgeArbitrator verdict | Task 6 (main.py arbitrator) |
| Verdict card with open questions | Task 5 (verdict_card_msg) |
| Restart button | Task 5 (verdict_card_msg) + Task 8 (a2uiaction handler) |
| Error display | Task 5 (error_card_msg) + Task 6 (except block) |
| Dark theme CSS | Task 7 (style.css) |
| Setup & run docs | Task 1 (requirements.txt) + Task 9 |
