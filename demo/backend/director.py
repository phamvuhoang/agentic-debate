from __future__ import annotations

import asyncio
import logging
from typing import Any

from agentic_debate import LlmChallengeSource
from agentic_debate.compile import DebateCompiler
from agentic_debate.context import DebateContext
from agentic_debate.engine import DebateEngine
from agentic_debate.llm.base import LlmCaller
from agentic_debate.methods.arbitration.llm_single_judge import LlmSingleJudgeArbitrator
from agentic_debate.methods.grouping import GroupByTopicStrategy
from agentic_debate.methods.synthesis.passthrough import PassthroughSynthesizer
from agentic_debate.methods.transcript import SimpleTranscriptFormatter
from agentic_debate.prompts import load_builtin_judge_prompt
from agentic_debate.spec import ArbitrationPolicy, TranscriptPolicy
from agentic_debate.types import DebateChallenge

from backend.observer import DebateStageObserver
from backend.planning import build_demo_plan
from backend.protocol import (
    ActionAckResponse,
    SessionActionRequest,
    SessionCreateRequest,
    SessionCreateResponse,
)
from backend.session_store import SessionStore

_logger = logging.getLogger(__name__)


class DebateDirector:
    def __init__(self, store: SessionStore, llm: LlmCaller) -> None:
        self.store = store
        self._llm = llm
        self._sequence: dict[str, int] = {}

    def _next_seq(self, session_id: str) -> int:
        self._sequence[session_id] = self._sequence.get(session_id, 0) + 1
        return self._sequence[session_id]

    def _publish(
        self,
        session_id: str,
        event_type: str,
        phase: str,
        payload: dict[str, Any],
    ) -> None:
        from backend.protocol import DebateEvent
        event = DebateEvent(
            session_id=session_id,
            sequence=self._next_seq(session_id),
            type=event_type,  # type: ignore[arg-type]
            phase=phase,  # type: ignore[arg-type]
            payload=payload,
        )
        self.store.publish(event)

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
        try:
            self._publish(session_id, "debate_created", "idle", {"topic": request.topic})

            ctx = DebateContext(namespace=session_id)
            plan = await build_demo_plan(
                request.topic,
                self._llm,
                ctx,
                participant_count=request.participant_count,
                round_count=request.round_count,
            )
            spec = plan.to_spec(namespace=session_id).model_copy(
                update={
                    "arbitration_policy": ArbitrationPolicy(method="llm_single_judge"),
                    "transcript_policy": TranscriptPolicy(output_locale=request.output_locale),
                }
            )

            for participant in spec.participants:
                self._publish(session_id, "agent_summoned", "summoning", {
                    "participant_id": participant.participant_id,
                    "label": participant.label,
                    "role": participant.role,
                    "stance": participant.stance,
                    **participant.metadata,
                })

            current_round: list[int] = [0]
            needs_localize = request.output_locale != "en"
            localizer = None
            if needs_localize:
                from backend.gemini import GeminiLocalizer
                localizer = GeminiLocalizer(self._llm)  # type: ignore[arg-type]

            async def on_challenge(challenge: DebateChallenge) -> None:
                if challenge.round_index != current_round[0]:
                    current_round[0] = challenge.round_index
                    self._publish(session_id, "round_closed", "debate", {"round_index": challenge.round_index - 1})

                self._publish(session_id, "speaker_activated", "debate", {
                    "speaker_id": challenge.challenger_id,
                })
                self._publish(session_id, "argument_started", "debate", {
                    "challenger_id": challenge.challenger_id,
                    "target_id": challenge.target_id,
                    "topic": challenge.topic,
                    "round_index": challenge.round_index,
                })

                text = challenge.challenge_text
                if needs_localize and localizer is not None:
                    text = await localizer.localize(text, request.output_locale, ctx)

                self._publish(session_id, "argument_completed", "debate", {
                    "challenger_id": challenge.challenger_id,
                    "challenge_text": text,
                    "confidence": challenge.confidence,
                })

            observer = DebateStageObserver(
                publish=lambda et, ph, pl: self._publish(session_id, et, ph, pl)
            )
            challenge_source = LlmChallengeSource(llm=self._llm, on_challenge=on_challenge)
            compiler = DebateCompiler(
                challenge_source=challenge_source,
                grouping=GroupByTopicStrategy(),
                arbitrator=LlmSingleJudgeArbitrator(
                    llm=self._llm,
                    prompt_template=load_builtin_judge_prompt(),
                ),
                synthesizer=PassthroughSynthesizer(),
                transcript_formatter=SimpleTranscriptFormatter(),
                observers=[observer],
            )
            compiled = await compiler.compile(spec, context=ctx)
            run_result = await DebateEngine().run(compiled, context=ctx)

            # Localize verdict if needed
            summary = run_result.arbitration.summary
            contested = list(run_result.arbitration.contested_topics)
            if request.output_locale != "en":
                from backend.gemini import GeminiLocalizer
                localizer = GeminiLocalizer(self._llm)  # type: ignore[arg-type]
                summary = await localizer.localize(summary, request.output_locale, ctx)
                contested = [
                    await localizer.localize(t, request.output_locale, ctx)
                    for t in contested
                ]

            # Publish verdict
            verdicts_payload = [v.model_dump() for v in run_result.arbitration.verdicts]
            self._publish(session_id, "verdict_revealed", "complete", {
                "summary": summary,
                "verdicts": verdicts_payload,
                "contested_topics": contested,
                "transcript": run_result.transcript,
            })

        except Exception:
            _logger.exception("session_run_failed session_id=%s", session_id)
            self._publish(session_id, "error_raised", "error", {"message": "Debate session failed."})
        finally:
            # Signal SSE subscribers that the stream is done
            for queue in self.store._listeners.get(session_id, []):
                queue.put_nowait(None)

    async def handle_action(
        self, session_id: str, request: SessionActionRequest
    ) -> ActionAckResponse:
        self.store.log_action(session_id, request)
        self._publish(session_id, "action_acknowledged", "debate", {
            "action": request.action,
            "payload": request.payload,
        })
        return ActionAckResponse(
            session_id=session_id,
            accepted=True,
            action=request.action,
            sequence=self._sequence.get(session_id, 0),
        )
