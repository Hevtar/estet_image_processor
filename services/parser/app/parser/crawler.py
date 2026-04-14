"""
Crawler — обход сайта ESTET через Selenium.
"""
import logging
import time
from typing import List, Optional
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from ..config import settings

logger = logging.getLogger(__name__)


class Crawler:
    """Crawler для обхода сайта ESTET"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.base_url = settings.ESTET_BASE_URL

    def _setup_driver(self):
        """Настройка WebDriver"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-agent=Mozilla/5.0 (ESTET Parser Bot {settings.ESTET_BASE_URL})")

        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            # Fallback: пробуем без webdriver-manager
            self.driver = webdriver.Chrome(options=options)

        self.driver.set_page_load_timeout(settings.PARSER_TIMEOUT)
        logger.info("✅ WebDriver инициализирован")

    def start(self):
        """Запустить crawler"""
        if not self.driver:
            self._setup_driver()

    def stop(self):
        """Остановить crawler"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("🛑 WebDriver остановлен")

    def get_page(self, url: str) -> str:
        """
        Получить HTML страницы.

        Args:
            url: URL страницы

        Returns:
            str: HTML контент
        """
        if not self.driver:
            self._setup_driver()

        full_url = urljoin(self.base_url, url)
        logger.info(f"📄 Загрузка: {full_url}")

        try:
            self.driver.get(full_url)
            # Ждем загрузки DOM
            WebDriverWait(self.driver, settings.PARSER_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Для каталога — ждем рендеринга продуктов (JS)
            if "/catalog/" in url:
                # Пробуем ждать появления карточек продуктов
                try:
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "a[href*='/catalog/'][href*='/'], .product-card, .catalog-item, .product-item, .swiper-slide a")
                        )
                    )
                except TimeoutException:
                    logger.warning(f"⏱️ Продукты не отрендерились за 15 сек, продолжаем с текущим HTML")

            # Дополнительная задержка для динамического контента
            time.sleep(settings.PARSER_SCRAPING_DELAY)

            # Скроллим вниз для подгрузки контента
            self._scroll_down()

            return self.driver.page_source

        except TimeoutException:
            logger.error(f"⏱️ Timeout загрузки: {full_url}")
            raise
        except WebDriverException as e:
            logger.error(f"❌ Ошибка WebDriver: {e}")
            raise

    def _scroll_down(self):
        """Прокрутить страницу вниз для подгрузки контента"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(3):  # 3 скролла достаточно
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            # Вернуться наверх
            self.driver.execute_script("window.scrollTo(0, 0);")
        except Exception as e:
            logger.debug(f"Скролл не удался: {e}")

    def get_all_links(self, url: str) -> List[str]:
        """
        Получить все ссылки на странице.

        Args:
            url: URL страницы

        Returns:
            List[str]: Список URL
        """
        html = self.get_page(url)
        links = []

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(self.base_url, href)
            if self.base_url in full_url:
                links.append(full_url)

        logger.info(f"🔗 Найдено {len(links)} ссылок на {url}")
        return links

    def get_catalog_urls(self) -> List[str]:
        """
        Получить URL всех категорий каталога.

        Returns:
            List[str]: URL категорий
        """
        # Используем предопределённые категории из конфига
        categories = getattr(settings, 'ESTET_CATALOG_CATEGORIES', [])
        if categories:
            urls = [self.base_url + cat for cat in categories if not cat.startswith('http')]
            logger.info(f"📂 Найдено {len(urls)} категорий (из конфига)")
            return urls

        # Fallback: парсим страницу каталога
        logger.info("⚠️ ESTET_CATALOG_CATEGORIES не заданы, пытаемся распарсить /catalog")
        html = self.get_page("/catalog")
        urls = []

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Ищем ссылки на категории
        catalog_links = soup.select("a[href*='kategoriya'], a[href*='category'], a[href*='/catalog/']")
        for link in catalog_links:
            href = link.get("href", "")
            if href and self.base_url in href:
                urls.append(href)

        logger.info(f"📂 Найдено {len(urls)} категорий")
        return urls

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
