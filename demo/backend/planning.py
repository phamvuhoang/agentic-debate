from __future__ import annotations

from agentic_debate.context import DebateContext
from agentic_debate.llm.base import LlmCaller
from agentic_debate.planning.types import DebatePlan
from agentic_debate.planning.llm import LlmDebatePlanner

from backend.constants import ACCENT_COLORS


async def build_demo_plan(
    topic: str,
    llm: LlmCaller,
    context: DebateContext,
) -> DebatePlan:
    """Build a package-native plan and attach demo presentation metadata."""
    plan = await LlmDebatePlanner(llm=llm).plan_topic(topic, context=context)
    decorated = plan.model_copy(deep=True)

    for index, participant in enumerate(decorated.participants):
        participant.metadata.setdefault(
            "accent_color",
            ACCENT_COLORS[index % len(ACCENT_COLORS)],
        )

    return decorated
