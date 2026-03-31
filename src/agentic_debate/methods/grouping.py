"""Grouping strategies for neutral debate challenges."""

from __future__ import annotations

from collections import defaultdict

from agentic_debate.context import DebateContext
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateChallenge, DebateTopicGroup


class GroupByTopicStrategy:
    """Group challenges by their topic string."""

    async def group(
        self,
        challenges: list[DebateChallenge],
        spec: DebateSpec,
        context: DebateContext,
    ) -> list[DebateTopicGroup]:
        _ = (spec, context)
        grouped: dict[str, list[DebateChallenge]] = defaultdict(list)
        for challenge in challenges:
            grouped[challenge.topic or "general"].append(challenge)
        return [
            DebateTopicGroup(topic=topic, challenges=topic_challenges)
            for topic, topic_challenges in grouped.items()
        ]
