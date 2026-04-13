"""
API middleware.
"""
import logging
import time

from fastapi import Request, Response

logger = logging.getLogger(__name__)


async def log_requests_middleware(request: Request, call_next):
    """Middleware для логирования запросов"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )

    return response
