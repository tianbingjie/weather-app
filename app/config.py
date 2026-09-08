import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    weather_base_url: str = os.getenv("WEATHER_BASE_URL", "https://openapi.weathercn.com")
    request_timeout: float = float(os.getenv("WEATHER_REQUEST_TIMEOUT", "12"))

    # 每日上游 API 调用配额（自然日重置），<= 0 表示不限制
    daily_quota: int = int(os.getenv("WEATHER_DAILY_QUOTA", "400"))

    # 上游请求速率上限（次/秒），<= 0 表示不限制
    qps_limit: float = float(os.getenv("WEATHER_QPS_LIMIT", "5"))

    # 各端点缓存 TTL（秒）。默认值按"单城市全天持续访问约 210 次/天"设计，
    # 配额器兜底，保证总调用不超过 400 次/天。
    cache_ttl_current: int = int(os.getenv("CACHE_TTL_CURRENT", "600"))      # 实况天气 10 分钟
    cache_ttl_minute: int = int(os.getenv("CACHE_TTL_MINUTE", "1800"))       # 分钟级降水 30 分钟
    cache_ttl_hourly: int = int(os.getenv("CACHE_TTL_HOURLY", "3600"))       # 逐小时 1 小时
    cache_ttl_alerts: int = int(os.getenv("CACHE_TTL_ALERTS", "3600"))       # 预警 1 小时
    cache_ttl_air: int = int(os.getenv("CACHE_TTL_AIR", "7200"))             # 空气质量 2 小时
    cache_ttl_daily: int = int(os.getenv("CACHE_TTL_DAILY", "21600"))        # 逐日预报 6 小时
    cache_ttl_indices: int = int(os.getenv("CACHE_TTL_INDICES", "43200"))    # 生活指数 12 小时
    cache_ttl_search: int = int(os.getenv("CACHE_TTL_SEARCH", "86400"))      # 城市搜索 24 小时
    cache_ttl_locate: int = int(os.getenv("CACHE_TTL_LOCATE", "86400"))      # 经纬度定位 24 小时


settings = Settings()
