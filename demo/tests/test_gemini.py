from __future__ import annotations
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from pydantic import BaseModel
from agentic_debate.context import DebateContext


class _SampleModel(BaseModel):
    name: str
    value: int


@pytest.fixture
def mock_genai_client():
    client = MagicMock()
    response = MagicMock()
    response.text = json.dumps({"name": "test", "value": 42})
    client.aio = MagicMock()
    client.aio.models = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=response)
    return client


@pytest.mark.asyncio
async def test_gemini_llm_caller_returns_parsed_model(mock_genai_client):
    from backend.gemini import GeminiLlmCaller
    caller = GeminiLlmCaller(client=mock_genai_client)
    ctx = DebateContext(namespace="test")
    result = await caller.generate_structured("prompt", _SampleModel, context=ctx)
    assert isinstance(result, _SampleModel)
    assert result.name == "test"
    assert result.value == 42


@pytest.mark.asyncio
async def test_gemini_llm_caller_passes_model_name(mock_genai_client):
    from backend.gemini import GeminiLlmCaller
    caller = GeminiLlmCaller(client=mock_genai_client, model="test-model-sentinel")
    ctx = DebateContext(namespace="test")
    await caller.generate_structured("my prompt", _SampleModel, context=ctx)
    call_kwargs = mock_genai_client.aio.models.generate_content.call_args
    assert call_kwargs.kwargs["model"] == "test-model-sentinel"
    assert call_kwargs.kwargs["contents"] == "my prompt"
