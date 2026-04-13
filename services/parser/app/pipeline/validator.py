"""
Data Validator — валидация данных продуктов.
"""
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DataValidator:
    """Валидатор данных продуктов"""

    REQUIRED_FIELDS = ["name", "category", "product_url"]
    VALID_CATEGORIES = [
        "Двери межкомнатные",
        "Стеновые панели",
        "Порталы каминные",
        "Другое"
    ]
    VALID_STYLES = [
        "классика", "неоклассика", "современный", "минимализм",
        "лофт", "скандинавский", "арт-деко", "unknown"
    ]

    def validate_product(self, product: Dict) -> tuple[bool, List[str]]:
        """
        Валидировать данные продукта.

        Args:
            product: Данные продукта

        Returns:
            tuple[bool, List[str]]: (is_valid, errors)
        """
        errors = []

        # Проверка обязательных полей
        for field in self.REQUIRED_FIELDS:
            if not product.get(field):
                errors.append(f"Missing required field: {field}")

        # Проверка категории
        category = product.get("category", "")
        if category and category not in self.VALID_CATEGORIES:
            logger.warning(f"⚠️ Неизвестная категория: {category}")
            # Не ошибка, просто предупреждение

        # Проверка URL
        url = product.get("product_url", "")
        if url and not url.startswith(("http://", "https://")):
            errors.append(f"Invalid URL: {url}")

        # Проверка названия
        name = product.get("name", "")
        if name and len(name) < 2:
            errors.append("Product name too short")

        is_valid = len(errors) == 0
        if is_valid:
            logger.debug(f"✅ Валидация пройдена: {product.get('name')}")
        else:
            logger.warning(f"❌ Валидация не пройдена: {errors}")

        return is_valid, errors

    def clean_product(self, product: Dict) -> Dict:
        """
        Очистить данные продукта.

        Args:
            product: Данные продукта

        Returns:
            Dict: Очищенные данные
        """
        cleaned = {}

        for key, value in product.items():
            if isinstance(value, str):
                cleaned[key] = value.strip()
            elif isinstance(value, list):
                cleaned[key] = [item.strip() if isinstance(item, str) else item for item in value]
            else:
                cleaned[key] = value

        # Значения по умолчанию
        cleaned.setdefault("style", "unknown")
        cleaned.setdefault("color_family", "unknown")
        cleaned.setdefault("material", "Не указан")
        cleaned.setdefault("finish_type", "unknown")
        cleaned.setdefault("special_features", [])
        cleaned.setdefault("original_description", "")
        cleaned.setdefault("ai_semantic_description", "")
        cleaned.setdefault("main_image_url", "")
        cleaned.setdefault("price", None)
        cleaned.setdefault("available_sizes", [])

        return cleaned

    def validate_batch(self, products: List[Dict]) -> Dict:
        """
        Валидировать батч продуктов.

        Args:
            products: Список продуктов

        Returns:
            Dict: Статистика валидации
        """
        valid = []
        invalid = []
        warnings = []

        for product in products:
            is_valid, errors = self.validate_product(product)
            if is_valid:
                cleaned = self.clean_product(product)
                valid.append(cleaned)
            else:
                invalid.append({"product": product, "errors": errors})

        stats = {
            "total": len(products),
            "valid": len(valid),
            "invalid": len(invalid),
            "validation_rate": round(len(valid) / len(products) * 100, 2) if products else 0,
        }

        logger.info(f"📊 Валидация батча: {stats}")
        return {
            "stats": stats,
            "valid_products": valid,
            "invalid_products": invalid,
        }
