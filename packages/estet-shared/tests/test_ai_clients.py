"""
Тесты для AI клиентов.
"""
import pytest
from unittest.mock import AsyncMock, patch
from estet_shared.ai_clients.gemini_client import GeminiClient


class TestGeminiClient:
    """Тесты Gemini клиента"""

    def test_init(self):
        client = GeminiClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.model == "google/gemini-2.0-flash-lite"
        assert client.max_retries == 3

    @pytest.mark.asyncio
    async def test_generate_text(self):
        # TODO: Реализовать интеграционные тесты с моком API
        pass
