"""Challenge source for already-generated counter-hypotheses."""

from __future__ import annotations

from agentic_debate.context import DebateContext
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateChallenge


class PrecomputedChallengeSource:
    """Return a pre-specified list of challenges unchanged."""

    def __init__(self, challenges: list[DebateChallenge]) -> None:
        self._challenges = list(challenges)

    async def collect(self, spec: DebateSpec, context: DebateContext) -> list[DebateChallenge]:
        _ = (spec, context)
        return list(self._challenges)
