"""Typed context passed through the debate engine lifecycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DebateContext:
    """Carries run-level metadata through the neutral debate engine.

    All fields except `namespace` are optional so that host adapters can
    populate only what they have available. Engine internals always receive
    a DebateContext instance — never None or a plain dict.
    """

    namespace: str
    run_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
