"""Neutral debate execution engine."""

from __future__ import annotations

import logging
from typing import Any, cast

from agentic_debate.compile import CompiledDebate
from agentic_debate.context import DebateContext
from agentic_debate.result import DebateRoundResult, DebateRunResult

_logger = logging.getLogger(__name__)


async def _apply_localization(
    transcript: dict[str, Any],
    localizer: Any,
    locale: str,
    context: DebateContext,
) -> dict[str, Any]:
    """Apply localization to human-readable text fields in the transcript."""
    result = dict(transcript)

    async def _loc(text: str) -> str:
        try:
            return cast(str, await localizer.localize(text, locale, context))
        except Exception:
            _logger.warning("debate_localization_failed_field_kept_in_english")
            return text

    # Top-level text fields
    for key in ("summary", "debate_summary"):
        if isinstance(result.get(key), str):
            result[key] = await _loc(result[key])

    # Verdict-level text fields
    verdicts = result.get("verdicts") or []
    localized_verdicts = []
    for verdict in verdicts:
        v = dict(verdict) if isinstance(verdict, dict) else verdict
        if isinstance(v, dict):
            if isinstance(v.get("rationale"), str):
                v["rationale"] = await _loc(v["rationale"])
            if isinstance(v.get("open_questions"), list):
                v["open_questions"] = [
                    await _loc(q) if isinstance(q, str) else q
                    for q in v["open_questions"]
                ]
        localized_verdicts.append(v)
    if localized_verdicts:
        result["verdicts"] = localized_verdicts

    return result


class DebateEngine:
    """Runs compiled debates without any host-specific side effects."""

    async def _notify(
        self,
        compiled: CompiledDebate,
        *,
        event_type: str,
        payload: dict[str, Any],
        context: DebateContext,
    ) -> None:
        for observer in compiled.observers:
            await observer.on_event(event_type, payload, context)

    async def run_round(self, compiled: CompiledDebate, context: DebateContext | None = None) -> DebateRoundResult:
        """Collect and group debate challenges."""
        ctx = context if context is not None else DebateContext(namespace=compiled.spec.namespace)
        await self._notify(
            compiled,
            event_type="round_started",
            payload={"namespace": compiled.spec.namespace},
            context=ctx,
        )
        challenges = await compiled.challenge_source.collect(compiled.spec, ctx)
        await self._notify(
            compiled,
            event_type="challenges_collected",
            payload={"count": len(challenges)},
            context=ctx,
        )
        topic_groups = await compiled.grouping.group(challenges, compiled.spec, ctx)
        result = DebateRoundResult(challenges=challenges, topic_groups=topic_groups)
        await self._notify(
            compiled,
            event_type="round_completed",
            payload={"topic_count": len(topic_groups)},
            context=ctx,
        )
        return result

    async def arbitrate(
        self,
        compiled: CompiledDebate,
        round_result: DebateRoundResult,
        context: DebateContext | None = None,
    ) -> DebateRunResult:
        """Arbitrate an already collected round result and build the transcript."""
        ctx = context if context is not None else DebateContext(namespace=compiled.spec.namespace)
        await self._notify(
            compiled,
            event_type="arbitration_started",
            payload={"topic_count": len(round_result.topic_groups)},
            context=ctx,
        )
        arbitration = await compiled.arbitrator.arbitrate(
            round_result.topic_groups,
            compiled.spec,
            ctx,
        )
        await self._notify(
            compiled,
            event_type="arbitration_completed",
            payload={"verdict_count": len(arbitration.verdicts)},
            context=ctx,
        )
        synthesis = await compiled.synthesizer.synthesize(
            spec=compiled.spec,
            round_result=round_result,
            arbitration=arbitration,
            context=ctx,
        )
        transcript = await compiled.transcript_formatter.build(
            spec=compiled.spec,
            round_result=round_result,
            arbitration=arbitration,
            synthesis=synthesis,
            context=ctx,
        )
        locale = compiled.spec.transcript_policy.output_locale
        if locale != "en" and compiled.output_localizer is not None:
            transcript = await _apply_localization(
                transcript, compiled.output_localizer, locale, ctx
            )
        run_result = DebateRunResult(
            round_result=round_result,
            arbitration=arbitration,
            synthesis=synthesis,
            transcript=transcript,
        )
        await self._notify(
            compiled,
            event_type="transcript_built",
            payload={"has_transcript": bool(transcript)},
            context=ctx,
        )
        return run_result

    async def run(self, compiled: CompiledDebate, context: DebateContext | None = None) -> DebateRunResult:
        """Execute both debate stages in one call."""
        ctx = context if context is not None else DebateContext(namespace=compiled.spec.namespace)
        round_result = await self.run_round(compiled, context=ctx)
        return await self.arbitrate(compiled, round_result, context=ctx)
