"""Deterministic heuristic arbitrator used for compatibility and fallback."""

from __future__ import annotations

from typing import Literal

from agentic_debate.context import DebateContext
from agentic_debate.spec import DebateSpec
from agentic_debate.types import DebateArbitration, DebateTopicGroup, DebateVerdict


class HeuristicArbitrator:
    """Deterministic confidence-threshold arbitrator used as a fallback."""

    async def arbitrate(
        self,
        groups: list[DebateTopicGroup],
        spec: DebateSpec,
        context: DebateContext,
    ) -> DebateArbitration:
        _ = (spec, context)
        verdicts: list[DebateVerdict] = []

        challenge_count = 0
        for group in groups:
            topic_challenges = list(group.challenges)
            challenge_count += len(topic_challenges)
            if not topic_challenges:
                continue
            target_counts: dict[str, int] = {}
            for challenge in topic_challenges:
                target_counts[challenge.target_id] = target_counts.get(challenge.target_id, 0) + 1
            dominant_target = max(target_counts, key=lambda key: target_counts[key])
            avg_confidence = sum(challenge.confidence for challenge in topic_challenges) / len(topic_challenges)
            winning_participant_id = (
                "unresolved"
                if avg_confidence < 0.5
                else topic_challenges[0].challenger_id
            )
            consensus_level: Literal["strong", "moderate", "contested"] = "contested" if avg_confidence < 0.6 else "moderate"
            verdicts.append(
                DebateVerdict(
                    topic=group.topic,
                    winning_participant_id=str(winning_participant_id),
                    confidence=round(avg_confidence, 2),
                    rationale=(
                        f"Heuristic arbitration: {len(topic_challenges)} challenge(s) on '{group.topic}'. "
                        f"Target lens '{dominant_target}' received most challenges."
                    ),
                    open_questions=["Requires human review to resolve definitively."],
                    consensus_level=consensus_level,
                )
            )

        contested_topics = [verdict.topic for verdict in verdicts if verdict.consensus_level == "contested"]
        return DebateArbitration(
            verdicts=verdicts,
            summary=(
                f"Heuristic debate: {challenge_count} challenge(s) across "
                f"{len(groups)} topic(s) processed without LLM arbitration."
            ),
            contested_topics=contested_topics,
        )
