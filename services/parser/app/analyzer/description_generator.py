"""
Description Generator — генерация AI-описаний через Gemini.
"""
import json
import logging
from typing import Dict, Optional

from estet_shared.ai_clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


# Промпт для генерации описания продукта
PRODUCT_DESCRIPTION_PROMPT = """
Ты — эксперт по описанию межкомнатных дверей и стеновых панелей фабрики ESTET.
Проанализируй изображение и данные о продукте, затем создай подробное описание.

Данные продукта:
- Название: {name}
- Категория: {category}
- Стиль: {style}
- Цвет: {color}
- Материал: {material}
- Отделка: {finish}

Создай описание в формате JSON со следующими полями:
{{
    "short_description": "Краткое описание (1-2 предложения)",
    "full_description": "Полное описание (3-5 предложений, включая характеристики)",
    "key_features": ["особенность 1", "особенность 2", ...],
    "recommended_interior": ["тип интерьера 1", ...],
    "style_tags": ["тег стиля 1", ...]
}}

Описание должно быть на русском языке, маркетингово привлекательным и информативным.
"""


class DescriptionGenerator:
    """Генератор AI-описаний продуктов"""

    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    async def generate_from_image(
        self,
        image_bytes: bytes,
        product_data: Dict,
        mime_type: str = "image/jpeg"
    ) -> Optional[Dict]:
        """
        Генерирует описание продукта на основе изображения и данных.

        Args:
            image_bytes: Байты изображения
            product_data: Данные продукта
            mime_type: MIME тип изображения

        Returns:
            Dict: Сгенерированное описание или None
        """
        prompt = PRODUCT_DESCRIPTION_PROMPT.format(
            name=product_data.get("name", "Неизвестно"),
            category=product_data.get("category", "Неизвестно"),
            style=product_data.get("style", "unknown"),
            color=product_data.get("color_family", "unknown"),
            material=product_data.get("material", "Не указан"),
            finish=product_data.get("finish_type", "unknown"),
        )

        try:
            result = await self.client.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                mime_type=mime_type,
                max_tokens=2048,
                temperature=0.2,
            )

            logger.info(f"✨ Сгенерировано описание для: {product_data.get('name', 'Unknown')}")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка генерации описания: {e}")
            return None

    async def generate_from_text(self, product_data: Dict) -> Optional[Dict]:
        """
        Генерирует описание только на основе текстовых данных.

        Args:
            product_data: Данные продукта

        Returns:
            Dict: Сгенерированное описание или None
        """
        prompt = PRODUCT_DESCRIPTION_PROMPT.format(
            name=product_data.get("name", "Неизвестно"),
            category=product_data.get("category", "Неизвестно"),
            style=product_data.get("style", "unknown"),
            color=product_data.get("color_family", "unknown"),
            material=product_data.get("material", "Не указан"),
            finish=product_data.get("finish_type", "unknown"),
        )

        # Добавляем оригинальное описание если есть
        if product_data.get("original_description"):
            prompt += f"\n\nОригинальное описание:\n{product_data['original_description']}"

        try:
            result = await self.client.generate_text(
                prompt=prompt,
                max_tokens=2048,
                temperature=0.2,
            )

            # Пытаемся распарсить JSON из контента
            content = result.get("content", "")
            if content:
                try:
                    # Извлекаем JSON из markdown code block если есть
                    if "```" in content:
                        lines = content.split("\n")
                        json_lines = []
                        in_json = False
                        for line in lines:
                            if line.strip().startswith("```json") or line.strip().startswith("```"):
                                in_json = not in_json
                                continue
                            if in_json:
                                json_lines.append(line)
                        content = "\n".join(json_lines)

                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("Не удалось распарсить JSON из ответа")
                    return {"full_description": content}

            return None

        except Exception as e:
            logger.error(f"❌ Ошибка генерации описания: {e}")
            return None
