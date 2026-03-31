"""Default host-agnostic transcript formatter."""
from __future__ import annotations

from typing import Any

from agentic_debate.context import DebateContext
from agentic_debate.result import DebateRoundResult
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateArbitration


class SimpleTranscriptFormatter:
    """Returns a clean, host-agnostic transcript dict.

    Uses neutral key names. Host adapters replace this with their own
    formatter to produce application-specific output shapes.
    """

    async def build(
        self,
        *,
        spec: DebateSpec,
        round_result: DebateRoundResult,
        arbitration: DebateArbitration,
        synthesis: dict[str, Any],
        context: DebateContext,
    ) -> dict[str, Any]:
        return {
            "namespace": spec.namespace,
            "challenges": [c.model_dump() for c in round_result.challenges],
            "topic_groups": [
                {
                    "topic": g.topic,
                    "challenges": [c.model_dump() for c in g.challenges],
                }
                for g in round_result.topic_groups
            ],
            "verdicts": [v.model_dump() for v in arbitration.verdicts],
            "summary": arbitration.summary,
            "contested_topics": list(arbitration.contested_topics),
        }
