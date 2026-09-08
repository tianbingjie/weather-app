import re
import threading
import time
from typing import Any

import requests

from app.config import settings


class WeatherAPIError(RuntimeError):
    pass


class WeatherRateLimitError(WeatherAPIError):
    """上游返回 429。"""


def _sanitize(text: str) -> str:
    """从任何日志/错误文本中抹掉 apikey，避免泄露。"""
    return re.sub(r"apikey=[^&\s]+", "apikey=***", text)


class RateLimiter:
    """全局速率限制器：保证跨线程的请求间隔不小于 1/rate_limit 秒。"""

    def __init__(self, rate_limit: float):
        self._min_interval = 1.0 / rate_limit if rate_limit > 0 else 0.0
        self._next_time = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        if self._min_interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            wait = self._next_time - now
            # 无论是否需要等待，都预留下一次的最早时间点
            self._next_time = max(now, self._next_time) + self._min_interval
        if wait > 0:
            time.sleep(wait)


class WeatherClient:
    def __init__(self):
        self.session = requests.Session()
        self.limiter = RateLimiter(settings.qps_limit)

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not settings.weather_api_key:
            raise WeatherAPIError("WEATHER_API_KEY 未配置")
        self.limiter.acquire()  # 每秒最多 qps_limit 次上游请求
        try:
            response = self.session.get(
                f"{settings.weather_base_url}{path}",
                params={"apikey": settings.weather_api_key, **(params or {})},
                timeout=settings.request_timeout,
            )
            if response.status_code == 429:
                raise WeatherRateLimitError("WeatherCN 请求过于频繁（429 限流）")
            response.raise_for_status()
            return response.json()
        except WeatherRateLimitError:
            raise
        except requests.RequestException as exc:
            raise WeatherAPIError(f"WeatherCN 请求失败: {_sanitize(str(exc))}") from exc
        except ValueError as exc:
            raise WeatherAPIError("WeatherCN 返回了无效 JSON") from exc
