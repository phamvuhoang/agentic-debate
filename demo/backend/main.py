from __future__ import annotations

import asyncio
import json
import logging
import pathlib

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

            # Sync observer children before engine run (children may have been rebound)
            observer._children = list(children)

            run_result = await DebateEngine().run(compiled, context=ctx)

            # Re-sync children from observer (in case it updated them during arbitration)
            children = list(observer._children)
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
