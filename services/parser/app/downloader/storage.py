"""
Storage — управление локальным хранилищем изображений.
"""
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class StorageManager:
    """Управление хранилищем данных"""

    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.images_path = self.base_path / "images"
        self.raw_path = self.base_path / "raw"
        self.processed_path = self.base_path / "processed"

    def initialize(self):
        """Инициализировать структуру директорий"""
        for path in [self.images_path, self.raw_path, self.processed_path]:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Директория создана: {path}")

    def save_html(self, html: str, filename: str) -> str:
        """Сохранить HTML"""
        self.raw_path.mkdir(parents=True, exist_ok=True)
        filepath = self.raw_path / filename
        filepath.write_text(html, encoding="utf-8")
        logger.info(f"💾 Сохранен HTML: {filepath}")
        return str(filepath)

    def save_json(self, data: dict, filename: str) -> str:
        """Сохранить JSON"""
        import json
        self.processed_path.mkdir(parents=True, exist_ok=True)
        filepath = self.processed_path / filename
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"💾 Сохранен JSON: {filepath}")
        return str(filepath)

    def save_image(self, image_bytes: bytes, filename: str, subdir: str = "products") -> str:
        """Сохранить изображение"""
        target_dir = self.images_path / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        filepath = target_dir / filename
        filepath.write_bytes(image_bytes)
        logger.info(f"🖼️ Сохранено изображение: {filepath}")
        return str(filepath)

    def file_exists(self, filepath: str) -> bool:
        """Проверить существование файла"""
        return Path(filepath).exists()

    def get_file_size(self, filepath: str) -> int:
        """Получить размер файла"""
        return Path(filepath).stat().st_size if Path(filepath).exists() else 0

    def cleanup(self, older_than_days: int = 30):
        """Очистить старые файлы"""
        import time
        now = time.time()
        cutoff = now - (older_than_days * 86400)

        for path in [self.raw_path, self.processed_path]:
            if path.exists():
                for file in path.iterdir():
                    if file.is_file() and file.stat().st_mtime < cutoff:
                        file.unlink()
                        logger.info(f"🗑️ Удален старый файл: {file}")

    def get_storage_stats(self) -> dict:
        """Получить статистику хранилища"""
        import shutil

        def get_dir_size(path: Path) -> int:
            total = 0
            if path.exists():
                for file in path.rglob("*"):
                    if file.is_file():
                        total += file.stat().st_size
            return total

        return {
            "images_size_mb": round(get_dir_size(self.images_path) / 1024 / 1024, 2),
            "raw_size_mb": round(get_dir_size(self.raw_path) / 1024 / 1024, 2),
            "processed_size_mb": round(get_dir_size(self.processed_path) / 1024 / 1024, 2),
        }
