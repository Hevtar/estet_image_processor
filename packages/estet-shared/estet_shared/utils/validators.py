"""
Валидаторы для ESTET Platform.
"""
import re
from typing import Optional


def validate_url(url: str) -> bool:
    """Валидирует URL"""
    pattern = re.compile(
        r'^https?://'  # http:// или https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and pattern.search(url) is not None


def validate_image_size(size_bytes: int, max_size_mb: int = 10) -> bool:
    """Валидирует размер изображения"""
    return size_bytes <= max_size_mb * 1024 * 1024
