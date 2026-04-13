"""
Утилиты для обработки изображений.
"""
import hashlib
import io
import logging
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Утилиты для обработки изображений"""

    @staticmethod
    def calculate_hash(image_bytes: bytes) -> str:
        """Вычисляет SHA256 хеш изображения"""
        return hashlib.sha256(image_bytes).hexdigest()

    @staticmethod
    def get_dimensions(image_bytes: bytes) -> Optional[Tuple[int, int]]:
        """Получает размеры изображения"""
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                return img.size  # (width, height)
        except Exception as e:
            logger.error(f"Ошибка получения размеров: {e}")
            return None

    @staticmethod
    def validate_image(image_bytes: bytes, max_size_mb: int = 10) -> bool:
        """Валидирует изображение"""
        # Проверяем размер файла
        if len(image_bytes) > max_size_mb * 1024 * 1024:
            logger.warning(f"Изображение слишком большое: {len(image_bytes) / 1024 / 1024:.2f}MB")
            return False

        # Проверяем что это валидное изображение
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
            return True
        except Exception as e:
            logger.error(f"Невалидное изображение: {e}")
            return False

    @staticmethod
    def resize_if_needed(image_bytes: bytes, max_width: int = 1920, max_height: int = 1920) -> bytes:
        """Изменяет размер если нужно"""
        with Image.open(io.BytesIO(image_bytes)) as img:
            if img.width <= max_width and img.height <= max_height:
                return image_bytes

            # Сохраняем пропорции
            ratio = min(max_width / img.width, max_height / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

            output = io.BytesIO()
            img.save(output, format=img.format or "JPEG")
            return output.getvalue()
