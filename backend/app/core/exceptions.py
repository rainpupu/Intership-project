"""
全局异常处理模块
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.logger import get_logger

logger = get_logger("exceptions")


class AppException(Exception):
    def __init__(self, code: int = 500, message: str = "服务器内部错误", detail: str = None):
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)


async def app_exception_handler(request: Request, exc: AppException):
    logger.error(f"AppException: {exc.message} | Path: {request.url.path} | Method: {request.method}")
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "detail": exc.detail},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTPException: {exc.status_code} {exc.detail} | Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail if isinstance(exc.detail, str) else "请求错误"},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "")
        error_messages.append(f"{loc}: {msg}")
    logger.warning(f"ValidationError: {error_messages} | Path: {request.url.path}")
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": "请求参数验证失败", "detail": error_messages},
    )


async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {type(exc).__name__}: {str(exc)} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "detail": str(exc)},
    )