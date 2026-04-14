# ТЕХНИЧЕСКОЕ ЗАДАНИЕ ДЛЯ QWEN CODE АГЕНТА

## Проект: Исправление парсера Estet Platform

---

## КОНТЕКСТ И ЦЕЛЬ

Парсер межкомнатных дверей сайта `moscow.estetdveri.ru` работает неверно. При запуске на странице коллекции MIO (`/catalog/mezhkomnatnye-dveri/mio/`) он:
- Парсит лишние страницы (другие коллекции, зеркала)
- Не заполняет таблицу `collections`
- Не передаёт `collection_id` продуктам
- Скачивает 141 изображение вместо ~18-24
- Получает пустой `original_description`
- Вызывает AI без данных

---

## ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ

```
services/parser/app/
├── parser/
│   ├── crawler.py        ← ИЗМЕНИТЬ
│   └── scraper.py        ← ИЗМЕНИТЬ
├── pipeline/
│   └── exporter.py       ← ИЗМЕНИТЬ
└── scripts/
    └── run_parser.py     ← ИЗМЕНИТЬ (основной оркестратор)
```

---

## ЗАДАЧА 1: `crawler.py` — Фильтрация URL

### Проблема
Метод `get_product_urls_from_catalog` возвращает ВСЕ ссылки страницы включая навигацию, футер, блоки "Похожие коллекции". Для MIO вернул 11 URL вместо 6.

### Что исправить

**Заменить метод `get_product_urls_from_catalog` целиком:**

```python
def get_product_urls_from_catalog(self, catalog_url: str) -> List[str]:
    """
    Получить URL ТОЛЬКО моделей текущей коллекции.
    
    Правило фильтрации:
    - URL коллекции: /catalog/mezhkomnatnye-dveri/mio/
    - URL модели:    /catalog/mezhkomnatnye-dveri/mio/mio-1/  ← берём
    - URL другой:    /catalog/mezhkomnatnye-dveri/novella/    ← пропускаем
    - URL раздела:   /catalog/mezhkomnatnye-dveri/collections/ ← пропускаем
    """
    from urllib.parse import urlparse
    
    html = self.get_page(catalog_url)
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    
    # Нормализуем путь коллекции для сравнения
    # Например: "/catalog/mezhkomnatnye-dveri/mio"
    collection_path = urlparse(catalog_url).path.rstrip("/")
    
    product_urls = []
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        
        # Работаем только с относительными и абсолютными путями сайта
        parsed = urlparse(href)
        
        # Если абсолютный URL — берём только path
        if parsed.netloc and parsed.netloc not in catalog_url:
            continue  # Внешняя ссылка — пропускаем
        
        path = parsed.path.rstrip("/")
        
        # КЛЮЧЕВОЕ ПРАВИЛО:
        # Путь модели должен начинаться с пути коллекции
        # И быть ровно на ОДИН уровень глубже
        # /catalog/mezhkomnatnye-dveri/mio/mio-1 → remaining = "mio-1" → "/" не содержит → OK
        # /catalog/mezhkomnatnye-dveri/novella   → не начинается с /mio/ → пропуск
        if not path.startswith(collection_path + "/"):
            continue
        
        remaining = path[len(collection_path):].strip("/")
        
        # Ровно один сегмент без вложений
        if "/" in remaining or not remaining:
            continue
        
        full_url = urljoin(self.base_url, path + "/")
        
        if full_url not in product_urls:
            product_urls.append(full_url)
            logger.debug(f"✅ Модель добавлена: {full_url}")
    
    logger.info(
        f"🔗 Найдено {len(product_urls)} моделей коллекции "
        f"(путь коллекции: {collection_path})"
    )
    return product_urls
```

---

## ЗАДАЧА 2: `scraper.py` — Извлечение данных

### Проблема A: `original_description` всегда пустой

Метод `_extract_description` использует селектор `.product-description__info`. Возможно этот класс неверный. Нужно добавить несколько fallback-селекторов.

**Заменить метод `_extract_description`:**

```python
def _extract_description(self, soup: BeautifulSoup) -> str:
    """
    Извлекает описание продукта.
    Пробует несколько селекторов характерных для Nuxt.js SPA.
    """
    selectors = [
        ".product-description__info",
        ".product-description__text", 
        ".product-detail__description",
        ".product-about__text",
        ".collection-description",
        "[itemprop='description']",
        ".product-text",
        ".about-product",
    ]
    
    for selector in selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 30:  # Минимум 30 символов — не пустышка
                logger.debug(f"✅ Описание найдено через селектор: {selector}")
                return text[:3000]
    
    # Fallback: ищем параграфы внутри main контента
    main = soup.select_one("main, .page-content, #__nuxt")
    if main:
        paragraphs = main.select("p")
        texts = []
        for p in paragraphs:
            t = p.get_text(strip=True)
            # Берём только содержательные параграфы (не навигация, не кнопки)
            if len(t) > 50:
                texts.append(t)
        if texts:
            return " ".join(texts[:3])[:3000]
    
    logger.warning("⚠️ Описание продукта не найдено ни одним селектором")
    return ""
```

### Проблема B: Лишние изображения (141 вместо ~18-24)

**Заменить метод `_extract_image_urls`:**

```python
def _extract_image_urls(self, soup: BeautifulSoup) -> List[str]:
    """
    Извлекает ТОЛЬКО изображения текущего продукта.
    
    Исключает:
    - SVG иконки
    - Изображения из блоков "Похожие коллекции"
    - Баннеры акций
    - Иконки особенностей (маленькие картинки)
    - Дубликаты
    """
    image_urls = []
    
    # Приоритетные селекторы — только галерея продукта
    primary_selectors = [
        ".product-detail-slider_big .swiper-slide picture img",
        ".product-detail-slider_big .swiper-slide img",
        ".product-detail-slider_big img",
        ".product-slider__main img",
        ".product-gallery img",
    ]
    
    for selector in primary_selectors:
        images = soup.select(selector)
        if images:
            logger.debug(f"✅ Изображения найдены через: {selector} ({len(images)} шт)")
            for img in images:
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if src and self._is_valid_product_image(src):
                    full_url = urljoin(self.base_url, src)
                    if full_url not in image_urls:
                        image_urls.append(full_url)
            break  # Нашли основную галерею — дальше не ищем
    
    # Fallback только если основные селекторы дали 0 результатов
    if not image_urls:
        logger.warning("⚠️ Основные селекторы галереи не дали результатов, используем fallback")
        # Ищем только на admin.estetdveri.ru — это изображения контента
        for img in soup.select('img[src*="admin.estetdveri.ru"]'):
            src = img.get("src") or img.get("data-src")
            if src and self._is_valid_product_image(src):
                full_url = urljoin(self.base_url, src)
                if full_url not in image_urls:
                    image_urls.append(full_url)
    
    logger.info(f"🖼️ Найдено {len(image_urls)} изображений продукта")
    return image_urls

def _is_valid_product_image(self, url: str) -> bool:
    """
    Проверяет что URL — это реальное изображение продукта.
    
    Returns:
        bool: True если изображение валидно
    """
    if not url:
        return False
    
    # Исключаем SVG (иконки)
    if url.lower().endswith(".svg"):
        return False
    
    # Исключаем data:image (base64 inline)
    if url.startswith("data:"):
        return False
    
    # Исключаем иконки маленького размера по паттернам в URL
    small_size_patterns = ["_80_80", "_40_40", "_24_24", "_32_32", "_16_16"]
    if any(p in url for p in small_size_patterns):
        return False
    
    # Оставляем только реальные форматы изображений
    valid_extensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
    url_lower = url.lower().split("?")[0]  # Убираем query params
    if not any(url_lower.endswith(ext) for ext in valid_extensions):
        # Если нет расширения — пропускаем
        return False
    
    return True
```

### Проблема C: Добавить метод `parse_collection_info`

Этого метода не существует в `scraper.py`, но он нужен в `run_parser.py`:

```python
def parse_collection_info(self, html: str) -> Dict:
    """
    Извлекает информацию о КОЛЛЕКЦИИ со страницы коллекции.
    (Не о модели, а о всей коллекции — название, описание, особенности)
    
    Returns:
        Dict: {
            "name": str,
            "slug": str, 
            "description": str,
            "features": List[str],
            "main_image_url": str
        }
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Название коллекции из h1
    name = ""
    h1 = soup.select_one("h1[itemprop='name'], h1")
    if h1:
        name = h1.get_text(strip=True)
    
    # Slug из названия
    slug = self._name_to_slug(name)
    
    # Описание коллекции — несколько вариантов селекторов
    description = ""
    desc_selectors = [
        ".collection-description__text",
        ".collection-about__text",
        ".first-collection__text",
        ".collection__description",
        ".collection-info__text",
        ".about-collection",
    ]
    for sel in desc_selectors:
        elem = soup.select_one(sel)
        if elem:
            text = elem.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) > 20:
                description = text[:3000]
                break
    
    # Особенности коллекции
    features = []
    feature_selectors = [
        ".collection-features__item",
        ".features-list__item",
        ".collection-advantages__item",
        ".advantages__item",
    ]
    for sel in feature_selectors:
        items = soup.select(sel)
        if items:
            for item in items:
                text = item.get_text(strip=True)
                if text and text not in features:
                    features.append(text)
            break
    
    # Главное изображение коллекции
    main_image_url = ""
    img_selectors = [
        ".collection-hero img",
        ".collection-banner img",
        ".first-collection img",
        ".collection__image img",
    ]
    for sel in img_selectors:
        img = soup.select_one(sel)
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                main_image_url = urljoin(self.base_url, src)
                break
    
    logger.info(
        f"📚 Спаршена коллекция: '{name}', "
        f"описание: {len(description)} симв., "
        f"особенности: {len(features)} шт."
    )
    
    return {
        "name": name,
        "slug": slug,
        "description": description,
        "features": features,
        "main_image_url": main_image_url,
    }

def _name_to_slug(self, name: str) -> str:
    """Конвертирует название в URL-slug"""
    # Транслитерация кириллицы
    translit_map = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo',
        'ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m',
        'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
        'ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
        'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',
    }
    slug = name.lower()
    result = ""
    for char in slug:
        result += translit_map.get(char, char)
    
    result = re.sub(r"[^\w\s-]", "", result)
    result = re.sub(r"[\s_]+", "-", result)
    result = result.strip("-")
    return result
```

### Проблема D: `special_features` содержит размеры

Метод `_extract_special_features` собирает ВСЕ свойства включая размеры. Нужно разделить.

**Заменить метод `_extract_special_features`:**

```python
def _extract_special_features(self, soup: BeautifulSoup) -> List[str]:
    """
    Извлекает ТОЛЬКО особенности продукта.
    НЕ включает размеры (высота/ширина/толщина) — они в available_sizes.
    """
    features = []
    
    # Размерные свойства — исключаем
    size_keywords = ["высота", "ширина", "толщина", "глубина", "длина", "размер"]
    
    for prop_block in soup.select(".property"):
        name_elem = prop_block.select_one(".property-name")
        if not name_elem:
            continue
        
        name = name_elem.get_text(strip=True).lower()
        
        # Пропускаем размерные свойства
        if any(kw in name for kw in size_keywords):
            continue
        
        items = prop_block.select(".property-items > *, .property-item span")
        for item in items:
            val = item.get_text(strip=True)
            if val:
                feature_text = f"{name_elem.get_text(strip=True)}: {val}"
                if feature_text not in features:
                    features.append(feature_text)
    
    # Дополнительно — блок особенностей коллекции на странице продукта
    collection_features = soup.select(".product-features__item, .door-features__item")
    for item in collection_features:
        text = item.get_text(strip=True)
        if text and text not in features:
            features.append(text)
    
    return features[:15]
```

---

## ЗАДАЧА 3: `exporter.py` — Исправление сигнатуры `export_collection`

### Проблема
Метод `export_collection` принимает отдельные параметры (`name`, `slug`, `description`...), но в `run_parser.py` планируется передавать словарь `collection_data`. Нужно унифицировать.

**Заменить метод `export_collection`:**

```python
async def export_collection(
    self,
    session: AsyncSession,
    collection_data: Dict,
) -> Collection:
    """
    Экспортировать коллекцию.

    Args:
        session: DB сессия
        collection_data: Словарь с данными коллекции:
            {
                "name": str,
                "slug": str,
                "description": str,
                "url": str,
                "image_url": str,
                "features": List[str]  (опционально)
            }

    Returns:
        Collection: Созданная или найденная коллекция
    """
    slug = collection_data.get("slug") or self._generate_slug(
        collection_data.get("name", "")
    )
    
    if not slug:
        raise ValueError("Невозможно создать коллекцию без slug/name")

    # Проверяем существование
    result = await session.execute(
        select(Collection).where(Collection.slug == slug)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Обновляем описание если появилось новое
        if collection_data.get("description") and not existing.description:
            existing.description = collection_data["description"]
            logger.info(f"♻️ Обновлено описание коллекции: {slug}")
        else:
            logger.info(f"♻️ Коллекция уже существует: {slug}")
        return existing

    # Создаем новую
    collection = Collection(
        name=collection_data.get("name", ""),
        slug=slug,
        description=collection_data.get("description", ""),
        url=collection_data.get("url", ""),
        image_url=collection_data.get("image_url", ""),
    )
    session.add(collection)
    await session.flush()

    logger.info(f"✅ Создана коллекция: {collection_data.get('name')}")
    return collection
```

**Добавить метод `export_product_images` (пакетное сохранение изображений):**

```python
async def export_product_images(
    self,
    session: AsyncSession,
    product_id: UUID,
    image_paths: List[str],
    image_urls: Optional[List[str]] = None,
) -> List[ProductImage]:
    """
    Пакетное сохранение изображений продукта.

    Args:
        session: DB сессия
        product_id: ID продукта
        image_paths: Локальные пути к файлам
        image_urls: Оригинальные URL (опционально)

    Returns:
        List[ProductImage]: Список созданных записей
    """
    saved = []
    
    for i, local_path in enumerate(image_paths):
        image_data = {
            "local_path": local_path,
            "url": image_urls[i] if image_urls and i < len(image_urls) else "",
            "is_primary": (i == 0),  # Первое изображение — главное
            "order": i,
        }
        
        try:
            img = await self.export_product_image(session, product_id, image_data)
            saved.append(img)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось сохранить изображение {local_path}: {e}")
    
    logger.info(f"🖼️ Сохранено {len(saved)} изображений для продукта {product_id}")
    return saved
```

---

## ЗАДАЧА 4: `run_parser.py` — Оркестратор (главное исправление)

### Полная замена функции `run_single_collection`:

```python
async def run_single_collection(
    url: str,
    skip_images: bool = False,
    skip_ai: bool = False
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
    from urllib.parse import urlparse
    
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
        base_url=settings.POLZA_API_URL,
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
            # Crawler уже применяет фильтрацию по collection_path
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
        product_data["collection_id"] = str(collection_id)
        
        # Маппинг поля description → original_description
        if "description" in product_data and "original_description" not in product_data:
            product_data["original_description"] = product_data.pop("description")
        
        logger.info(
            f"   Название: {product_data.get('name')}, "
            f"   Описание: {len(product_data.get('original_description', ''))} символов, "
            f"   Изображений в HTML: {len(product_data.get('image_urls', []))}"
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
                        image_bytes = storage.read_file(downloaded_paths[0])
                        if image_bytes:
                            ai_result = await description_gen.generate_from_image(
                                image_bytes=image_bytes,
                                product_data=product_data,
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
                        logger.info(f"   ✨ AI описание сгенерировано")
                
                except Exception as ai_err:
                    logger.warning(f"   ⚠️ Ошибка AI генерации: {ai_err}")
            else:
                logger.warning(
                    Продолжаю с места где оборвалось:

```python
                logger.warning(
                    f"   ⚠️ Нет данных для AI анализа продукта {product_url}. "
                    f"Пропускаем генерацию (нет ни описания, ни изображения)."
                )

        # ── 4. Валидация ──────────────────────────────────────
        is_valid, validation_errors = validator.validate_product(product_data)
        
        if not is_valid:
            logger.warning(
                f"   ⚠️ Продукт не прошёл валидацию: {product_url}\n"
                f"   Причины: {validation_errors}"
            )
            stats["errors"] += 1
            return

        cleaned_data = validator.clean_product(product_data)

        # ── 5. Сохранение в БД ───────────────────────────────
        async with db.session() as session:
            
            # 5.1 Сохраняем продукт
            product = await exporter.export_product(
                session=session,
                product_data=cleaned_data,
                collection_id=collection_id,
            )
            await session.flush()
            
            # 5.2 Сохраняем изображения в product_images
            if downloaded_paths:
                # Составляем соответствие path → original_url
                url_path_pairs = list(results.items())
                original_urls = [u for u, p in url_path_pairs if p]
                
                await exporter.export_product_images(
                    session=session,
                    product_id=product.id,
                    image_paths=downloaded_paths,
                    image_urls=original_urls,
                )
            
            await session.commit()
            logger.info(f"   💾 Продукт сохранён в БД (id={product.id})")

        # ── 6. Генерация embedding ────────────────────────────
        if not skip_ai:
            try:
                embedding = await embedding_gen.generate_for_product(cleaned_data)
                
                async with db.session() as emb_session:
                    await exporter.export_embedding(
                        session=emb_session,
                        product_id=product.id,
                        embedding=embedding,
                    )
                    await emb_session.commit()
                
                stats["embeddings_generated"] += 1
                logger.info(f"   🧮 Embedding сохранён")
            
            except Exception as emb_err:
                logger.warning(f"   ⚠️ Ошибка генерации embedding: {emb_err}")

        # ── 7. Отмечаем URL как обработанный ─────────────────
        url_discovery.mark_visited(product_url)
        stats["products_processed"] += 1
        logger.info(f"   ✅ Модель успешно обработана: {product_data.get('name')}")

    except Exception as e:
        logger.error(
            f"❌ Ошибка парсинга модели {product_url}: {e}",
            exc_info=True
        )
        stats["errors"] += 1
```

---

## ЗАДАЧА 5: БД — исправление размерности embedding

```sql
-- Выполнить в psql или через миграцию Alembic

-- 1. Удаляем старый индекс
DROP INDEX IF EXISTS idx_product_embeddings_vector;

-- 2. Меняем размерность вектора с 768 на 3072
--    (Gemini text-embedding-004 возвращает 3072 измерения)
ALTER TABLE product_embeddings
    ALTER COLUMN embedding TYPE vector(3072);

-- 3. Создаём новый индекс под правильную размерность
CREATE INDEX idx_product_embeddings_vector
    ON product_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

Если используется Alembic — добавить миграцию:

```python
# migrations/versions/xxx_fix_embedding_dimensions.py

def upgrade():
    op.execute("DROP INDEX IF EXISTS idx_product_embeddings_vector")
    op.execute(
        "ALTER TABLE product_embeddings "
        "ALTER COLUMN embedding TYPE vector(3072)"
    )
    op.execute(
        "CREATE INDEX idx_product_embeddings_vector "
        "ON product_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )

def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_product_embeddings_vector")
    op.execute(
        "ALTER TABLE product_embeddings "
        "ALTER COLUMN embedding TYPE vector(768)"
    )
    op.execute(
        "CREATE INDEX idx_product_embeddings_vector "
        "ON product_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )
```

---

## ЗАДАЧА 6: Очистка тестовых данных перед повторным запуском

```sql
-- Удаляем некорректные данные из тестового прогона

-- Сначала зависимые таблицы
DELETE FROM product_embeddings;
DELETE FROM product_images;

-- Потом основные
DELETE FROM products;
DELETE FROM collections;

-- Проверяем что всё чисто
SELECT COUNT(*) FROM products;      -- должно быть 0
SELECT COUNT(*) FROM collections;   -- должно быть 0
SELECT COUNT(*) FROM product_images; -- должно быть 0
```

---

## ИТОГОВЫЙ ЧЕКЛИСТ ДЛЯ АГЕНТА

```
Файл: crawler.py
  ✅ Заменить метод get_product_urls_from_catalog
     — фильтрация по collection_path
     — только модели на 1 уровень глубже

Файл: scraper.py
  ✅ Заменить _extract_description
     — множество fallback-селекторов
  ✅ Заменить _extract_image_urls
     — только галерея продукта
     — добавить _is_valid_product_image
  ✅ Заменить _extract_special_features
     — исключить размеры (высота/ширина/толщина)
  ✅ Добавить parse_collection_info
     — название, описание, особенности коллекции
  ✅ Добавить _name_to_slug
     — транслитерация для slug

Файл: exporter.py
  ✅ Заменить export_collection
     — принимает Dict вместо отдельных параметров
  ✅ Добавить export_product_images
     — пакетное сохранение изображений

Файл: run_parser.py
  ✅ Заменить run_single_collection
     — правильный порядок: коллекция → модели
     — передача collection_id в продукты
  ✅ Добавить _parse_single_product
     — атомарная обработка одной модели

БД: PostgreSQL
  ✅ Изменить vector(768) → vector(3072)
  ✅ Пересоздать индекс
  ✅ Очистить тестовые данные
```

---

## ОЖИДАЕМЫЙ РЕЗУЛЬТАТ ПОСЛЕ ИСПРАВЛЕНИЙ

```
При запуске на /catalog/mezhkomnatnye-dveri/mio/:

📊 ИТОГИ ПАРСИНГА:
   Коллекция сохранена: True        ← таблица collections заполнена
   Найдено моделей:     6           ← только MIO, не Novella/Alto/Зеркала
   Обработано моделей:  6           ← все 6 успешно
   Скачано изображений: ~18-24      ← ~3-4 на модель, не 141
   AI описаний:         6           ← для каждой модели
   Embeddings:          6           ← для каждой модели
   Ошибок:              0

Таблица collections:
  1 запись — коллекция MIO с описанием и особенностями

Таблица products:
  6 записей — модели MIO 1, MIO 2, MIO 1 asm...
  collection_id заполнен у всех ← не NULL!
  original_description заполнен ← не пустой!

Таблица product_images:
  ~18-24 записей — изображения моделей

Таблица product_embeddings:
  6 записей — векторы 3072 измерения
```