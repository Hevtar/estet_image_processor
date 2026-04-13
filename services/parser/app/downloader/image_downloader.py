"""
Image Downloader — асинхронное скачивание изображений.
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

from ..config import settings

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Асинхронный загрузчик изображений"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or settings.PARSER_IMAGES_PATH)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.downloaded: Dict[str, str] = {}  # url -> local_path

    async def download_image(
        self,
        url: str,
        filename: Optional[str] = None,
        subdir: str = "products"
    ) -> Optional[str]:
        """
        Скачать одно изображение.

        Args:
            url: URL изображения
            filename: Имя файла (опционально)
            subdir: Поддиректория

        Returns:
            Optional[str]: Локальный путь или None при ошибке
        """
        if url in self.downloaded:
            logger.debug(f"♻️ Уже скачано: {url}")
            return self.downloaded[url]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️ Ошибка загрузки {url}: HTTP {response.status}")
                        return None

                    content = await response.read()

                    # Определяем имя файла
                    if not filename:
                        filename = self._generate_filename(url)

                    # Создаем директорию
                    target_dir = self.output_dir / subdir
                    target_dir.mkdir(parents=True, exist_ok=True)

                    filepath = target_dir / filename

                    # Сохраняем
                    filepath.write_bytes(content)
                    logger.info(f"📥 Скачано: {url} -> {filepath}")

                    local_path = str(filepath)
                    self.downloaded[url] = local_path
                    return local_path

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки {url}: {e}")
            return None

    async def download_images(
        self,
        urls: List[str],
        subdir: str = "products",
        max_concurrent: int = 5
    ) -> Dict[str, Optional[str]]:
        """
        Скачать несколько изображений параллельно.

        Args:
            urls: Список URL изображений
            subdir: Поддиректория
            max_concurrent: Максимум параллельных запросов

        Returns:
            Dict[str, Optional[str]]: URL -> локальный путь
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def download_with_semaphore(url):
            async with semaphore:
                return await self.download_image(url, subdir=subdir)

        tasks = [download_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)

        return dict(zip(urls, results))

    def _generate_filename(self, url: str) -> str:
        """Генерирует имя файла из URL"""
        import hashlib
        # Используем хеш URL для уникальности
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        # Пытаемся извлечь расширение
        ext = ".jpg"  # default
        if "." in url.split("/")[-1]:
            ext = "." + url.split("/")[-1].split(".")[-1].split("?")[0]
            if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                ext = ".jpg"
        return f"{url_hash}{ext}"

    def get_stats(self) -> Dict:
        """Получить статистику загрузок"""
        total_size = 0
        for path in self.downloaded.values():
            try:
                total_size += os.path.getsize(path)
            except OSError:
                pass

        return {
            "downloaded": len(self.downloaded),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
        }
