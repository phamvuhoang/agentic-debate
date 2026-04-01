from __future__ import annotations
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from agentic_debate.context import DebateContext
from backend.gemini import GeminiLocalizer, GeminiLlmCaller

@pytest.fixture
def mock_llm_caller():
    caller = MagicMock(spec=GeminiLlmCaller)
    caller.generate_text = AsyncMock(return_value="Translated text")
    return caller

@pytest.mark.asyncio
async def test_gemini_localizer_skips_en(mock_llm_caller):
    localizer = GeminiLocalizer(llm=mock_llm_caller)
    ctx = DebateContext(namespace="test")
    result = await localizer.localize("Hello", "en", ctx)
    assert result == "Hello"
    mock_llm_caller.generate_text.assert_not_called()

@pytest.mark.asyncio
async def test_gemini_localizer_calls_llm_for_other_locales(mock_llm_caller):
    localizer = GeminiLocalizer(llm=mock_llm_caller)
    ctx = DebateContext(namespace="test")
    result = await localizer.localize("Hello", "vi", ctx)
    assert result == "Translated text"
    mock_llm_caller.generate_text.assert_called_once()
    prompt = mock_llm_caller.generate_text.call_args[0][0]
    assert "Vietnamese" in prompt or "vi" in prompt
    assert "Hello" in prompt
