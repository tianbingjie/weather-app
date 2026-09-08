"""缓存与每日配额的单元测试。"""
import time

from app.services.cache_service import DailyQuota, TTLCache
from app.services.weather_client import RateLimiter, _sanitize


def test_cache_fresh_and_stale():
    cache = TTLCache()
    cache.set("k", {"v": 1}, ttl=60)
    value, fresh = cache.get("k")
    assert value == {"v": 1} and fresh is True

    # 过期后应返回 stale 值
    cache.set("k2", {"v": 2}, ttl=0.05)
    time.sleep(0.1)
    value, fresh = cache.get("k2")
    assert value == {"v": 2} and fresh is False

    # 完全没有缓存
    value, fresh = cache.get("missing")
    assert value is None and fresh is False


def test_daily_quota_limit_and_reset():
    quota = DailyQuota(limit=3)
    assert quota.try_acquire() is True
    assert quota.try_acquire() is True
    assert quota.try_acquire() is True
    assert quota.try_acquire() is False  # 超出配额
    assert quota.remaining == 0


def test_daily_quota_unlimited():
    quota = DailyQuota(limit=0)
    for _ in range(100):
        assert quota.try_acquire() is True


def test_sanitize_apikey():
    msg = "429 Client Error for url: https://openapi.weathercn.com/alerts/v1/1.json?apikey=SECRET123&language=zh-cn"
    cleaned = _sanitize(msg)
    assert "SECRET123" not in cleaned
    assert "apikey=***" in cleaned


def test_rate_limiter_spacing():
    # 20 次/秒 -> 最小间隔 0.05s；连发 5 次应至少耗时 0.2s
    limiter = RateLimiter(20)
    start = time.monotonic()
    for _ in range(5):
        limiter.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.18  # 留一点调度误差余量


def test_rate_limiter_unlimited():
    limiter = RateLimiter(0)
    start = time.monotonic()
    for _ in range(100):
        limiter.acquire()
    assert time.monotonic() - start < 0.1
