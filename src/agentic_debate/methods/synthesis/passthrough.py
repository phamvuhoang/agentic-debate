"""No-op synthesis used by the compatibility path."""

from __future__ import annotations

from typing import Any

from agentic_debate.context import DebateContext
from agentic_debate.result import DebateRoundResult
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateArbitration


class PassthroughSynthesizer:
    """Return an empty synthesis payload."""

    async def synthesize(
        self,
        *,
        spec: DebateSpec,
        round_result: DebateRoundResult,
        arbitration: DebateArbitration,
        context: DebateContext,
    ) -> dict[str, Any]:
        _ = (spec, round_result, arbitration, context)
        return {}
