"""
Главный скрипт запуска парсинга.

Использование:
    python scripts/run_parser.py                  # Полный парсинг
    python scripts/run_parser.py --collection URL  # Парсинг коллекции
    python scripts/run_parser.py --product URL     # Парсинг продукта
    python scripts/run_parser.py --skip-images     # Без скачивания изображений
    python scripts/run_parser.py --skip-ai         # Без AI анализа
"""
import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.parser.crawler import Crawler
from app.parser.scraper import Scraper
from bs4 import BeautifulSoup
from app.parser.url_discovery import URLDiscovery
from app.downloader.image_downloader import ImageDownloader
from app.downloader.storage import StorageManager
from app.analyzer.description_generator import DescriptionGenerator
from app.analyzer.embedding_generator import EmbeddingGenerator
from app.pipeline.validator import DataValidator
from app.pipeline.deduplicator import Deduplicator
from app.pipeline.exporter import Exporter
from estet_shared.database import Database
from estet_shared.ai_clients.gemini_client import GeminiClient

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def _parse_product(
    crawler, scraper, product_url, url_discovery,
    validator, exporter, db, embedding_gen,
    description_gen, skip_images, skip_ai, stats, storage
):
    """Парсинг одного продукта"""
    try:
        product_html = crawler.get_page(product_url)
        product_data = scraper.parse_product_page(product_html)
        product_data["product_url"] = product_url
        product_data["slug"] = product_url.rstrip("/").split("/")[-1]

        # Скачивание изображений
        if not skip_images and product_data.get("image_urls"):
            downloader = ImageDownloader()
            results = await downloader.download_images(
                product_data["image_urls"],
                subdir="products"
            )
            downloaded = [p for p in results.values() if p]
            stats["images_downloaded"] += len(downloaded)

            if downloaded:
                product_data["main_image_url"] = downloaded[0]

        # AI анализ
        if not skip_ai:
            ai_description = await description_gen.generate_from_text(product_data)
            if ai_description:
                product_data["ai_semantic_description"] = ai_description.get(
                    "full_description", ""
                )
                stats["ai_descriptions_generated"] += 1

        # Валидация и экспорт
        validation_result = validator.validate_product(product_data)
        if validation_result[0]:
            cleaned = validator.clean_product(product_data)
            async with db.session() as session:
                product = await exporter.export_product(session, cleaned)
                await session.commit()

                # Генерация embedding
                if not skip_ai and product:
                    embedding = await embedding_gen.generate_for_product(cleaned)
                    async with db.session() as emb_session:
                        await exporter.export_embedding(
                            emb_session, product.id, embedding
                        )
                        await emb_session.commit()

            stats["products_processed"] += 1
            url_discovery.mark_visited(product_url)

    except Exception as e:
        logger.error(f"❌ Ошибка парсинга продукта {product_url}: {e}")
        stats["errors"] += 1


async def run_full_parse(skip_images: bool = False, skip_ai: bool = False):
    """
    Запустить полный парсинг каталога.

    Args:
        skip_images: Пропустить скачивание изображений
        skip_ai: Пропустить AI анализ
    """
    logger.info("🚀 Запуск полного парсинга каталога ESTET")
    start_time = datetime.utcnow()

    # Инициализация компонентов
    storage = StorageManager()
    storage.initialize()

    db = Database(settings.DATABASE_URL)
    await db.create_tables()

    gemini = GeminiClient(
        api_key=settings.POLZA_API_KEY,
        api_url=settings.POLZA_API_URL,
        model=settings.GEMINI_MODEL,
    )

    description_gen = DescriptionGenerator(gemini)
    embedding_gen = EmbeddingGenerator(gemini)
    validator = DataValidator()
    deduplicator = Deduplicator()
    exporter = Exporter(db)

    stats = {
        "collections_found": 0,
        "products_found": 0,
        "products_processed": 0,
        "images_downloaded": 0,
        "ai_descriptions_generated": 0,
        "embeddings_generated": 0,
        "errors": 0,
    }

    try:
        # 1. Обход каталога
        logger.info("📂 Шаг 1: Обход каталога...")
        url_discovery = URLDiscovery(settings.ESTET_BASE_URL)

        with Crawler(headless=settings.PARSER_HEADLESS_BROWSER) as crawler:
            # Получаем все категории
            collection_urls = crawler.get_catalog_urls()
            stats["collections_found"] = len(collection_urls)
            logger.info(f"📂 Найдено {len(collection_urls)} коллекций")

            # Для каждой коллекции
            for collection_url in collection_urls:
                logger.info(f"🔍 Парсинг коллекции: {collection_url}")

                try:
                    html = crawler.get_page(collection_url)
                    storage.save_html(html, f"collection_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.html")

                    scraper = Scraper()
                    # parse_collection_page теперь возвращает URL моделей/продуктов
                    model_urls = scraper.parse_collection_page(html)
                    url_discovery.mark_visited(collection_url)

                    if not model_urls:
                        logger.warning(f"⚠️ Не найдено моделей в {collection_url}")
                        continue

                    logger.info(f"📦 Найдено {len(model_urls)} моделей/продуктов в {collection_url}")

                    # Каждый URL модели может содержать конкретные продукты
                    for model_url in model_urls:
                        if url_discovery.is_visited(model_url):
                            continue

                        # Если URL содержит достаточно сегментов — это уже продукт
                        path_parts = [p for p in model_url.split("/") if p]
                        catalog_idx = path_parts.index("catalog") if "catalog" in path_parts else -1

                        if catalog_idx >= 0 and len(path_parts) - catalog_idx >= 4:
                            # Это URL конкретного продукта: /catalog/category/model/product/
                            logger.info(f"📦 Парсинг продукта: {model_url}")
                            await _parse_product(
                                crawler, scraper, model_url, url_discovery,
                                validator, exporter, db, embedding_gen,
                                description_gen, skip_images, skip_ai, stats, storage
                            )
                        else:
                            # Это страница модели — парсим как страницу продукта
                            logger.info(f"🔍 Парсинг модели: {model_url}")
                            await _parse_product(
                                crawler, scraper, model_url, url_discovery,
                                validator, exporter, db, embedding_gen,
                                description_gen, skip_images, skip_ai, stats, storage
                            )

                except Exception as e:
                    logger.error(f"❌ Ошибка парсинга коллекции {collection_url}: {e}")
                    stats["errors"] += 1
                    continue

        # Итоговая статистика
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info("=" * 50)
        logger.info("✅ Парсинг завершен!")
        logger.info(f"⏱️ Время: {elapsed:.2f} секунд")
        logger.info(f"📊 Статистика: {stats}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка парсинга: {e}")
        stats["errors"] += 1
    finally:
        await db.close()


async def run_single_collection(url: str, skip_images: bool = False, skip_ai: bool = False):
    """Парсинг одной коллекции"""
    logger.info(f"🚀 Запуск парсинга коллекции: {url}")

    with Crawler(headless=settings.PARSER_HEADLESS_BROWSER) as crawler:
        html = crawler.get_page(url)
        scraper = Scraper()
        product_urls = scraper.parse_collection_page(html)

        logger.info(f"📦 Найдено {len(product_urls)} продуктов")

        for product_url in product_urls:
            logger.info(f"🔍 Парсинг: {product_url}")
            # ... та же логика что и в full_parse

    logger.info("✅ Парсинг коллекции завершен")


async def run_single_product(url: str, skip_ai: bool = False):
    """Парсинг одного продукта"""
    logger.info(f"🚀 Запуск парсинга продукта: {url}")

    with Crawler(headless=settings.PARSER_HEADLESS_BROWSER) as crawler:
        html = crawler.get_page(url)
        scraper = Scraper()
        product_data = scraper.parse_product_page(html)
        product_data["product_url"] = url

        if not skip_ai:
            gemini = GeminiClient(api_key=settings.POLZA_API_KEY)
            description_gen = DescriptionGenerator(gemini)
            ai_description = await description_gen.generate_from_text(product_data)
            if ai_description:
                product_data["ai_semantic_description"] = ai_description.get("full_description", "")

        logger.info(f"📦 Продукт: {product_data}")

    logger.info("✅ Парсинг продукта завершен")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="ESTET Parser - парсинг каталога")
    parser.add_argument("--collection", type=str, help="URL коллекции для парсинга")
    parser.add_argument("--product", type=str, help="URL продукта для парсинга")
    parser.add_argument("--skip-images", action="store_true", help="Пропустить скачивание изображений")
    parser.add_argument("--skip-ai", action="store_true", help="Пропустить AI анализ")
    parser.add_argument("--full", action="store_true", help="Полный парсинг каталога")

    args = parser.parse_args()

    if args.full or (not args.collection and not args.product):
        asyncio.run(run_full_parse(skip_images=args.skip_images, skip_ai=args.skip_ai))
    elif args.collection:
        asyncio.run(run_single_collection(args.collection, skip_images=args.skip_images, skip_ai=args.skip_ai))
    elif args.product:
        asyncio.run(run_single_product(args.product, skip_ai=args.skip_ai))


if __name__ == "__main__":
    main()
