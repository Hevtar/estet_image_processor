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

                    logger.info(f"📦 Найдено {len(model_urls)} URL на странице {collection_url}")

                    # Каждый URL модели может содержать конкретные продукты
                    for model_url in model_urls:
                        if url_discovery.is_visited(model_url):
                            continue

                        # Определяем тип URL по количеству сегментов после /catalog/
                        path_parts = [p for p in model_url.split("/") if p]
                        try:
                            catalog_idx = path_parts.index("catalog")
                            segments_after_catalog = len(path_parts) - catalog_idx - 1
                        except ValueError:
                            continue

                        # segments_after_catalog:
                        # 2 = /catalog/category/          — раздел каталога (пропускаем)
                        # 3 = /catalog/category/filter/   — фильтр (пропускаем)
                        # 3 = /catalog/category/model/    — коллекция/модель (парсим как продукт)
                        # 4 = /catalog/category/model/id/ — конкретный продукт (парсим)

                        if segments_after_catalog <= 2:
                            logger.debug(f"⏭️ Пропускаем раздел: {model_url}")
                            continue

                        if segments_after_catalog == 3:
                            # Это может быть коллекция или фильтр
                            # Проверяем по названию: фильтры содержат слова-фильтры
                            last_segment = path_parts[-1].lower()
                            filter_keywords = [
                                'temnye', 'svetlye', 'belye', 'serye', 'korichnevye',
                                'chornye', 'bezhennye', 'filter', 'style_', 'glass_',
                                'otkryvaniye', 'type_', 'purpose', 'design_',
                                'collection', 'collections'
                            ]
                            if any(kw in last_segment for kw in filter_keywords):
                                logger.debug(f"⏭️ Пропускаем фильтр: {model_url}")
                                continue

                        # Парсим как продукт
                        logger.info(f"📦 Парсинг: {model_url}")
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


async def run_single_collection(
    url: str,
    skip_images: bool = False,
    skip_ai: bool = False,
):
    """
    Парсинг одной коллекции дверей.

    Правильный порядок:
    1. Загрузить страницу коллекции
    2. Извлечь данные КОЛЛЕКЦИИ и сохранить в таблицу collections
    3. Получить URL только моделей ЭТОЙ коллекции (с фильтрацией)
    4. Для каждой модели: зайти в карточку, спарсить, сохранить
    5. Для каждого продукта: скачать изображения, сгенерировать AI описание, сохранить
    """
    logger.info(f"🚀 Запуск парсинга коллекции: {url}")

    stats = {
        "collection_saved": False,
        "products_found": 0,
        "products_processed": 0,
        "images_downloaded": 0,
        "ai_descriptions_generated": 0,
        "embeddings_generated": 0,
        "errors": 0,
    }

    # Инициализация зависимостей
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
    exporter = Exporter(db)
    storage = StorageManager()
    url_discovery = URLDiscovery(settings.ESTET_BASE_URL)
    scraper = Scraper()

    try:
        with Crawler(headless=settings.PARSER_HEADLESS_BROWSER) as crawler:

            # ══════════════════════════════════════
            # ШАГ 1: Парсим данные КОЛЛЕКЦИИ
            # ══════════════════════════════════════
            logger.info(f"📖 Загрузка страницы коллекции: {url}")
            collection_html = crawler.get_page(url)

            collection_data = scraper.parse_collection_info(collection_html)
            collection_data["url"] = url

            # Сохраняем коллекцию в БД
            async with db.session() as session:
                collection = await exporter.export_collection(session, collection_data)
                await session.commit()
                collection_id = collection.id

            stats["collection_saved"] = True
            logger.info(
                f"✅ Коллекция сохранена: '{collection_data.get('name')}' "
                f"(id={collection_id})"
            )

            # ══════════════════════════════════════
            # ШАГ 2: Получаем URL моделей коллекции
            # ══════════════════════════════════════
            product_urls = crawler.get_product_urls_from_catalog(url)
            stats["products_found"] = len(product_urls)

            logger.info(f"📦 Найдено {len(product_urls)} моделей для парсинга")

            if not product_urls:
                logger.error(
                    f"❌ Не найдено ни одной модели на странице {url}. "
                    f"Проверьте HTML структуру страницы."
                )
                return stats

            # ══════════════════════════════════════
            # ШАГ 3: Парсим каждую модель
            # ══════════════════════════════════════
            for product_url in product_urls:

                if url_discovery.is_visited(product_url):
                    logger.debug(f"⏭️ Уже обработан: {product_url}")
                    continue

                logger.info(f"🔍 Парсинг модели: {product_url}")

                await _parse_single_product(
                    crawler=crawler,
                    scraper=scraper,
                    product_url=product_url,
                    collection_id=collection_id,
                    collection_info=collection_data,
                    url_discovery=url_discovery,
                    validator=validator,
                    exporter=exporter,
                    db=db,
                    embedding_gen=embedding_gen,
                    description_gen=description_gen,
                    skip_images=skip_images,
                    skip_ai=skip_ai,
                    stats=stats,
                    storage=storage,
                )

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        stats["errors"] += 1
    finally:
        await db.close()

    # Итоговая статистика
    logger.info("=" * 60)
    logger.info("📊 ИТОГИ ПАРСИНГА:")
    logger.info(f"   Коллекция сохранена: {stats['collection_saved']}")
    logger.info(f"   Найдено моделей:     {stats['products_found']}")
    logger.info(f"   Обработано моделей:  {stats['products_processed']}")
    logger.info(f"   Скачано изображений: {stats['images_downloaded']}")
    logger.info(f"   AI описаний:         {stats['ai_descriptions_generated']}")
    logger.info(f"   Embeddings:          {stats['embeddings_generated']}")
    logger.info(f"   Ошибок:              {stats['errors']}")
    logger.info("=" * 60)

    return stats


async def _parse_single_product(
    crawler,
    scraper,
    product_url: str,
    collection_id,
    collection_info,
    url_discovery,
    validator,
    exporter,
    db,
    embedding_gen,
    description_gen,
    skip_images: bool,
    skip_ai: bool,
    stats: dict,
    storage,
):
    """
    Парсинг одной карточки модели двери.

    Порядок:
    1. Загрузить HTML карточки модели
    2. Извлечь все данные
    3. Скачать изображения (только продукта)
    4. Сгенерировать AI описание (если есть данные)
    5. Сохранить в products + product_images + embeddings
    """
    try:
        # ── 1. Парсинг HTML карточки ──────────────────────────
        product_html = crawler.get_page(product_url)
        product_data = scraper.parse_product_page(product_html)
        product_data["product_url"] = product_url

        # Маппинг поля description → original_description
        if "description" in product_data and "original_description" not in product_data:
            product_data["original_description"] = product_data.pop("description")

        logger.info(
            f"   Название: {product_data.get('name')}, "
            f"Описание: {len(product_data.get('original_description', ''))} симв., "
            f"Изображений в HTML: {len(product_data.get('image_urls', []))}"
        )

        # ── 2. Скачивание изображений ─────────────────────────
        downloaded_paths = []
        original_image_urls = product_data.get("image_urls", [])

        if not skip_images and original_image_urls:
            downloader = ImageDownloader()
            results = await downloader.download_images(
                original_image_urls,
                subdir="products"
            )
            # results: Dict[url → local_path or None]
            downloaded_paths = [p for p in results.values() if p]
            stats["images_downloaded"] += len(downloaded_paths)

            if downloaded_paths:
                product_data["main_image_url"] = downloaded_paths[0]
                logger.info(f"   📥 Скачано {len(downloaded_paths)} изображений")

        # ── 3. AI генерация описания ──────────────────────────
        if not skip_ai:
            has_text = bool(product_data.get("original_description", "").strip())
            has_image = bool(downloaded_paths)

            if has_text or has_image:
                try:
                    # Предпочитаем анализ изображения если оно есть
                    if has_image:
                        image_bytes = Path(downloaded_paths[0]).read_bytes()
                        if image_bytes:
                            ai_result = await description_gen.generate_from_image(
                                image_bytes=image_bytes,
                                product_data=product_data,
                                collection_info=collection_info,
                            )
                        else:
                            ai_result = await description_gen.generate_from_text(product_data)
                    else:
                        ai_result = await description_gen.generate_from_text(product_data)

                    if ai_result:
                        product_data["ai_semantic_description"] = ai_result.get(
                            "full_description", ""
                        )
                        stats["ai_descriptions_generated"] += 1

                        # Сохраняем стилевой анализ
                        style_analysis = ai_result.get("style_analysis", {})

                        if style_analysis.get("door_style"):
                            # Перезаписываем поле style более точным значением от AI
                            product_data["style"] = style_analysis["door_style"]
                            product_data["door_style_description"] = style_analysis["door_style"]

                        if style_analysis.get("compatible_interior_styles"):
                            compatible = style_analysis["compatible_interior_styles"]
                            product_data["compatible_styles"] = compatible
                            logger.info(
                                f"   🎨 Стиль: {style_analysis.get('door_style', '')[:60]}\n"
                                f"   🏠 Совместимые: {', '.join(compatible[:4])}"
                            )

                        logger.info(f"   ✨ AI описание сгенерировано")

                except Exception as ai_err:
                    logger.warning(f"   ⚠️ Ошибка AI генерации: {ai_err}")
            else:
                logger.warning(
                    f"   ⚠️ Нет данных для AI анализа продукта {product_url}. "
                    f"Пропускаем генерацию (нет ни описания, ни изображения)."
                )

        # ── 4. Валидация ──────────────────────────────────────
        is_valid, errors = validator.validate_product(product_data)

        if not is_valid:
            logger.warning(f"   ❌ Валидация не пройдена: {errors}")
            stats["errors"] += 1
            return

        cleaned = validator.clean_product(product_data)

        # ── 5. Сохранение в БД ────────────────────────────────
        async with db.session() as session:
            product = await exporter.export_product(session, cleaned)
            await session.commit()

            if not product:
                logger.error(f"   ❌ Не удалось сохранить продукт")
                stats["errors"] += 1
                return

            logger.info(f"   ✅ Продукт сохранён: {product.name}")

            # Сохраняем изображения
            if downloaded_paths:
                async with db.session() as img_session:
                    await exporter.export_product_images(
                        img_session,
                        product.id,
                        downloaded_paths,
                        image_urls=original_image_urls[:len(downloaded_paths)],
                    )
                    await img_session.commit()

            # Генерация embedding
            if not skip_ai:
                embedding = await embedding_gen.generate_for_product(cleaned)
                async with db.session() as emb_session:
                    await exporter.export_embedding(
                        emb_session, product.id, embedding
                    )
                    await emb_session.commit()
                stats["embeddings_generated"] += 1

        stats["products_processed"] += 1
        url_discovery.mark_visited(product_url)

    except Exception as e:
        logger.error(f"❌ Ошибка парсинга продукта {product_url}: {e}", exc_info=True)
        stats["errors"] += 1


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
