from __future__ import annotations

from agentic_debate.context import DebateContext
from agentic_debate.llm.base import LlmCaller
from agentic_debate.planning.types import DebatePlan
from agentic_debate.planning.llm import LlmDebatePlanner

from backend.constants import ACCENT_COLORS

_DEMO_PARTICIPANT_UPPER_BOUND = 10
_DEMO_ROUND_UPPER_BOUND = 5


async def build_demo_plan(
    topic: str,
    llm: LlmCaller,
    context: DebateContext,
    participant_count: int | None = None,
    round_count: int | None = None,
    max_participants: int | None = None,
    max_rounds: int | None = None,
) -> DebatePlan:
    """Build a package-native plan and attach demo presentation metadata."""
    plan = await LlmDebatePlanner(llm=llm).plan_topic(
        topic,
        context=context,
        participant_count=participant_count,
        round_count=round_count,
        max_participants=max_participants,
        max_rounds=max_rounds,
        participant_upper_bound=_DEMO_PARTICIPANT_UPPER_BOUND,
        round_upper_bound=_DEMO_ROUND_UPPER_BOUND,
    )
    decorated = plan.model_copy(deep=True)

    for index, participant in enumerate(decorated.participants):
        participant.metadata.setdefault(
            "accent_color",
            ACCENT_COLORS[index % len(ACCENT_COLORS)],
        )
        participant.metadata.setdefault("seat_index", index)
        participant.metadata.setdefault("emblem", f"sigil-{index + 1}")

    return decorated
