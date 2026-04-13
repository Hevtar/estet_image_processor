"""
Image Analyzer — анализ изображений через Gemini.
"""
import logging
from typing import Dict, Optional

from estet_shared.ai_clients.gemini_client import GeminiClient
from ..config import settings

logger = logging.getLogger(__name__)


# Промпт для анализа изображения клиента
IMAGE_ANALYSIS_PROMPT = """
Проанализируй изображение интерьера и определи характеристики, которые помогут подобрать подходящие двери.

Определи:
1. Общий стиль интерьера (современный, классика, минимализм, лофт и т.д.)
2. Цветовая палитра (преобладающие цвета)
3. Тип материалов (дерево, металл, стекло, ткань)
4. Общее настроение (теплое, холодное, уютное, строгое)

Ответь в формате JSON:
{{
    "style": "определенный стиль",
    "colors": ["цвет1", "цвет2", ...],
    "materials": ["материал1", ...],
    "mood": "настроение",
    "description": "Краткое описание интерьера (2-3 предложения)",
    "recommended_door_styles": ["рекомендуемый стиль двери 1", ...],
    "recommended_door_colors": ["рекомендуемый цвет двери 1", ...]
}}
"""


class ImageAnalyzer:
    """Анализатор изображений клиентов"""

    def __init__(self):
        self.client = GeminiClient(
            api_key=settings.POLZA_API_KEY,
            api_url=settings.POLZA_API_URL,
            model=settings.GEMINI_MODEL,
        )

    async def analyze(self, image_bytes: bytes, mime_type: str = "image/jpeg") -> Dict:
        """
        Анализировать изображение клиента.

        Args:
            image_bytes: Байты изображения
            mime_type: MIME тип

        Returns:
            Dict: Результат анализа
        """
        try:
            result = await self.client.analyze_image(
                image_bytes=image_bytes,
                prompt=IMAGE_ANALYSIS_PROMPT,
                mime_type=mime_type,
                max_tokens=settings.GEMINI_MAX_TOKENS,
                temperature=settings.GEMINI_TEMPERATURE,
            )

            logger.info("✅ Изображение проанализировано")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка анализа изображения: {e}")
            return {
                "style": "unknown",
                "colors": [],
                "materials": [],
                "mood": "unknown",
                "description": "Не удалось проанализировать изображение",
                "recommended_door_styles": [],
                "recommended_door_colors": [],
            }
