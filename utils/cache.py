"""
缓存管理模块
提供数据缓存功能，减少重复API调用
"""
import pickle
import os
import time
from typing import Any, Optional
from pathlib import Path
import hashlib


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: str = "cache", ttl: int = 3600):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
            ttl: 缓存过期时间（秒）
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl

        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, key: str) -> str:
        """
        生成缓存文件名

        Args:
            key: 缓存键

        Returns:
            缓存文件名
        """
        # 使用MD5哈希避免文件名过长
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return key_hash

    def _get_cache_path(self, key: str) -> Path:
        """
        获取缓存文件路径

        Args:
            key: 缓存键

        Returns:
            缓存文件路径
        """
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.pkl"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        cache_path = self._get_cache_path(key)

        # 检查缓存文件是否存在
        if not cache_path.exists():
            return None

        # 检查缓存是否过期
        file_mtime = cache_path.stat().st_mtime
        if time.time() - file_mtime > self.ttl:
            # 缓存已过期，删除文件
            try:
                cache_path.unlink()
            except:
                pass
            return None

        # 读取缓存数据
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            return data
        except Exception as e:
            print(f"读取缓存失败 {key}: {e}")
            return None

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存数据

        Args:
            key: 缓存键
            value: 要缓存的数据
        """
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            print(f"写入缓存失败 {key}: {e}")

    def delete(self, key: str) -> None:
        """
        删除缓存数据

        Args:
            key: 缓存键
        """
        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            try:
                cache_path.unlink()
            except Exception as e:
                print(f"删除缓存失败 {key}: {e}")

    def clear(self) -> None:
        """清空所有缓存"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
        except Exception as e:
            print(f"清空缓存失败: {e}")

    def get_size(self) -> int:
        """
        获取缓存大小（字节）

        Returns:
            缓存总大小
        """
        total_size = 0
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                total_size += cache_file.stat().st_size
        except:
            pass
        return total_size


class MemoizedCache:
    """内存缓存装饰器"""

    def __init__(self, ttl: int = 3600):
        """
        初始化装饰器

        Args:
            ttl: 缓存过期时间（秒）
        """
        self.ttl = ttl
        self.cache = {}
        self.timestamps = {}

    def __call__(self, func):
        """装饰器"""
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = (func.__name__, args, frozenset(kwargs.items()))

            # 检查缓存
            if key in self.cache:
                # 检查是否过期
                if time.time() - self.timestamps[key] < self.ttl:
                    return self.cache[key]
                else:
                    # 缓存过期，删除
                    del self.cache[key]
                    del self.timestamps[key]

            # 调用函数
            result = func(*args, **kwargs)

            # 缓存结果
            self.cache[key] = result
            self.timestamps[key] = time.time()

            return result

        return wrapper

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()


# 全局缓存实例（默认1小时TTL）
_global_cache = None


def get_cache(ttl: int = 3600) -> CacheManager:
    """
    获取全局缓存实例

    Args:
        ttl: 缓存过期时间（秒）

    Returns:
        缓存管理器实例
    """
    global _global_cache

    if _global_cache is None or _global_cache.ttl != ttl:
        cache_dir = Path(__file__).parent.parent.parent / "cache"
        _global_cache = CacheManager(str(cache_dir), ttl)

    return _global_cache


# 测试代码
if __name__ == "__main__":
    # 测试缓存
    cache = CacheManager(cache_dir="test_cache", ttl=10)

    # 设置缓存
    cache.set("test_key", {"data": "test_value"})
    print("缓存已设置")

    # 获取缓存
    data = cache.get("test_key")
    print(f"获取缓存: {data}")

    # 测试缓存过期
    print("等待11秒...")
    time.sleep(11)

    data = cache.get("test_key")
    print(f"过期后获取缓存: {data}")

    # 测试装饰器
    print("\n=== 测试装饰器 ===")

    memo_cache = MemoizedCache(ttl=5)

    @memo_cache
    def expensive_function(n):
        print(f"执行耗时操作: 计算 {n} 的平方")
        return n ** 2

    # 第一次调用
    result1 = expensive_function(5)
    print(f"结果: {result1}")

    # 第二次调用（应该从缓存获取）
    result2 = expensive_function(5)
    print(f"结果: {result2}")

    # 等待过期
    print("等待6秒...")
    time.sleep(6)

    # 第三次调用（缓存已过期）
    result3 = expensive_function(5)
    print(f"结果: {result3}")

    # 清理测试缓存
    cache.clear()
    import shutil
    shutil.rmtree("test_cache")
