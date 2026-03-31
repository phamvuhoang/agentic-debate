"""Output localization protocol and no-op default."""
from __future__ import annotations

from typing import Protocol

from agentic_debate.context import DebateContext


class OutputLocalizer(Protocol):
    """Translates human-readable debate output text to a target locale.

    Called by the engine after transcript_formatter.build() only when
    spec.transcript_policy.output_locale != "en" and an output_localizer
    is wired into CompiledDebate.

    If localize() raises, the engine logs a warning and keeps the original
    English text for that field. DebateRunResult.transcript stores the
    localized version and is the authoritative output.
    """

    async def localize(
        self,
        text: str,
        target_locale: str,
        context: DebateContext,
    ) -> str: ...


class PassthroughLocalizer:
    """No-op localizer. Returns input text unchanged."""

    async def localize(
        self, text: str, target_locale: str, context: DebateContext
    ) -> str:
        return text
