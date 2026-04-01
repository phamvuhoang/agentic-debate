# Installable Planning API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an installable, provider-neutral planning API and built-in LLM challenge source so `agentic-debate` supports a package-level `topic -> runnable debate` workflow.

**Architecture:** Introduce a new `agentic_debate.planning` package that resolves a raw topic into a validated `DebatePlan`, then converts that plan into a standard `DebateSpec`. Add a built-in `LlmChallengeSource` under `methods/rounds` that generates round content from any `LlmCaller`, then migrate the demo and README to consume those installable APIs instead of duplicate demo-local implementations.

**Tech Stack:** Python 3.12, Pydantic v2, pytest, pytest-asyncio, hatchling, existing `LlmCaller` protocol

---

## File Map

```text
src/agentic_debate/
  __init__.py                         # export planning models, planner, and LLM challenge source
  errors.py                           # typed planning and generation exceptions
  prompts/__init__.py                 # prompt loaders, default prompt-set helpers, judge prompt helper
  prompts/planning_intent.md          # built-in prompt for intent analysis
  prompts/planning_team.md            # built-in prompt for participant generation
  prompts/challenge_first_round.md    # built-in prompt for first-round openings
  prompts/challenge_rebuttal.md       # built-in prompt for rebuttal rounds
  planning/__init__.py                # planning package exports
  planning/base.py                    # DebatePlanner protocol
  planning/types.py                   # DebateIntent, PlannedParticipant, DebatePlan
  planning/llm.py                     # LlmDebatePlanner + prompt-set types
  methods/rounds/__init__.py          # export LlmChallengeSource
  methods/rounds/llm.py               # built-in generated challenge source

tests/
  test_planning_types.py              # DebatePlan validation and to_spec()
  test_planning_llm.py                # planner normalization, prompt injection, error wrapping
  test_rounds_llm.py                  # round-robin, pairwise, callback, invalid mode, error wrapping
  test_readme_installable_flow.py     # smoke coverage of new public package path

demo/backend/
  main.py                             # switch to installable planner and challenge source
  gemini.py                           # keep GeminiLlmCaller and GeminiLocalizer only
  prompts.py                          # keep demo-only prompts only
  challenge_source.py                 # delete after migration to package LlmChallengeSource

README.md                             # replace demo imports with package imports
docs/superpowers/specs/2026-04-01-installable-planning-api-design.md
```

---

### Task 1: Add planning models and public exports

**Files:**
- Create: `src/agentic_debate/planning/__init__.py`
- Create: `src/agentic_debate/planning/base.py`
- Create: `src/agentic_debate/planning/types.py`
- Modify: `src/agentic_debate/__init__.py`
- Test: `tests/test_planning_types.py`

- [ ] **Step 1: Write the failing tests for planning models**

```python
from agentic_debate.planning.types import DebateIntent, DebatePlan, PlannedParticipant
from pydantic import ValidationError
from agentic_debate.spec import RoundPolicy
import pytest


def test_debate_plan_to_spec_builds_runnable_spec():
    plan = DebatePlan(
        topic="Should AI replace doctors?",
        intent=DebateIntent(
            reframed_topic="Should AI replace doctors?",
            domain="healthcare",
            controversy_level="high",
            recommended_participants=3,
            recommended_rounds=2,
        ),
        participants=[
            PlannedParticipant(
                participant_id="doctor",
                label="Doctor",
                role="expert",
                stance="Keep humans central",
                metadata={"accent_color": "#4F86C6"},
            ),
            PlannedParticipant(
                participant_id="builder",
                label="Builder",
                role="technologist",
                stance="Automate aggressively",
            ),
        ],
        round_policy=RoundPolicy(mode="round_robin", max_rounds=2),
    )

    spec = plan.to_spec(namespace="test")

    assert spec.subject.title == "Should AI replace doctors?"
    assert spec.round_policy.mode == "round_robin"
    assert spec.round_policy.max_rounds == 2
    assert len(spec.participants) == 2
    assert spec.participants[0].metadata["accent_color"] == "#4F86C6"


def test_debate_plan_requires_unique_participant_ids():
    plan = DebatePlan(
        topic="Should AI replace doctors?",
        intent=DebateIntent(
            reframed_topic="Should AI replace doctors?",
            domain="healthcare",
            controversy_level="high",
            recommended_participants=2,
            recommended_rounds=2,
        ),
        participants=[
            PlannedParticipant(participant_id="doctor", label="Doctor A", role="expert"),
            PlannedParticipant(participant_id="doctor", label="Doctor B", role="expert"),
        ],
        round_policy=RoundPolicy(mode="round_robin", max_rounds=2),
    )

    with pytest.raises(ValueError):
        plan.to_spec(namespace="test")


def test_planned_participant_rejects_extra_top_level_fields():
    with pytest.raises(ValidationError):
        PlannedParticipant(
            participant_id="doctor",
            label="Doctor",
            role="expert",
            accent_color="#f00",
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_planning_types.py -v`  
Expected: `ModuleNotFoundError: No module named 'agentic_debate.planning'`

- [ ] **Step 3: Implement the planning models and protocol**

```python
class PlannedParticipant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    participant_id: str
    label: str
    role: str
    stance: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebatePlanner(Protocol):
    async def plan_topic(self, topic: str, *, context: DebateContext) -> DebatePlan: ...


class DebateIntent(BaseModel):
    reframed_topic: str
    domain: str
    controversy_level: Literal["low", "medium", "high"]
    recommended_participants: int
    recommended_rounds: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class DebatePlan(BaseModel):
    topic: str
    intent: DebateIntent
    participants: list[PlannedParticipant]
    round_policy: RoundPolicy
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_spec(self, namespace: str, *, subject_kind: str = "open_question") -> DebateSpec:
        return DebateSpec(
            namespace=namespace,
            subject=DebateSubject(kind=subject_kind, title=self.intent.reframed_topic),
            participants=[
                DebateParticipant(
                    **p.model_dump(
                        include={"participant_id", "label", "role", "stance", "metadata"}
                    )
                )
                for p in self.participants
            ],
            round_policy=self.round_policy,
        )
```

- [ ] **Step 4: Export the new planning types from the package root**

```python
from agentic_debate.planning import DebateIntent, DebatePlan, DebatePlanner, PlannedParticipant
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest tests/test_planning_types.py -v`  
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/agentic_debate/planning src/agentic_debate/__init__.py tests/test_planning_types.py
git commit -m "feat: add planning models and exports"
```

---

### Task 2: Implement built-in prompt loading and the LLM planner

**Files:**
- Create: `src/agentic_debate/prompts/planning_intent.md`
- Create: `src/agentic_debate/prompts/planning_team.md`
- Create: `src/agentic_debate/planning/llm.py`
- Modify: `src/agentic_debate/prompts/__init__.py`
- Modify: `src/agentic_debate/errors.py`
- Modify: `src/agentic_debate/__init__.py`
- Test: `tests/test_planning_llm.py`

- [ ] **Step 1: Write the failing tests for planner behavior**

```python
@pytest.mark.asyncio
async def test_llm_debate_planner_normalizes_intent_and_returns_plan():
    # _FakePlannerCaller should return an invalid controversy level such as "banana"
    # so this test proves the planner normalizes unsupported values to "medium".
    planner = LlmDebatePlanner(llm=_FakePlannerCaller())
    plan = await planner.plan_topic("should ai replace doctors", context=DebateContext(namespace="test"))

    assert plan.intent.controversy_level == "medium"
    assert 2 <= len(plan.participants) <= 5
    assert plan.round_policy.max_rounds == plan.intent.recommended_rounds


@pytest.mark.asyncio
async def test_llm_debate_planner_wraps_intent_failures():
    planner = LlmDebatePlanner(llm=_ExplodingCaller())
    with pytest.raises(DebatePlanningError) as exc:
        await planner.plan_topic("topic", context=DebateContext(namespace="test"))
    assert exc.value.stage == "intent_analysis"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_planning_llm.py -v`  
Expected: `ImportError` for `LlmDebatePlanner` and/or `DebatePlanningError`

- [ ] **Step 3: Add built-in prompt assets and prompt-set helpers**

```python
@dataclass(frozen=True)
class PlanningPromptSet:
    intent_prompt_template: str
    team_prompt_template: str


def load_builtin_planning_prompt_set() -> PlanningPromptSet:
    return PlanningPromptSet(
        intent_prompt_template=_read_prompt("planning_intent.md"),
        team_prompt_template=_read_prompt("planning_team.md"),
    )


def load_builtin_judge_prompt() -> str:
    return _read_prompt("judge_generic.md")
```

Template contract to encode in the prompt assets and planner tests:

- `planning_intent.md`: `{topic}`
- `planning_team.md`: `{topic}`, `{reframed_topic}`, `{domain}`, `{controversy_level}`, `{participant_count}`, `{round_count}`

- [ ] **Step 4: Implement `LlmDebatePlanner` with validation and error wrapping**

```python
class LlmDebatePlanner:
    async def plan_topic(self, topic: str, *, context: DebateContext) -> DebatePlan:
        try:
            raw_intent = await self._llm.generate_structured(..., _RawIntentResult, context=context)
        except Exception as exc:
            raise DebatePlanningError("intent_analysis", str(exc)) from exc

        intent = DebateIntent(
            reframed_topic=raw_intent.reframed_topic,
            domain=raw_intent.domain,
            controversy_level=_normalize_controversy(raw_intent.controversy_level),
            recommended_participants=max(2, min(5, raw_intent.recommended_participants)),
            recommended_rounds=max(1, min(3, raw_intent.recommended_rounds)),
        )

        try:
            raw_team = await self._llm.generate_structured(..., _TeamResponse, context=context)
        except Exception as exc:
            raise DebatePlanningError("participant_generation", str(exc)) from exc

        return DebatePlan(
            ...,
            round_policy=RoundPolicy(
                mode="round_robin",
                max_rounds=intent.recommended_rounds,
            ),
        )
```

- [ ] **Step 5: Export the planner and error classes**

```python
from agentic_debate.planning.llm import LlmDebatePlanner
from agentic_debate.errors import DebatePlanningError
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/test_planning_llm.py -v`  
Expected: all tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/agentic_debate/prompts src/agentic_debate/planning/llm.py src/agentic_debate/errors.py src/agentic_debate/__init__.py tests/test_planning_llm.py
git commit -m "feat: add built-in llm debate planner"
```

---

### Task 3: Add the built-in LLM challenge source

**Files:**
- Create: `src/agentic_debate/prompts/challenge_first_round.md`
- Create: `src/agentic_debate/prompts/challenge_rebuttal.md`
- Create: `src/agentic_debate/methods/rounds/llm.py`
- Modify: `src/agentic_debate/methods/rounds/__init__.py`
- Modify: `src/agentic_debate/prompts/__init__.py`
- Modify: `src/agentic_debate/errors.py`
- Modify: `src/agentic_debate/__init__.py`
- Test: `tests/test_rounds_llm.py`

- [ ] **Step 1: Write the failing tests for round generation**

```python
@pytest.mark.asyncio
async def test_llm_challenge_source_round_robin_generates_one_turn_per_participant():
    source = LlmChallengeSource(llm=_FakeChallengeCaller())
    challenges = await source.collect(_make_spec(mode="round_robin", max_rounds=2), DebateContext(namespace="test"))
    assert len(challenges) == 6
    assert challenges[0].challenger_id == "p0"
    assert challenges[0].target_id == "p1"


@pytest.mark.asyncio
async def test_llm_challenge_source_pairwise_generates_all_pairs():
    source = LlmChallengeSource(llm=_FakeChallengeCaller())
    challenges = await source.collect(_make_spec(mode="pairwise", max_rounds=1), DebateContext(namespace="test"))
    assert {(c.challenger_id, c.target_id) for c in challenges} == {
        ("p0", "p1"), ("p0", "p2"), ("p1", "p0"), ("p1", "p2"), ("p2", "p0"), ("p2", "p1")
    }


@pytest.mark.asyncio
async def test_llm_challenge_source_pairwise_repeats_pairs_each_round():
    source = LlmChallengeSource(llm=_FakeChallengeCaller())
    challenges = await source.collect(_make_spec(mode="pairwise", max_rounds=2), DebateContext(namespace="test"))
    assert len(challenges) == 12
    assert {c.round_index for c in challenges} == {1, 2}


@pytest.mark.asyncio
async def test_llm_challenge_source_rejects_precomputed_mode():
    with pytest.raises(DebateConfigurationError):
        await LlmChallengeSource(llm=_FakeChallengeCaller()).collect(
            _make_spec(mode="precomputed", max_rounds=1),
            DebateContext(namespace="test"),
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_rounds_llm.py -v`  
Expected: `ImportError` for `LlmChallengeSource`

- [ ] **Step 3: Implement prompt-set loading for challenge generation**

```python
@dataclass(frozen=True)
class ChallengePromptSet:
    first_round_prompt_template: str
    rebuttal_prompt_template: str
```

Template contract to encode in the prompt assets and round tests:

- `challenge_first_round.md`: `{challenger_label}`, `{challenger_stance}`, `{topic}`, `{round_index}`
- `challenge_rebuttal.md`: `{challenger_label}`, `{challenger_stance}`, `{topic}`, `{target_label}`, `{prior_argument}`, `{round_index}`

- [ ] **Step 4: Implement `LlmChallengeSource` with round-robin, pairwise, callback, and wrapped errors**

```python
class LlmChallengeSource:
    def __init__(
        self,
        llm: LlmCaller,
        on_challenge: Callable[[DebateChallenge], Awaitable[None]] | None = None,
    ) -> None:
        ...

    async def collect(self, spec: DebateSpec, context: DebateContext) -> list[DebateChallenge]:
        if spec.round_policy.mode == "precomputed":
            raise DebateConfigurationError("LlmChallengeSource does not support precomputed round mode")

        turns = _build_turns(spec)
        prior_args: dict[str, str] = {}
        challenges: list[DebateChallenge] = []

        for round_index, challenger, target in turns:
            prompt = self._build_prompt(...)
            try:
                output = await self._llm.generate_structured(prompt, _ChallengeOutput, context=context)
            except Exception as exc:
                raise DebateGenerationError("challenge_generation", str(exc)) from exc
            ...
```

- [ ] **Step 5: Export `LlmChallengeSource` from the rounds package and package root**

```python
from agentic_debate.methods.rounds.llm import LlmChallengeSource
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/test_rounds_llm.py -v`  
Expected: all tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/agentic_debate/prompts src/agentic_debate/methods/rounds src/agentic_debate/errors.py src/agentic_debate/__init__.py tests/test_rounds_llm.py
git commit -m "feat: add built-in llm challenge source"
```

---

### Task 4: Add package-level smoke coverage for the installable happy path

**Files:**
- Create: `tests/test_readme_installable_flow.py`

- [ ] **Step 1: Write the failing smoke test for the documented package API**

```python
@pytest.mark.asyncio
async def test_installable_topic_to_runnable_debate_flow():
    llm = _SequenceFakeLlmCaller([
        {
            "reframed_topic": "Is nuclear power safe?",
            "domain": "energy",
            "controversy_level": "high",
            "recommended_participants": 3,
            "recommended_rounds": 2,
        },
        {
            "participants": [
                {"participant_id": "engineer", "label": "Engineer", "role": "expert", "stance": "Nuclear is scalable"},
                {"participant_id": "activist", "label": "Activist", "role": "critic", "stance": "Nuclear risk is underestimated"},
                {"participant_id": "economist", "label": "Economist", "role": "analyst", "stance": "Cost decides viability"},
            ]
        },
        *[
            {
                "challenge_text": f"challenge {i}",
                "topic_tag": "safety_cost",
                "confidence": 0.75,
            }
            for i in range(1, 7)
        ],
        {
            "verdicts": [
                {
                    "topic": "safety_cost",
                    "winning_participant_id": "engineer",
                    "confidence": 0.8,
                    "rationale": "Engineering argument carried the round.",
                    "open_questions": [],
                    "consensus_level": "moderate",
                }
            ],
            "debate_summary": "Engineer leads.",
            "contested_topics": [],
        },
    ])
    ctx = DebateContext(namespace="test")

    plan = await LlmDebatePlanner(llm=llm).plan_topic("Is nuclear power safe?", context=ctx)
    spec = plan.to_spec(namespace="test")

    compiler = DebateCompiler(
        challenge_source=LlmChallengeSource(llm=llm),
        grouping=GroupByTopicStrategy(),
        arbitrator=LlmSingleJudgeArbitrator(llm=llm, prompt_template=SIMPLE_TEMPLATE),
        synthesizer=PassthroughSynthesizer(),
        transcript_formatter=SimpleTranscriptFormatter(),
    )

    result = await DebateEngine().run(await compiler.compile(spec), context=ctx)
    assert result.arbitration.verdicts


class _SequenceFakeLlmCaller:
    def __init__(self, responses: list[dict]) -> None:
        self._responses = iter(responses)

    async def generate_structured(self, prompt: str, response_model: type, *, context):
        try:
            payload = next(self._responses)
        except StopIteration as exc:
            raise AssertionError("Unexpected extra LLM call in smoke test") from exc
        return response_model.model_validate(payload)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_readme_installable_flow.py -v`  
Expected: FAIL because planner and challenge source are not both available yet or are not wired together correctly

- [ ] **Step 3: Adjust any missing exports or defaults until the smoke path passes**

```python
__all__ = [
    ...,
    "DebateIntent",
    "DebatePlan",
    "DebatePlanner",
    "PlannedParticipant",
    "LlmDebatePlanner",
    "LlmChallengeSource",
]
```

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `pytest tests/test_readme_installable_flow.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_readme_installable_flow.py src/agentic_debate/__init__.py
git commit -m "test: cover installable topic-to-debate flow"
```

---

### Task 5: Migrate the demo onto the library APIs

**Files:**
- Modify: `demo/backend/main.py`
- Modify: `demo/backend/gemini.py`
- Modify: `demo/backend/prompts.py`
- Delete: `demo/backend/challenge_source.py`
- Modify: `demo/tests/test_intent.py`
- Modify: `demo/tests/test_challenge_source.py`

- [ ] **Step 1: Rewrite the demo tests so they assert the new integration boundary**

Existing coverage to preserve while moving the boundary:

- `demo/tests/test_intent.py` currently checks intent clamping, round clamping, generated team count, and accent-color metadata assignment
- `demo/tests/test_challenge_source.py` currently checks `n_participants * max_rounds`, round indices, round-robin targets, callback firing, and populated challenge fields

The rewrite should keep those behavioral assertions, but import the package planner and package `LlmChallengeSource` instead of demo-local implementations.

```python
async def test_demo_uses_library_planner_with_gemini_adapter():
    from agentic_debate.planning.llm import LlmDebatePlanner
    from backend.gemini import GeminiLlmCaller
    ...


async def test_demo_uses_library_llm_challenge_source():
    from agentic_debate.methods.rounds.llm import LlmChallengeSource
    ...
```

- [ ] **Step 2: Run the demo-focused tests to verify they fail**

Run: `pytest demo/tests/test_intent.py demo/tests/test_challenge_source.py -v`  
Expected: FAIL because the demo still references local planner/challenge implementations

- [ ] **Step 3: Update the demo backend to import the library planner and challenge source**

```python
from agentic_debate import LlmChallengeSource, LlmDebatePlanner

planner = LlmDebatePlanner(llm=llm)
plan = await planner.plan_topic(request.topic, context=ctx)
participants = [p.model_copy() for p in plan.participants]
spec = plan.to_spec(namespace="demo")
```

- [ ] **Step 4: Reduce `demo/backend/gemini.py` and `demo/backend/prompts.py` to provider/demo-only responsibilities**

```python
class GeminiLlmCaller:
    async def generate_structured(...): ...


class GeminiLocalizer:
    async def localize(...): ...
```

- [ ] **Step 5: Run the demo-focused tests to verify they pass**

Run: `pytest demo/tests/test_intent.py demo/tests/test_challenge_source.py -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add demo/backend/main.py demo/backend/gemini.py demo/backend/prompts.py demo/tests/test_intent.py demo/tests/test_challenge_source.py
git rm demo/backend/challenge_source.py
git commit -m "refactor(demo): consume installable planning and challenge apis"
```

---

### Task 6: Update README to document the installable API

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write the failing documentation smoke assertion**

```python
def test_readme_does_not_reference_demo_backend_imports():
    text = Path("README.md").read_text()
    assert "from backend.gemini" not in text
    assert "LlmDebatePlanner" in text
    assert "LlmChallengeSource" in text
```

- [ ] **Step 2: Run the assertion to verify it fails**

Run: `pytest tests/test_readme_installable_flow.py::test_readme_does_not_reference_demo_backend_imports -v`  
Expected: FAIL because README still documents demo imports

- [ ] **Step 3: Replace demo imports with the installable package flow**

```python
from agentic_debate import LlmDebatePlanner, LlmChallengeSource

plan = await LlmDebatePlanner(llm=llm).plan_topic("Is nuclear power safe?", context=ctx)
spec = plan.to_spec(namespace="my-app")
```

- [ ] **Step 4: Run the assertion to verify it passes**

Run: `pytest tests/test_readme_installable_flow.py::test_readme_does_not_reference_demo_backend_imports -v`  
Expected: PASS

- [ ] **Step 5: Run the focused package test suite**

Run: `pytest tests/test_planning_types.py tests/test_planning_llm.py tests/test_rounds_llm.py tests/test_readme_installable_flow.py -v`  
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add README.md tests/test_readme_installable_flow.py
git commit -m "docs: document installable planning api"
```

---

### Task 7: Final verification

**Files:**
- Verify only; no new files

- [ ] **Step 1: Run the root test suite**

Run: `pytest tests -v`  
Expected: PASS

- [ ] **Step 2: Run the demo test suite**

Run: `pytest demo/tests -v`  
Expected: PASS

- [ ] **Step 3: Run static checks**

Run: `ruff check src tests demo`  
Expected: PASS

Run: `mypy src`  
Expected: PASS

- [ ] **Step 4: Verify README example imports are installable**

Run: `python - <<'PY'\nfrom agentic_debate import LlmDebatePlanner, LlmChallengeSource\nprint('ok')\nPY`  
Expected: `ok`

- [ ] **Step 5: Commit any remaining verification-driven fixes**

```bash
git add -A
git commit -m "chore: finish installable planning api rollout"
```
