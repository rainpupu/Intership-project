"""
API 请求日志中间件
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logger import get_logger

logger = get_logger("request")


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        logger.info(f"Request started | Method: {method} | Path: {path} | Client: {client_host}")

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request failed | Method: {method} | Path: {path} | Error: {str(e)}")
            raise

        process_time = (time.time() - start_time) * 1000
        logger.info(f"Request completed | Method: {method} | Path: {path} | Status: {response.status_code} | Duration: {process_time:.2f}ms")
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response