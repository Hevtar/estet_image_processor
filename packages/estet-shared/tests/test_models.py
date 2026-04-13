"""
Тесты для Shared Package.
"""
import pytest
from estet_shared.models.product import ProductCreate, ProductResponse
from estet_shared.utils.validators import validate_url, validate_image_size


class TestValidators:
    """Тесты валидаторов"""

    def test_valid_url(self):
        assert validate_url("https://example.com") is True
        assert validate_url("http://localhost:8000") is True
        assert validate_url("https://moscow.estetdveri.ru/doors") is True

    def test_invalid_url(self):
        assert validate_url("not_a_url") is False
        assert validate_url("") is False
        assert validate_url(None) is False

    def test_image_size_valid(self):
        assert validate_image_size(1024 * 1024 * 5) is True  # 5MB
        assert validate_image_size(1024 * 1024 * 10) is True  # 10MB

    def test_image_size_invalid(self):
        assert validate_image_size(1024 * 1024 * 15) is False  # 15MB


class TestProductModels:
    """Тесты моделей продуктов"""

    def test_product_create(self):
        product = ProductCreate(
            name="Тестовая дверь",
            category="Двери межкомнатные",
            product_url="https://example.com/door",
            slug="test-door"
        )
        assert product.name == "Тестовая дверь"
        assert product.category == "Двери межкомнатные"
