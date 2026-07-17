# -*- coding: utf-8 -*-
"""
Redis 客户端封装
"""
import json
from typing import Any, Optional
import redis
from app.config.settings import settings
from app.core.logger import get_logger

logger = get_logger("redis")


class RedisClient:
    def __init__(self):
        self._client = None
        self._connect()

    def _connect(self):
        try:
            self._client = redis.from_url(
                settings.REDIS_URL, decode_responses=True,
                socket_connect_timeout=5, socket_timeout=5, retry_on_timeout=True,
            )
            self._client.ping()
            logger.info(f"Redis 连接成功: {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            self._client = None

    @property
    def client(self) -> Optional[redis.Redis]:
        if self._client is None:
            self._connect()
        return self._client

    def is_connected(self) -> bool:
        try:
            if self._client:
                self._client.ping()
                return True
        except Exception:
            pass
        return False

    def get(self, key: str) -> Optional[str]:
        try:
            if self.client:
                return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET 失败: {key}, {e}")
        return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        try:
            if self.client:
                self.client.set(key, value, ex=ex)
                return True
        except Exception as e:
            logger.error(f"Redis SET 失败: {key}, {e}")
        return False

    def delete(self, key: str) -> bool:
        try:
            if self.client:
                self.client.delete(key)
                return True
        except Exception as e:
            logger.error(f"Redis DELETE 失败: {key}, {e}")
        return False

    def get_json(self, key: str) -> Optional[Any]:
        data = self.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"Redis JSON 解析失败: {key}, {e}")
        return None

    def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        try:
            return self.set(key, json.dumps(value, ensure_ascii=False), ex=ex)
        except Exception as e:
            logger.error(f"Redis JSON 序列化失败: {key}, {e}")
            return False


redis_client = RedisClient()