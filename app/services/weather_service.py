import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.config import settings
from app.services.cache_service import DailyQuota, TTLCache
from app.services.weather_client import WeatherAPIError, WeatherClient, WeatherRateLimitError

logger = logging.getLogger("weather.service")


class WeatherService:
    # 端点名 -> 缓存 TTL（秒）
    TTL = {
        "current": settings.cache_ttl_current,
        "minute": settings.cache_ttl_minute,
        "hourly": settings.cache_ttl_hourly,
        "alerts": settings.cache_ttl_alerts,
        "air": settings.cache_ttl_air,
        "daily": settings.cache_ttl_daily,
        "indices": settings.cache_ttl_indices,
        "search": settings.cache_ttl_search,
        "locate": settings.cache_ttl_locate,
    }

    def __init__(self):
        self.client = WeatherClient()
        self.cache = TTLCache()
        self.quota = DailyQuota(settings.daily_quota)

    # ---------- 缓存 + 配额统一入口 ----------

    def _fetch(self, name: str, path: str, params: dict[str, Any]):
        """带 TTL 缓存与每日配额的上游请求，返回 (data, is_stale)。
        上游速率由 WeatherClient 内的 RateLimiter 全局控制在每秒 qps_limit 次。
        """
        key = path + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        value, fresh = self.cache.get(key)
        if fresh:
            logger.debug("缓存命中: %s", name)
            return value, False

        if not self.quota.try_acquire():
            logger.warning("每日配额已用尽，回退缓存数据: %s", name)
            if value is not None:
                return value, True
            return {"error": "今日 API 调用配额已用完，请明天再试"}, True

        try:
            data = self.client.get(path, params)
        except WeatherRateLimitError:
            if value is not None:
                logger.warning("上游 429，回退缓存数据: %s", name)
                return value, True
            raise
        except WeatherAPIError:
            if value is not None:
                logger.warning("上游请求失败，回退缓存数据: %s", name)
                return value, True
            raise
        self.cache.set(key, data, self.TTL.get(name, 600))
        return data, False

    # ---------- 对外方法 ----------

    def search(self, query: str) -> Any:
        return self._fetch("search", "/locations/v1/cities/translate",
                           {"q": query, "language": "zh-cn", "details": "true"})[0]

    def locate(self, lat: float, lon: float) -> Any:
        return self._fetch("locate", "/locations/v1/cities/geoposition/search.json",
                           {"q": f"{lat},{lon}", "language": "zh-cn"})[0]

    def dashboard(self, location_key: str, lat: float | None = None, lon: float | None = None):
        jobs = {
            "current": (f"/currentconditions/v1/{location_key}.json", {"language": "zh-cn", "details": "true"}),
            "daily": (f"/forecasts/v1/daily/10day/{location_key}.json", {"language": "zh-cn", "details": "true", "metric": "true"}),
            "hourly": (f"/forecasts/v1/hourly/24hour/{location_key}.json", {"language": "zh-cn", "details": "true", "metric": "true"}),
            "alerts": (f"/alerts/v1/{location_key}.json", {"language": "zh-cn", "details": "true"}),
            "air": (f"/airquality/v1/global/observations/{location_key}.json", {"language": "zh-cn"}),
            "indices": (f"/indices/v1/daily/1day/{location_key}/100", {"language": "zh-cn", "details": "true"}),
        }
        if lat is not None and lon is not None:
            jobs["minute"] = ("/nowcast_cn/v3/basic", {"q": f"{lat},{lon}"})

        result, stale = {}, []
        # 并发 4：实际发往上游的节奏由 RateLimiter 统一控制在每秒最多 5 次
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(self._fetch, name, path, params): name
                       for name, (path, params) in jobs.items()}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    data, is_stale = future.result()
                    result[name] = data
                    if is_stale:
                        stale.append(name)
                except Exception as exc:
                    logger.error("获取 %s 失败: %s", name, exc)
                    result[name] = {"error": str(exc)}

        result["meta"] = {
            "stale": stale,
            "quota_remaining": self.quota.remaining,
        }
        return result
