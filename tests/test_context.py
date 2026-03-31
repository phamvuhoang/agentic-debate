"""Tests for DebateContext."""
from __future__ import annotations

from agentic_debate.context import DebateContext


def test_debate_context_defaults():
    ctx = DebateContext(namespace="test.ns")
    assert ctx.namespace == "test.ns"
    assert ctx.run_id is None
    assert ctx.correlation_id is None
    assert ctx.metadata == {}


def test_debate_context_full():
    ctx = DebateContext(
        namespace="test.ns",
        run_id="run-1",
        correlation_id="corr-1",
        metadata={"key": "val"},
    )
    assert ctx.run_id == "run-1"
    assert ctx.metadata["key"] == "val"
