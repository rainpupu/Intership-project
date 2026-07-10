"""
简易速率限制模块

基于内存的滑动窗口速率限制，适用于单进程场景。
"""
import time
import threading
from collections import defaultdict
from fastapi import Request, HTTPException
from app.core.logger import get_logger

logger = get_logger("rate_limit")

# 全局计数器: {key: [(timestamp, ...)] }
_request_log: dict[str, list[float]] = defaultdict(list)
_lock = threading.Lock()
_last_cleanup = time.monotonic()  # 上次全量清理时间
_CLEANUP_INTERVAL = 300  # 每 5 分钟执行一次全量清理


def _cleanup_expired(now: float):
    """清理所有过期的速率限制记录（内部调用，需已持有 _lock）"""
    global _last_cleanup
    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return
    _last_cleanup = now
    expired_keys = []
    for key, timestamps in _request_log.items():
        # 清理该 key 的过期条目
        cutoff = now - 120  # 清理 2 分钟前的记录（大于任何可能的窗口）
        _request_log[key] = [t for t in timestamps if t > cutoff]
        if not _request_log[key]:
            expired_keys.append(key)
    for key in expired_keys:
        del _request_log[key]
    if expired_keys:
        logger.debug(f"速率限制清理: 移除 {len(expired_keys)} 个过期 key")


def reset_rate_limit():
    """重置速率限制状态（供测试用例使用）"""
    global _request_log
    with _lock:
        _request_log.clear()


def check_rate_limit(
    key: str,
    max_requests: int = 5,
    window_seconds: int = 60,
) -> None:
    """
    检查是否超过速率限制

    Args:
        key: 限流键（如 IP + 端点）
        max_requests: 窗口内最大请求数
        window_seconds: 时间窗口（秒）

    Raises:
        HTTPException: 超过限制时抛出 429
    """
    now = time.monotonic()
    cutoff = now - window_seconds

    with _lock:
        # 定期全量清理过期记录，防止内存泄漏
        _cleanup_expired(now)
        # 清理当前 key 的过期记录
        _request_log[key] = [t for t in _request_log[key] if t > cutoff]

        if len(_request_log[key]) >= max_requests:
            logger.warning(f"速率限制触发: key={key}, count={len(_request_log[key])}")
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )

        _request_log[key].append(now)


def rate_limit_dependency(max_requests: int = 5, window_seconds: int = 60):
    """
    返回 FastAPI 依赖函数，用于接口级别的速率限制

    Args:
        max_requests: 窗口内最大请求数
        window_seconds: 时间窗口（秒）
    """
    async def dependency(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"{client_ip}:{path}"
        check_rate_limit(key, max_requests, window_seconds)

    return dependency
