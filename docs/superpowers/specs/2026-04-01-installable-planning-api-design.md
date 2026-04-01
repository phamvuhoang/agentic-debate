# Installable Planning API Design Spec

**Date:** 2026-04-01  
**Status:** Approved

---

## Overview

`agentic-debate` currently ships a solid neutral execution engine, but its documented "topic to debate" workflow still depends on demo-only modules under `demo/backend/`. This design adds an installable, provider-neutral planning layer and a built-in LLM challenge source so a package consumer can go from a raw topic to a runnable debate without copying demo code.

The new feature keeps the engine host-agnostic. The library continues to depend only on the `LlmCaller` protocol, not on Gemini or any specific provider SDK. Provider-specific adapters remain outside the core package surface.

---

## Problem Statement

The library README markets Auto-Team and intent analysis as the standout feature, but the installable wheel currently exports only engine primitives. The usable planning path lives in the demo:

- `demo/backend/gemini.py` owns `intent_analysis()` and `generate_team()`
- `demo/backend/challenge_source.py` owns the only LLM-backed challenge generator
- `README.md` points consumers at demo imports instead of installable package modules

This creates three problems:

1. The documented happy path is not actually package-supported.
2. The demo duplicates logic that should be reusable by other hosts.
3. The product promise is stronger than the public API.

---

## Goals

- Provide a first-class, installable planning API that turns a raw topic into a resolved debate plan.
- Keep the feature provider-neutral by building on `LlmCaller`.
- Ship a built-in LLM challenge source so consumers can go from `topic -> runnable debate`.
- Preserve the existing engine architecture: planning resolves a `DebateSpec`; execution remains unchanged.
- Migrate the demo to consume the library APIs instead of keeping a second implementation.
- Update README examples so they only use installable modules.

---

## Non-Goals

- Adding a provider SDK dependency to `pyproject.toml`
- Replacing the current compiler or engine lifecycle
- Solving every future planning strategy in v1
- Implementing `llm_panel` or `weighted_vote` arbitration in the same milestone
- Adding persistence, session state, auth, or UI concerns to the package

---

## Proposed Public API

### Planning models

Add a new planning package:

```text
src/agentic_debate/planning/
  __init__.py
  base.py
  types.py
  llm.py
```

New installable models:

- `DebateIntent`
  - `reframed_topic: str`
  - `domain: str`
  - `controversy_level: Literal["low", "medium", "high"]`
  - `recommended_participants: int`
  - `recommended_rounds: int`
  - `metadata: dict[str, Any]`
- `PlannedParticipant`
  - same serialized fields as `DebateParticipant`
  - optional host-specific data such as accent color or presentation hints must live inside `metadata`, not as extra top-level fields
  - v1 should forbid extra top-level fields to keep `DebatePlan -> DebateSpec` conversion predictable
  - enforce this with `model_config = ConfigDict(extra="forbid")`
- `DebatePlan`
  - `topic: str`
  - `intent: DebateIntent`
  - `participants: list[PlannedParticipant]`
  - `round_policy: RoundPolicy`
  - `metadata: dict[str, Any]`
  - `to_spec(namespace: str, *, subject_kind: str = "open_question") -> DebateSpec`

`DebatePlan.to_spec()` must map participants using an explicit field projection:

- `participant_id`
- `label`
- `role`
- `stance`
- `metadata`

It must not pass arbitrary `model_dump()` output through to `DebateParticipant`.

### Planning protocols

Add a provider-neutral protocol:

```python
class DebatePlanner(Protocol):
    async def plan_topic(self, topic: str, *, context: DebateContext) -> DebatePlan: ...
```

This becomes the stable contract for any future rule-based, human-authored, or provider-specific planners.

### Built-in LLM planner

Add `LlmDebatePlanner` in `agentic_debate.planning.llm`:

```python
planner = LlmDebatePlanner(llm=my_llm)
plan = await planner.plan_topic("Is nuclear power safe?", context=ctx)
spec = plan.to_spec(namespace="my-app")
```

Responsibilities:

1. Analyze a raw topic into `DebateIntent`
2. Generate participants from that intent
3. Clamp and validate participant/round recommendations
4. Always produce a `DebatePlan` with an explicit `RoundPolicy` runnable by the built-in LLM challenge source

### Built-in LLM challenge source

Add `LlmChallengeSource` to `src/agentic_debate/methods/rounds/llm.py` and export it publicly.

```python
challenge_source = LlmChallengeSource(llm=my_llm)
```

Constructor contract:

```python
LlmChallengeSource(
    llm=my_llm,
    on_challenge: Callable[[DebateChallenge], Awaitable[None]] | None = None,
)
```

Responsibilities:

1. Generate first-round openings and later rebuttals from a resolved `DebateSpec`
2. Support `RoundPolicy(mode="round_robin")` in v1
3. Support `RoundPolicy(mode="pairwise")` in v1; for `max_rounds > 1`, each round repeats the full directed pair matrix
4. Reject `RoundPolicy(mode="precomputed")` with a configuration error when paired with this source
5. Optionally invoke `on_challenge(challenge)` after each generated `DebateChallenge`, allowing hosts to stream or inspect output incrementally

`PrecomputedChallengeSource` remains the manual/static path. `LlmChallengeSource` becomes the built-in generated path.

---

## Default Prompt Assets

The package already contains prompt assets under `src/agentic_debate/prompts/`. Extend that directory with installable prompt templates:

- `planning_intent.md`
- `planning_team.md`
- `challenge_first_round.md`
- `challenge_rebuttal.md`

These prompts should be loadable through package code, not copied into host adapters. Hosts can still override templates by passing a custom prompt set into `LlmDebatePlanner` or `LlmChallengeSource`.

Required template variables:

- `planning_intent.md`
  - `{topic}`
- `planning_team.md`
  - `{topic}`
  - `{reframed_topic}`
  - `{domain}`
  - `{controversy_level}`
  - `{participant_count}`
  - `{round_count}`
- `challenge_first_round.md`
  - `{challenger_label}`
  - `{challenger_stance}`
  - `{topic}`
  - `{round_index}`
- `challenge_rebuttal.md`
  - `{challenger_label}`
  - `{challenger_stance}`
  - `{topic}`
  - `{target_label}`
  - `{prior_argument}`
  - `{round_index}`

Proposed supporting types:

- `PlanningPromptSet`
- `ChallengePromptSet`
- `load_builtin_judge_prompt()`

These are small immutable containers or helpers for prompt templates. The defaults load from built-in package assets; advanced hosts can substitute their own.

---

## Execution Flow

### Installable happy path

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

planner = LlmDebatePlanner(llm=llm)
plan = await planner.plan_topic("Should AI replace doctors?", context=ctx)
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

### Internal flow

1. `LlmDebatePlanner.plan_topic()` calls `LlmCaller.generate_structured()` for intent analysis.
2. The planner calls `LlmCaller.generate_structured()` again for participant generation.
3. The planner clamps counts and creates `DebatePlan`.
4. `LlmDebatePlanner` sets `round_policy=RoundPolicy(mode="round_robin", max_rounds=intent.recommended_rounds)` on the returned plan.
5. `DebatePlan.to_spec()` produces a normal `DebateSpec` by explicitly projecting supported participant fields.
6. `LlmChallengeSource.collect()` inspects `spec.round_policy` and generates challenges for each round.
7. Existing grouping, arbitration, synthesis, transcript formatting, localization, and observer flows continue unchanged.

---

## Error Model

Use the existing `DebateConfigurationError` for invalid plan/challenge wiring, and add typed library errors for generation-time failures:

- `DebatePlanningError(DebateError)`
  - `stage`: `"intent_analysis"` or `"participant_generation"`
- `DebateGenerationError(DebateExecutionError)`
  - `stage`: `"challenge_generation"`

Behavior:

- Provider/structured-output exceptions are wrapped at the planning or challenge boundary.
- Validation errors remain explicit; the error message should say which stage produced invalid output.
- `LlmChallengeSource` raises `DebateConfigurationError` when the `RoundPolicy.mode` is incompatible with generated challenges.

This keeps failures localized and easier for host applications to surface cleanly.

---

## Validation Rules

`LlmDebatePlanner` should preserve the useful guardrails already present in the demo:

- participant count is clamped to 2..5
- round count is clamped to 1..3
- unrecognized controversy levels fall back to `"medium"`
- generated participant lists are truncated to the requested participant count

Additional v1 validations:

- at least 2 participants are required
- participant IDs must be unique after generation
- `PlannedParticipant` stores host-specific additions inside `metadata`; `to_spec()` projects only the supported participant fields listed above
- `PlannedParticipant(..., accent_color="#f00")` should raise `ValidationError`; tests should cover this explicitly
- `DebatePlan.to_spec()` should fail fast if the plan is internally inconsistent

---

## Demo Migration

After the package ships the feature, the demo should consume it instead of keeping parallel implementations:

- `demo/backend/main.py` imports `LlmDebatePlanner` and package `LlmChallengeSource`
- `demo/backend/gemini.py` keeps the Gemini `LlmCaller` and localizer only
- demo-local planning/challenge tests move to root package tests where possible
- `demo/backend/prompts.py` keeps only prompts that are truly demo-specific, such as translation or any demo-only presentation text

This reduces duplication and makes the demo a real proof that the package surface works.

---

## README and Documentation Changes

Update `README.md` so the first integration example uses only installable imports from `agentic_debate`. The README should no longer reference `demo/backend/*` as part of the consumer API.

Add a short example showing:

1. implement a provider adapter for `LlmCaller`
2. call `LlmDebatePlanner`
3. compile and run with `LlmChallengeSource`

This is the documentation counterpart to the new package-level happy path.

---

## Testing Strategy

Add or migrate package-level tests covering:

- `DebatePlan.to_spec()` shape and validation
- `LlmDebatePlanner` intent normalization and participant clamping
- custom prompt set injection for planner and challenge source
- `LlmChallengeSource` round-robin sequencing
- `LlmChallengeSource` pairwise sequencing
- `LlmChallengeSource` callback firing behavior
- failure wrapping into `DebatePlanningError` / `DebateGenerationError`
- README-level smoke coverage for the new public API

The previous demo-only tests for intent analysis and challenge generation should move into root `tests/` so the package behavior is verified where it lives.

---

## File-Level Impact

### New files

- `src/agentic_debate/planning/__init__.py`
- `src/agentic_debate/planning/base.py`
- `src/agentic_debate/planning/types.py`
- `src/agentic_debate/planning/llm.py`
- `src/agentic_debate/methods/rounds/llm.py`
- `src/agentic_debate/prompts/planning_intent.md`
- `src/agentic_debate/prompts/planning_team.md`
- `src/agentic_debate/prompts/challenge_first_round.md`
- `src/agentic_debate/prompts/challenge_rebuttal.md`
- `tests/test_planning_types.py`
- `tests/test_planning_llm.py`
- `tests/test_rounds_llm.py`

### Modified files

- `src/agentic_debate/__init__.py`
- `src/agentic_debate/errors.py`
- `src/agentic_debate/prompts/__init__.py`
- `src/agentic_debate/methods/rounds/__init__.py`
- `README.md`
- `demo/backend/main.py`
- `demo/backend/gemini.py`
- `demo/backend/prompts.py`
- `demo/tests/test_intent.py`
- `demo/tests/test_challenge_source.py`

### Deleted files

- `demo/backend/challenge_source.py`

---

## Alternatives Considered

### Thin convenience helper only

Rejected because it would improve documentation quickly but would not create clear, reusable planning boundaries inside the package.

### Move Gemini planning code directly into the package

Rejected because it would violate the host-neutral contract and drag provider assumptions into the public surface.

### Build a larger end-to-end session builder first

Rejected because it would expand API surface before the basic installable planning primitives are proven.

---

## Future Work

- Additional planning strategies beyond LLM-backed generation
- Built-in arbitration prompt helpers alongside the existing judge prompt asset
- Official extras or example adapter packages for specific providers
- Follow-up work to reconcile or implement other advertised policy modes

---

## Decision

Ship an official provider-neutral planning API and a built-in LLM challenge source inside the installable package. Keep provider wiring behind `LlmCaller`, migrate the demo onto the package APIs, and update the README so the advertised happy path is real.
