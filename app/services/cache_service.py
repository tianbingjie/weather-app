"""内存 TTL 缓存 + 每日 API 调用配额控制。

目标：把对 WeatherCN 上游的调用控制在每天 400 次以内。
策略：
1. 各端点 TTL 缓存，命中则不请求上游；
2. 缓存过期后优先保留旧值（stale），上游失败或配额用尽时回退旧值；
3. DailyQuota 按自然日计数，超出后只读缓存。
"""
import threading
import time


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value, expires_at):
        self.value = value
        self.expires_at = expires_at


class TTLCache:
    """线程安全的内存缓存；过期条目保留用于 stale 回退。"""

    def __init__(self, max_items: int = 2048):
        self._items: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()
        self._max_items = max_items

    def get(self, key: str):
        """返回 (value, is_fresh)。value 为 None 表示完全没有缓存。"""
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None, False
            if entry.expires_at > time.time():
                return entry.value, True
            return entry.value, False  # 过期但保留 stale 值

    def set(self, key: str, value, ttl: float) -> None:
        with self._lock:
            if len(self._items) >= self._max_items:
                now = time.time()
                for k in [k for k, e in self._items.items() if e.expires_at < now]:
                    del self._items[k]
                if len(self._items) >= self._max_items:
                    return
            self._items[key] = _CacheEntry(value, time.time() + ttl)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


class DailyQuota:
    """按自然日计数的调用配额；limit <= 0 表示不限制。"""

    def __init__(self, limit: int):
        self._limit = limit
        self._lock = threading.Lock()
        self._day = None
        self._used = 0

    def _roll_if_needed(self) -> None:
        today = time.localtime()[:3]
        if today != self._day:
            self._day = today
            self._used = 0

    def try_acquire(self) -> bool:
        if self._limit <= 0:
            return True
        with self._lock:
            self._roll_if_needed()
            if self._used >= self._limit:
                return False
            self._used += 1
            return True

    @property
    def remaining(self) -> int:
        if self._limit <= 0:
            return -1
        with self._lock:
            self._roll_if_needed()
            return self._limit - self._used
