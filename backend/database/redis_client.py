"""Redis 客户端：prod 模式连接 Redis 服务器，dev 模式使用内存模拟。"""

import redis.asyncio as redis

from backend.config import get_settings


def get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.from_url(settings.redis_url, decode_responses=True)
