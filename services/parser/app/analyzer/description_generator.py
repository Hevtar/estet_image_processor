"""
Description Generator — генерация визуального анализа и стилевого анализа двери.
"""
import json
import logging
import re
from typing import Dict, Optional

from estet_shared.ai_clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class DescriptionGenerator:
    """
    Генератор AI-описаний продуктов.

    Содержит:
    1. Визуальный анализ изображения двери (фрезеровки, филёнки, поверхность)
    2. Стилевой анализ (подбор совместимых стилей интерьера)
    3. Генерация по тексту для fallback
    """

    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    def _build_visual_description_prompt(
        self,
        product_data: dict,
        collection_info: dict = None,
    ) -> str:
        """
        Промпт для визуального анализа изображения двери.

        Результат содержит:
        1. Визуальное описание полотна (фрезеровки, филёнки, поверхность)
        2. Описание наличников если видны
        3. Анализ стиля и подбор совместимых стилей интерьера
        4. Итоговый связный текст для поля ai_semantic_description
        """
        product_name = product_data.get("name", "")

        collection_context = ""
        if collection_info:
            if collection_info.get("description"):
                collection_context += f"""
ОПИСАНИЕ КОЛЛЕКЦИИ (используй как контекст и терминологический ориентир):
{collection_info['description']}
"""
            if collection_info.get("features"):
                features_text = "\n".join(
                    f"  - {f}" for f in collection_info["features"]
                )
                collection_context += f"""
ЗАЯВЛЕННЫЕ ОСОБЕННОСТИ КОЛЛЕКЦИИ:
{features_text}
"""

        prompt = f"""
Ты эксперт по межкомнатным дверям и дизайну интерьеров.
Твоя задача — проанализировать изображение двери и создать структурированное описание.

ПРОДУКТ: {product_name}
{collection_context}

═══════════════════════════════════════════════════
ЧАСТЬ 1 — ВИЗУАЛЬНЫЙ АНАЛИЗ ДВЕРИ
═══════════════════════════════════════════════════

Внимательно рассмотри изображение. Опиши ТОЛЬКО ТО ЧТО ВИДИШЬ.
Не придумывай детали которых нет на фото.

Для поля "panel_description" опиши:

А. ПОЛОТНО:
   - Тип поверхности: гладкое / с фрезеровками / филенчатое / комбинированное?
   - Если есть ФРЕЗЕРОВКИ:
       * Сколько линий/канавок?
       * Их форма: прямоугольные / скруглённые / V-образные?
       * Расположение: по периметру / вертикальные / горизонтальные / диагональные?
       * Замкнуты ли линии по всему периметру или прерываются?
       * Глубина: поверхностные / выраженные / глубокие?
   - Если есть ФИЛЁНКИ:
       * Количество и расположение (верхняя/нижняя/левая/правая)
       * Форма: прямоугольные / арочные?
       * Тип: врезные / накладные?
   - ОСТЕКЛЕНИЕ: есть / нет? Если есть — форма, размер, расположение
   - ТЕКСТУРА ПОВЕРХНОСТИ: матовая / глянцевая / сатиновая / с текстурой под дерево?
   - ЦВЕТ: опиши точно (молочно-белый / бежевый / серый и т.д.)
   - РУЧКА: тип, материал, форма, наличие подиума

Б. НАЛИЧНИКИ (если видны на изображении):
   - Профиль: плоский / ступенчатый / фигурный / классический с калёвкой?
   - Ширина: узкий (~50мм) / стандартный (~70мм) / широкий (>90мм)?
   - Торец: прямой / скруглённый / с фаской?
   - Стыковка в углах: под 45° / с угловым элементом?

В. ДОПОЛНИТЕЛЬНЫЕ ЭЛЕМЕНТЫ:
   - Подиум для ручки: есть / нет, если есть — форма и размер
   - Молдинги или декоративные накладки
   - Любые другие заметные элементы

═══════════════════════════════════════════════════
ЧАСТЬ 2 — СТИЛЕВОЙ АНАЛИЗ
═══════════════════════════════════════════════════

На основе УВИДЕННОГО на изображении (форма фрезеровок, наличие/отсутствие
декора, пропорции, тип поверхности):

Для поля "door_style" определи:
   - В каком стиле выполнена дверь?
   - Какие визуальные признаки на это указывают?
   - Пример: "Неоклассика с элементами transitional — геометрическая
     ступенчатая рамка без исторических орнаментов, асимметричное
     завершение фрезеровки как современный дизайнерский акцент"

Для поля "compatible_interior_styles" подбери стили интерьера:
   КРИТЕРИИ ПОДБОРА:
   - Стиль двери должен соответствовать характеру интерьера
   - Учитывай: наличие/отсутствие декора, геометрию линий,
     цвет и фактуру поверхности

   СПИСОК СТИЛЕЙ ДЛЯ АНАЛИЗА (выбери подходящие):
   Неоклассика, Современная классика, Transitional, Минимализм,
   Скандинавский стиль, Контемпорари, Ар-деко, Прованс,
   Французский стиль, Американский стиль, Эклектика,
   Лофт, Хай-тек, Индустриальный, Японский минимализм,
   Рустик, Шале, Кантри, Средиземноморский

Для поля "incompatible_styles" укажи стили где дверь будет неуместна
и объясни кратко почему.

═══════════════════════════════════════════════════
ФОРМАТ ОТВЕТА
═══════════════════════════════════════════════════

Верни строго валидный JSON без markdown обёртки:

{{
  "panel_description": "детальное описание полотна двери на основе изображения",
  "casing_description": "описание наличников или 'Наличники на изображении не представлены'",
  "additional_elements": "дополнительные видимые элементы или пустая строка",
  "style_analysis": {{
    "door_style": "стиль в котором выполнена дверь с обоснованием",
    "compatible_interior_styles": ["Стиль 1", "Стиль 2", "Стиль 3"],
    "incompatible_styles": ["Стиль А — причина", "Стиль Б — причина"]
  }},
  "full_description": "связный читаемый текст 4-6 предложений объединяющий визуальное описание и стилевую характеристику"
}}

ТРЕБОВАНИЯ К full_description:
- Первые 2-3 предложения: что видно на двери (полотно, фрезеровки, поверхность)
- Последние 1-2 предложения: в каких интерьерах уместна
- Конкретно и точно: не "красивая дверь" а "три параллельные фрезеровки по периметру"
- Без упоминания бренда, цены, доставки
- Без фраз "на изображении", "я вижу", "судя по фото"
"""
        return prompt

    def _detect_mime_type(self, image_bytes: bytes) -> str:
        """
        Определяет MIME-тип изображения по сигнатуре байт.
        """
        if image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return "image/webp"
        elif image_bytes[:3] == b'\xff\xd8\xff':
            return "image/jpeg"
        elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        else:
            # Fallback — большинство изображений на сайте webp
            return "image/webp"

    def _parse_json_response(self, response_text: str) -> dict:
        """
        Парсит JSON из ответа Gemini.
        Обрабатывает markdown обёртку ```json ... ```
        """
        if not response_text:
            return {}

        clean = response_text.strip()

        # Убираем markdown обёртку
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if json_match:
            clean = json_match.group(1).strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Невалидный JSON в ответе AI: {e}")
            logger.debug(f"Ответ AI: {response_text[:500]}")
            # Fallback — сохраняем текст как full_description
            return {
                "panel_description": "",
                "casing_description": "",
                "additional_elements": "",
                "style_analysis": {
                    "door_style": "",
                    "compatible_interior_styles": [],
                    "incompatible_styles": [],
                },
                "full_description": response_text.strip(),
            }

    async def generate_from_image(
        self,
        image_bytes: bytes,
        product_data: dict,
        collection_info: dict = None,
    ) -> dict:
        """
        Генерирует визуальное описание и стилевой анализ двери.

        Args:
            image_bytes:     Байты изображения продукта (webp/jpg/png)
            product_data:    Метаданные продукта из scraper
            collection_info: Данные коллекции как контекст (опционально)

        Returns:
            dict: {
                "panel_description":   str,
                "casing_description":  str,
                "additional_elements": str,
                "style_analysis": {
                    "door_style":                str,
                    "compatible_interior_styles": List[str],
                    "incompatible_styles":        List[str]
                },
                "full_description": str   ← записывается в ai_semantic_description
            }

        Возвращает {} если изображение не передано или произошла ошибка.
        """
        if not image_bytes:
            logger.warning(
                f"⚠️ Нет изображения для '{product_data.get('name')}'. "
                f"Пропускаем визуальный анализ."
            )
            return {}

        prompt = self._build_visual_description_prompt(
            product_data=product_data,
            collection_info=collection_info,
        )

        mime_type = self._detect_mime_type(image_bytes)

        try:
            response = await self.client.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                mime_type=mime_type,
                max_tokens=2048,
                temperature=0.2,
            )

            # analyze_image может вернуть уже распарсенный JSON (если ответ был валидный JSON)
            # или {"content": "текст"} (если не JSON)
            if response.get("panel_description") or response.get("full_description"):
                # Ответ уже распарсен — используем напрямую
                result = response
            else:
                # Ответ в поле "content" — нужно распарсить
                result = self._parse_json_response(response.get("content", ""))

            # Валидация результата
            full_desc = result.get("full_description", "")
            style_analysis = result.get("style_analysis", {})
            compatible_styles = style_analysis.get("compatible_interior_styles", [])

            if len(full_desc) < 100:
                logger.warning(
                    f"⚠️ Слишком короткое описание ({len(full_desc)} симв.) "
                    f"для '{product_data.get('name')}'. Возможно ИИ не увидел изображение."
                )

            if not compatible_styles:
                logger.warning(
                    f"⚠️ Не получены совместимые стили для '{product_data.get('name')}'"
                )

            logger.info(
                f"✅ Визуальный анализ завершён: '{product_data.get('name')}'\n"
                f"   Описание: {len(full_desc)} символов\n"
                f"   Стиль двери: {style_analysis.get('door_style', 'не определён')[:80]}\n"
                f"   Совместимых стилей: {len(compatible_styles)}"
            )

            return result

        except Exception as e:
            logger.error(
                f"❌ Ошибка визуального анализа '{product_data.get('name')}': {e}",
                exc_info=True
            )
            return {}

    async def generate_from_text(self, product_data: Dict) -> Optional[Dict]:
        """
        Генерирует описание только на основе текстовых данных (fallback).

        Args:
            product_data: Данные продукта

        Returns:
            Dict: Сгенерированное описание или None
        """
        prompt = f"""
Ты эксперт по межкомнатным дверям и дизайну интерьеров.
Опиши продукт на основе текстовых данных.

Название: {product_data.get("name", "Неизвестно")}
Категория: {product_data.get("category", "Неизвестно")}
Стиль: {product_data.get("style", "unknown")}
Цвет: {product_data.get("color_family", "unknown")}
Материал: {product_data.get("material", "Не указан")}
Отделка: {product_data.get("finish_type", "unknown")}
"""
        if product_data.get("original_description"):
            prompt += f"\nОригинальное описание:\n{product_data['original_description']}"

        prompt += """
\nСоздай описание в формате JSON:
{
    "full_description": "Подробное описание продукта (3-5 предложений)",
    "short_description": "Краткое описание (1-2 предложения)"
}
"""

        try:
            result = await self.client.generate_text(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.2,
            )

            content = result.get("content", "")
            if content:
                parsed = self._parse_json_response(content)
                if parsed.get("full_description"):
                    return parsed
                return {"full_description": content}

            return None

        except Exception as e:
            logger.error(f"❌ Ошибка генерации описания: {e}")
            return None
