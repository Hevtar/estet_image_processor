"""
Клиент для Gemini API через Polza.ai.
"""
import asyncio
import base64
import json
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GeminiClient:
    """Клиент для работы с Gemini через Polza.ai"""

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.polza.ai/v1",
        model: str = "google/gemini-2.0-flash-lite",
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.max_retries = max_retries

    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
        max_tokens: int = 2048,
        temperature: float = 0.2,
    ) -> Dict:
        """
        Анализирует изображение с помощью Gemini.

        Args:
            image_bytes: Байты изображения
            prompt: Текстовый промпт
            mime_type: MIME тип изображения
            max_tokens: Максимум токенов в ответе
            temperature: Температура генерации

        Returns:
            Dict с результатом анализа
        """
        # Конвертируем в base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{base64_image}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_uri, "detail": "high"}
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        return await self._call_api_with_retry(payload)

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Dict:
        """
        Генерирует текст без изображения.

        Args:
            prompt: Текстовый промпт
            max_tokens: Максимум токенов
            temperature: Температура

        Returns:
            Dict с результатом
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        return await self._call_api_with_retry(payload)

    async def generate_embedding(
        self,
        text: str,
        model: str = "google/gemini-embedding-001"
    ) -> List[float]:
        """
        Генерирует embedding для текста через Polza.ai embeddings API.

        Args:
            text: Текст для embedding
            model: Модель для embeddings

        Returns:
            List[float]: Вектор embedding (768 dimensions для gemini-embedding-001)
        """
        try:
            payload = {
                "model": model,
                "input": text,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/embeddings",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Polza возвращает формат: {"data": [{"embedding": [...]}]}
                embedding = data["data"][0]["embedding"]
                logger.debug(f"✅ Embedding сгенерирован: {len(embedding)} dimensions")
                return embedding

        except Exception as e:
            logger.error(f"❌ Ошибка генерации embedding: {e}")
            # Fallback — заглушка
            return [0.0] * 768

    async def _call_api_with_retry(self, payload: Dict) -> Dict:
        """Вызов API с retry логикой"""
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{self.api_url}/chat/completions",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        }
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Извлекаем контент
                    content = data["choices"][0]["message"]["content"]

                    # Пытаемся распарсить как JSON (если промпт требовал JSON)
                    try:
                        cleaned = content.strip()
                        if cleaned.startswith("```"):
                            lines = cleaned.split("\n")
                            cleaned = "\n".join(lines[1:-1])
                        return json.loads(cleaned)
                    except json.JSONDecodeError:
                        # Если не JSON, возвращаем как есть
                        return {"content": content}

            except httpx.TimeoutException:
                logger.warning(f"⏱️ Timeout на попытке {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

            except Exception as e:
                logger.error(f"❌ Ошибка API на попытке {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

        raise Exception("Max retries exceeded")
