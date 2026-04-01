"""LLM-backed challenge generation."""

from __future__ import annotations

from typing import Awaitable, Callable

from pydantic import BaseModel

from agentic_debate.context import DebateContext
from agentic_debate.errors import DebateConfigurationError, DebateGenerationError
from agentic_debate.llm.base import LlmCaller
from agentic_debate.prompts import ChallengePromptSet, load_builtin_challenge_prompt_set
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateChallenge, DebateParticipant


class _ChallengeOutput(BaseModel):
    challenge_text: str
    topic_tag: str
    confidence: float


class LlmChallengeSource:
    """Generate debate challenges from a resolved spec using an LLM caller."""

    def __init__(
        self,
        *,
        llm: LlmCaller,
        prompt_set: ChallengePromptSet | None = None,
        on_challenge: Callable[[DebateChallenge], Awaitable[None]] | None = None,
    ) -> None:
        self._llm = llm
        self._prompt_set = prompt_set or load_builtin_challenge_prompt_set()
        self._on_challenge = on_challenge

    async def collect(self, spec: DebateSpec, context: DebateContext) -> list[DebateChallenge]:
        participants = spec.participants
        if len(participants) < 2:
            raise DebateConfigurationError("LlmChallengeSource requires at least two participants")
        if spec.round_policy.mode == "precomputed":
            raise DebateConfigurationError(
                "LlmChallengeSource does not support precomputed round mode"
            )

        challenges: list[DebateChallenge] = []
        prior_args: dict[str, str] = {}

        for round_index in range(1, spec.round_policy.max_rounds + 1):
            for challenger, target in _iter_turns(participants, spec.round_policy.mode):
                try:
                    output = await self._llm.generate_structured(
                        self._build_prompt(
                            round_index=round_index,
                            challenger=challenger,
                            target=target,
                            topic=spec.subject.title,
                            prior_argument=prior_args.get(challenger.participant_id, ""),
                        ),
                        _ChallengeOutput,
                        context=context,
                    )
                except Exception as exc:
                    raise DebateGenerationError(stage="challenge_generation", message=str(exc)) from exc

                challenge = DebateChallenge(
                    round_index=round_index,
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

    def _build_prompt(
        self,
        *,
        round_index: int,
        challenger: DebateParticipant,
        target: DebateParticipant,
        topic: str,
        prior_argument: str,
    ) -> str:
        if round_index == 1:
            return self._prompt_set.first_round_prompt_template.format(
                challenger_label=challenger.label,
                challenger_stance=challenger.stance or "neutral",
                topic=topic,
                round_index=round_index,
            )

        return self._prompt_set.rebuttal_prompt_template.format(
            challenger_label=challenger.label,
            challenger_stance=challenger.stance or "neutral",
            topic=topic,
            target_label=target.label,
            prior_argument=prior_argument,
            round_index=round_index,
        )


def _iter_turns(
    participants: list[DebateParticipant],
    mode: str,
) -> list[tuple[DebateParticipant, DebateParticipant]]:
    if mode == "round_robin":
        return [
            (challenger, participants[(index + 1) % len(participants)])
            for index, challenger in enumerate(participants)
        ]
    if mode == "pairwise":
        return [
            (challenger, target)
            for challenger in participants
            for target in participants
            if challenger.participant_id != target.participant_id
        ]
    raise DebateConfigurationError(f"Unsupported LlmChallengeSource round mode: {mode}")
