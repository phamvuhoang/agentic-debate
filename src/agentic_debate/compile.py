"""Compilation helpers for a resolved debate plan."""

from __future__ import annotations

from dataclasses import dataclass
from agentic_debate.context import DebateContext
from agentic_debate.localization import OutputLocalizer
from agentic_debate.protocols import (
    Arbitrator,
    ChallengeSource,
    DebateObserver,
    GroupingStrategy,
    Synthesizer,
    TranscriptFormatter,
)
from agentic_debate.spec import DebateSpec


@dataclass(slots=True)
class CompiledDebate:
    """A fully wired debate execution plan."""

    spec: DebateSpec
    challenge_source: ChallengeSource
    grouping: GroupingStrategy
    arbitrator: Arbitrator
    synthesizer: Synthesizer
    transcript_formatter: TranscriptFormatter
    observers: list[DebateObserver]
    output_localizer: OutputLocalizer | None = None


class DebateCompiler:
    """Static compiler used by adapters to assemble a debate execution plan."""

    def __init__(
        self,
        *,
        challenge_source: ChallengeSource,
        grouping: GroupingStrategy,
        arbitrator: Arbitrator,
        synthesizer: Synthesizer,
        transcript_formatter: TranscriptFormatter,
        observers: list[DebateObserver] | None = None,
        output_localizer: OutputLocalizer | None = None,
    ) -> None:
        self._challenge_source = challenge_source
        self._grouping = grouping
        self._arbitrator = arbitrator
        self._synthesizer = synthesizer
        self._transcript_formatter = transcript_formatter
        self._observers = list(observers or [])
        self._output_localizer = output_localizer

    async def compile(self, spec: DebateSpec, context: DebateContext | None = None) -> CompiledDebate:
        """Return a compiled debate.

        `context` is accepted to support future dynamic compilation but is not
        needed for the initial static compiler.
        """
        _ = context
        return CompiledDebate(
            spec=spec,
            challenge_source=self._challenge_source,
            grouping=self._grouping,
            arbitrator=self._arbitrator,
            synthesizer=self._synthesizer,
            transcript_formatter=self._transcript_formatter,
            observers=self._observers,
            output_localizer=self._output_localizer,
        )
