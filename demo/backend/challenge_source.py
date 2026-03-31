from __future__ import annotations

from typing import Awaitable, Callable
from pydantic import BaseModel

from agentic_debate.context import DebateContext
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateChallenge

from backend.prompts import CHALLENGE_PROMPT, FIRST_ROUND_CHALLENGE_PROMPT


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
        participants = spec.participants
        n = len(participants)
        max_rounds = spec.round_policy.max_rounds

        if n < 2:
            raise ValueError(f"LlmChallengeSource requires at least 2 participants, got {n}")

        challenges: list[DebateChallenge] = []
        # prior_args[participant_id] = argument this participant received (used in their next turn to rebut)
        prior_args: dict[str, str] = {}

        for round_idx in range(1, max_rounds + 1):
            for i, challenger in enumerate(participants):
                target = participants[(i + 1) % n]
                prior = prior_args.get(challenger.participant_id, "")

                if round_idx == 1:
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
