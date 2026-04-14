"""
Crawler — обход сайта ESTET.
Поддерживает два режима:
1. API-режим — перехват JSON API запросов (рекомендуется для SPA)
2. Selenium — рендеринг через браузер (fallback)
"""
import json
import logging
import time
from typing import Dict, List, Optional
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
        self._api_responses: List[Dict] = []

    def _setup_driver(self):
        """Настройка WebDriver с перехватом network"""
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")  # Новый headless режим
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (ESTET Parser Bot)")

        # Включаем CDP для перехвата network
        options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,  # Отключаем картинки для скорости
        })

        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            self.driver = webdriver.Chrome(options=options)

        # Включаем перехват network через CDP
        self.driver.execute_cdp_cmd("Network.enable", {})
        self.driver.set_page_load_timeout(settings.PARSER_TIMEOUT)
        logger.info("✅ WebDriver инициализирован (CDP network interception enabled)")

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
        Для SPA: ждём рендеринга и скроллим для подгрузки.
        """
        if not self.driver:
            self._setup_driver()

        full_url = urljoin(self.base_url, url)
        logger.info(f"📄 Загрузка: {full_url}")

        try:
            self.driver.get(full_url)

            # Для каталога — ждём рендеринга контента
            if "/catalog/" in url:
                self._wait_for_spa_content()

            time.sleep(settings.PARSER_SCRAPING_DELAY)

            # Скроллим для подгрузки ленивого контента
            self._scroll_down()

            return self.driver.page_source

        except TimeoutException:
            logger.error(f"⏱️ Timeout загрузки: {full_url}")
            raise
        except WebDriverException as e:
            logger.error(f"❌ Ошибка WebDriver: {e}")
            raise

    def _wait_for_spa_content(self):
        """Ждём появления контента, сгенерированного JS"""
        selectors_to_try = [
            # Страница модели/продукта
            "h1[itemprop='name']",
            ".product-top",
            ".price_value",
            # Страница каталога
            ".catalog-page",
            ".first-collection",
            # Общие
            "#__nuxt",
        ]

        for selector in selectors_to_try:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.debug(f"✅ Контент найден: {selector}")
                return
            except TimeoutException:
                continue

        logger.warning("⏱️ Ни один селектор SPA контента не сработал")
        time.sleep(3)  # Fallback — просто ждём

    def _scroll_down(self):
        """Прокрутить страницу вниз для подгрузки контента"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(5):  # 5 скроллов
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    logger.debug(f"Скролл завершён после {i+1} итераций")
                    break
                last_height = new_height
            self.driver.execute_script("window.scrollTo(0, 0);")
        except Exception as e:
            logger.debug(f"Скролл не удался: {e}")

    def get_catalog_urls(self) -> List[str]:
        """
        Получить URL всех категорий каталога.
        """
        categories = getattr(settings, 'ESTET_CATALOG_CATEGORIES', [])
        if categories:
            urls = [self.base_url + cat for cat in categories if not cat.startswith('http')]
            logger.info(f"📂 Найдено {len(urls)} категорий (из конфига)")
            return urls

        logger.info("⚠️ ESTET_CATALOG_CATEGORIES не заданы")
        return []

    def get_product_urls_from_catalog(self, catalog_url: str) -> List[str]:
        """
        Получить все URL продуктов со страницы каталога.
        Ждёт рендеринга SPA и собирает ссылки на модели.
        """
        html = self.get_page(catalog_url)

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        product_urls = []

        # Стратегия: собираем ВСЕ уникальные ссылки, которые похожи на URL модели
        for a in soup.find_all("a", href=True):
            href = a["href"]
            parts = [p for p in href.split("/") if p]
            # /catalog/category/model-name/ — минимум 3 сегмента
            if len(parts) >= 3 and parts[0] == "catalog":
                full_url = urljoin(self.base_url, href)
                if full_url not in product_urls:
                    product_urls.append(full_url)

        logger.info(f"🔗 Найдено {len(product_urls)} URL со страницы {catalog_url}")
        return product_urls

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
