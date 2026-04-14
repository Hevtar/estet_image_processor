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
        """Извлекает описание — .product-description__info"""
        desc = soup.select_one(".product-description__info")
        if desc:
            # Получаем текст без лишних пробелов
            text = desc.get_text(separator=" ", strip=True)
            # Убираем повторяющиеся пробелы
            import re
            text = re.sub(r"\s+", " ", text)
            return text[:2000]  # Ограничиваем длину
        return ""

    def _extract_image_urls(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает URL изображений — .product-detail-slider_big img"""
        image_urls = []
        images = soup.select(".product-detail-slider_big .swiper-slide picture img")
        if not images:
            images = soup.select(".product-detail-slider_big img")
        if not images:
            images = soup.select(".product-detail-slider img")
        if not images:
            # Fallback: все img с admin.estetdveri.ru
            images = soup.select('img[src*="admin.estetdveri.ru"]')

        for img in images:
            src = img.get("src") or img.get("data-src")
            if src:
                from urllib.parse import urljoin
                image_urls.append(urljoin(self.base_url, src))

        logger.info(f"🖼️ Найдено {len(image_urls)} изображений")
        return image_urls

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
        """Извлекает особенности из свойств"""
        features = []
        for prop_block in soup.select(".property"):
            name_elem = prop_block.select_one(".property-name")
            if name_elem:
                name = name_elem.get_text(strip=True)
                # Собираем все возможные значения
                items = prop_block.select(".property-items > *")
                for item in items:
                    val = item.get_text(strip=True)
                    if val and val not in features:
                        features.append(f"{name}: {val}")
        return features[:10]  # Ограничиваем
