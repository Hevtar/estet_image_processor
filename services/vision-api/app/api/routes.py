"""
API Routes для Vision API.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from ..services.image_analyzer import ImageAnalyzer
from ..services.vector_search import VectorSearch
from ..services.ranking import RankingService
from ..schemas.request import SearchRequest
from ..schemas.response import SearchResponse, ProductResult

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Vision Search"])

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key_header: str = Depends(api_key_header)):
    """Верификация API ключа"""
    from ..config import settings

    if settings.VISION_AUTH_REQUIRED:
        if not api_key_header or api_key_header != settings.VISION_API_KEY:
            raise HTTPException(status_code=403, detail="Invalid API key")
    return True


@router.post("/search", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    max_results: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    style: Optional[str] = Query(None, description="Фильтр по стилю"),
    _: bool = Depends(verify_api_key),
):
    """
    Поиск похожих продуктов по изображению.

    - **file**: Изображение от клиента
    - **max_results**: Максимум результатов
    - **category**: Фильтр по категории (опционально)
    - **style**: Фильтр по стилю (опционально)
    """
    try:
        # Валидация файла
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Файл должен быть изображением")

        # Читаем файл
        image_bytes = await file.read()
        max_size = 10 * 1024 * 1024  # 10MB
        if len(image_bytes) > max_size:
            raise HTTPException(status_code=400, detail=f"Изображение слишком большое (макс. {max_size // 1024 // 1024}MB)")

        # 1. Анализируем изображение через Gemini
        analyzer = ImageAnalyzer()
        analysis = await analyzer.analyze(image_bytes)

        # 2. Ищем похожие продукты в БД
        vector_search = VectorSearch()
        candidates = await vector_search.search(
            query_text=analysis.get("description", ""),
            max_results=max_results * 3,  # Берем с запасом для ранжирования
            category=category,
            style=style,
        )

        # 3. Ранжируем результаты
        ranking = RankingService()
        ranked = ranking.rank(candidates, analysis)

        # Берем top N (ranked — это dict, конвертируем в список)
        top_items = list(ranked.items())[:max_results]

        # Формируем ответ
        results = [
            ProductResult(
                id=product.id,
                name=product.name,
                category=product.category,
                style=product.style,
                color_family=product.color_family,
                ai_semantic_description=product.ai_semantic_description,
                main_image_url=product.main_image_url,
                product_url=product.product_url,
                score=score,
            )
            for product, score in top_items
        ]

        return SearchResponse(
            success=True,
            results=results,
            total=len(results),
            analysis=analysis,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")


@router.post("/search/text", response_model=SearchResponse)
async def search_by_text(
    request: SearchRequest,
    _: bool = Depends(verify_api_key),
):
    """
    Поиск продуктов по текстовому описанию.

    - **query**: Текстовый запрос
    - **max_results**: Максимум результатов
    - **category**: Фильтр по категории
    - **style**: Фильтр по стилю
    """
    try:
        vector_search = VectorSearch()
        candidates = await vector_search.search(
            query_text=request.query,
            max_results=request.max_results,
            category=request.category,
            style=request.style,
        )

        ranking = RankingService()
        ranked = ranking.rank(candidates, {"description": request.query})

        top_items = list(ranked.items())[:request.max_results]

        results = [
            ProductResult(
                id=product.id,
                name=product.name,
                category=product.category,
                style=product.style,
                ai_semantic_description=product.ai_semantic_description,
                main_image_url=product.main_image_url,
                product_url=product.product_url,
                score=score,
            )
            for product, score in top_items
        ]

        return SearchResponse(
            success=True,
            results=results,
            total=len(results),
        )

    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", response_model=ProductResult)
async def get_product(
    product_id: str,
    _: bool = Depends(verify_api_key),
):
    """Получить продукт по ID"""
    try:
        from estet_shared.database import Database
        from estet_shared.models import Product
        from sqlalchemy import select
        from uuid import UUID

        from ..config import settings

        db = Database(settings.DATABASE_URL)
        async with db.session() as session:
            result = await session.execute(select(Product).where(Product.id == UUID(product_id)))
            product = result.scalar_one_or_none()

            if not product:
                raise HTTPException(status_code=404, detail="Продукт не найден")

            return ProductResult(
                id=product.id,
                name=product.name,
                category=product.category,
                style=product.style,
                color_family=product.color_family,
                ai_semantic_description=product.ai_semantic_description,
                main_image_url=product.main_image_url,
                product_url=product.product_url,
                score=1.0,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения продукта: {e}")
        raise HTTPException(status_code=500, detail=str(e))
