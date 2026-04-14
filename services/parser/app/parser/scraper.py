"""
Scraper — извлечение данных из HTML через BeautifulSoup.
"""
import logging
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from ..config import settings

logger = logging.getLogger(__name__)


class Scraper:
    """Scraper для извлечения данных из HTML"""

    def __init__(self):
        self.base_url = settings.ESTET_BASE_URL

    def parse_product_page(self, html: str) -> Dict:
        """
        Парсит страницу продукта.

        Args:
            html: HTML контент страницы

        Returns:
            Dict: Данные продукта
        """
        soup = BeautifulSoup(html, "html.parser")

        product_data = {
            "name": self._extract_name(soup),
            "category": self._extract_category(soup),
            "style": self._extract_style(soup),
            "color_family": self._extract_color(soup),
            "material": self._extract_material(soup),
            "finish_type": self._extract_finish_type(soup),
            "price": self._extract_price(soup),
            "description": self._extract_description(soup),
            "image_urls": self._extract_image_urls(soup),
            "available_sizes": self._extract_sizes(soup),
            "special_features": self._extract_special_features(soup),
        }

        logger.info(f"📦 Спаршен продукт: {product_data['name']}")
        return product_data

    def parse_collection_page(self, html: str) -> List[str]:
        """
        Парсит страницу коллекции и возвращает ссылки на продукты.

        Сайт Nuxt.js SPA — продукты рендерятся через JS.
        Стратегия: ищем ссылки на модели в хлебных крошках и навигации,
        а также в карточках товаров если они подгрузились.

        Returns:
            List[str]: URL продуктов (моделей)
        """
        soup = BeautifulSoup(html, "html.parser")
        product_urls = []

        # Стратегия 1: Ищем внутренние навигационные ссылки на модели
        # (коллекции/модели в aside internal-navigation)
        nav_links = soup.select("a.internal-navigation__item[href]")
        for link in nav_links:
            href = link.get("href", "")
            # Пропускаем "Все двери" и "Коллекции"
            if href and '/catalog/' in href and 'collections' not in href:
                from urllib.parse import urljoin
                full_url = urljoin(self.base_url, href)
                if full_url not in product_urls:
                    product_urls.append(full_url)

        # Стратегия 2: Ищем ссылки на модели в хлебных крошках
        breadcrumbs = soup.select("ul.breadcrumbs li a[href]")
        for link in breadcrumbs:
            href = link.get("href", "")
            if href and '/catalog/' in href and '/catalog/mezhkomnatnye-dveri/' != href:
                from urllib.parse import urljoin
                full_url = urljoin(self.base_url, href)
                if full_url not in product_urls:
                    product_urls.append(full_url)

        # Стратегия 3: Ищем карточки продуктов (если JS отрендерил)
        product_selectors = [
            "a.product-card__link",
            "a.product-item__link",
            ".product-card a[href]",
            ".product-item a[href]",
            ".catalog-item a[href]",
            ".swiper-slide a[href]",
        ]

        for selector in product_selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get("href", "")
                    if href and '/catalog/' in href:
                        from urllib.parse import urljoin
                        full_url = urljoin(self.base_url, href)
                        if full_url not in product_urls:
                            product_urls.append(full_url)
                break

        # Стратегия 4: Ищем ВСЕ ссылки содержащие /catalog/ и не ведущие на разделы
        if not product_urls:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                # Ищем URL уровня модели: /catalog/category/model/
                parts = [p for p in href.split("/") if p]
                if len(parts) >= 3 and parts[0] == "catalog":
                    from urllib.parse import urljoin
                    full_url = urljoin(self.base_url, href)
                    if full_url not in product_urls:
                        product_urls.append(full_url)

        logger.info(f"🔗 Найдено {len(product_urls)} ссылок на странице коллекции")
        return product_urls

    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Извлекает название продукта — h1[itemprop="name"]"""
        elem = soup.select_one('h1[itemprop="name"]')
        if elem:
            return elem.get_text(strip=True)
        # Fallback
        elem = soup.select_one("h1")
        if elem:
            return elem.get_text(strip=True)
        return "Неизвестный продукт"

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Извлекает категорию из хлебных крошек"""
        crumbs = soup.select("ul.breadcrumbs li a")
        for crumb in crumbs:
            href = crumb.get("href", "")
            if "/catalog/mezhkomnatnye-dveri/" == href:
                return "Двери межкомнатные"
            elif "/catalog/skrytye-dveri/" == href:
                return "Скрытые двери"
            elif "/catalog/vkhodnye-dveri/" == href:
                return "Входные двери"
            elif "/catalog/stenovye-paneli/" == href:
                return "Стеновые панели"
            elif "/catalog/mezhkomnatnye-peregorodki/" == href:
                return "Межкомнатные перегородки"
        return "Другое"

    def _extract_collection(self, soup: BeautifulSoup) -> str:
        """Извлекает коллекцию из ссылки"""
        link = soup.select_one("a.collection_link .collection_name")
        if link:
            return link.get_text(strip=True)
        # Из хлебных крошек
        crumbs = soup.select("ul.breadcrumbs li a")
        for crumb in crumbs:
            href = crumb.get("href", "")
            parts = [p for p in href.split("/") if p]
            if len(parts) == 3 and parts[0] == "catalog":
                # Это уровень коллекции
                return crumb.get_text(strip=True)
        return ""

    def _extract_style(self, soup: BeautifulSoup) -> str:
        """Извлекает стиль из фильтров и описания"""
        text = soup.get_text().lower()

        style_patterns = {
            "минимализм": ["минимализм"],
            "скандинавский": ["скандинавск"],
            "классический": ["классическ"],
            "неоклассический": ["неоклассическ"],
            "современный": ["современн"],
            "дизайнерский": ["дизайнерск"],
            "джапанди": ["джапанди"],
            "бионика": ["бионика"],
            "другое": ["другое"],
        }

        for style, patterns in style_patterns.items():
            if any(p in text for p in patterns):
                return style

        return "unknown"

    def _extract_color(self, soup: BeautifulSoup) -> str:
        """Извлекает цвет из свойств продукта"""
        # Ищем "Цвет:" label
        for prop_block in soup.select(".property"):
            name_elem = prop_block.select_one(".property-name")
            if name_elem and "цвет" in name_elem.get_text(strip=True).lower():
                items = prop_block.select(".filter__item--label, .property-item span")
                if items:
                    return items[0].get_text(strip=True)

        # Fallback из текста
        text = soup.get_text().lower()
        color_map = {
            "белый": ["белый", "white", "ral-9002", "ral 9002"],
            "серый": ["серый", "grey", "ral-7006"],
            "коричневый": ["коричнев", "венге", "орех", "дуб"],
            "бежевый": ["бежевый"],
            "черный": ["черный", "black"],
        }
        for color, patterns in color_map.items():
            if any(p in text for p in patterns):
                return color
        return "unknown"

    def _extract_material(self, soup: BeautifulSoup) -> str:
        """Извлекает материал из свойств"""
        text = soup.get_text().lower()
        materials = {
            "Шпон": ["шпон"],
            "Эмаль": ["эмаль"],
            "Массив": ["массив"],
            "Экошпон": ["экошпон"],
            "МДФ": ["мдф"],
            "Грунт": ["грунт"],
            "Покрытие": ["покрытие"],
        }
        for material, patterns in materials.items():
            if any(p in text for p in patterns):
                return material
        return "Не указан"

    def _extract_finish_type(self, soup: BeautifulSoup) -> str:
        """Извлекает тип отделки из свойств"""
        for prop_block in soup.select(".property"):
            name_elem = prop_block.select_one(".property-name")
            if name_elem and "оформление" in name_elem.get_text(strip=True).lower():
                items = prop_block.select(".property-item span")
                if items:
                    return items[0].get_text(strip=True)

        text = soup.get_text().lower()
        if "эмаль" in text:
            return "эмаль"
        elif "шпон" in text:
            return "шпон"
        return "unknown"

    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Извлекает цену — .price_value"""
        elem = soup.select_one(".price_value")
        if elem:
            text = elem.get_text(strip=True).replace(" ", "")
            try:
                return float(text)
            except ValueError:
                pass
        return None

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """
        Извлекает описание продукта.
        Пробует несколько селекторов характерных для Nuxt.js SPA.
        """
        import re

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

    def _extract_sizes(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает размеры (высота/ширина) из свойств"""
        sizes = []
        for prop_block in soup.select(".property.size"):
            name_elem = prop_block.select_one(".property-name")
            if not name_elem:
                continue
            name = name_elem.get_text(strip=True).lower()
            items = prop_block.select(".property-item span")
            for item in items:
                val = item.get_text(strip=True)
                if val:
                    sizes.append(f"{name}: {val}")
        return sizes

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
                import re
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
                    from urllib.parse import urljoin
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
        import re

        # Транслитерация кириллицы
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        }
        slug = name.lower()
        result = ""
        for char in slug:
            result += translit_map.get(char, char)

        result = re.sub(r"[^\w\s-]", "", result)
        result = re.sub(r"[\s_]+", "-", result)
        result = result.strip("-")
        return result
