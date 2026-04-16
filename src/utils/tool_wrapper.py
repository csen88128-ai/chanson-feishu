"""
工具包装器模块
为工具调用添加重试、缓存和降级机制
"""
import time
import functools
from typing import Callable, Any, Optional
from datetime import datetime


class ToolWrapper:
    """工具包装器基类"""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        cache_ttl: int = 300
    ):
        """
        初始化工具包装器
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            cache_ttl: 缓存有效期（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache_ttl = cache_ttl
        self._cache = {}
    
    def wrap(self, func: Callable) -> Callable:
        """
        包装工具函数，添加重试和缓存
        
        Args:
            func: 要包装的函数
            
        Returns:
            包装后的函数
        """
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            # 尝试从缓存获取
            cache_key = self._get_cache_key(func.__name__, args, kwargs)
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                print(f"✅ 工具缓存命中: {func.__name__}")
                return cached_result
            
            # 执行工具，带重试
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    print(f"🔧 工具调用: {func.__name__} (尝试 {attempt + 1}/{self.max_retries})")
                    result = func(*args, **kwargs)
                    
                    # 成功，缓存结果
                    self._set_to_cache(cache_key, result)
                    print(f"✅ 工具成功: {func.__name__}")
                    return result
                    
                except Exception as e:
                    last_error = e
                    print(f"⚠️  工具失败: {func.__name__} - {str(e)}")
                    
                    if attempt < self.max_retries - 1:
                        # 等待后重试
                        time.sleep(self.retry_delay)
                        continue
            
            # 所有重试都失败，返回降级结果
            print(f"❌ 工具降级: {func.__name__}")
            return self._get_fallback_result(func.__name__, args, kwargs, last_error)
        
        return wrapped
    
    def _get_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 简化：使用函数名和第一个参数（通常是symbol）
        symbol = args[0] if args else kwargs.get('symbol', 'default')
        return f"{func_name}_{symbol}"
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取"""
        if key in self._cache:
            cached = self._cache[key]
            age = time.time() - cached['timestamp']
            if age < self.cache_ttl:
                return cached['value']
            else:
                # 缓存过期，删除
                del self._cache[key]
        return None
    
    def _set_to_cache(self, key: str, value: Any):
        """设置缓存"""
        self._cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def _get_fallback_result(self, func_name: str, args: tuple, kwargs: dict, error: Exception) -> str:
        """获取降级结果"""
        symbol = args[0] if args else kwargs.get('symbol', 'BTCUSDT')
        
        # 尝试从文件读取数据
        import json
        import os
        
        fallback_data_file = f"/workspace/chanson-feishu/{symbol.lower()}_latest_realtime_v2.json"
        
        if os.path.exists(fallback_data_file):
            try:
                with open(fallback_data_file, 'r') as f:
                    data = json.load(f)
                
                # 根据不同函数返回不同格式
                if 'kline' in func_name:
                    return json.dumps({
                        'symbol': symbol,
                        'interval': kwargs.get('interval', '1h'),
                        'data': data,
                        'source': 'fallback_file',
                        'timestamp': datetime.now().isoformat()
                    })
                elif 'sentiment' in func_name:
                    return json.dumps({
                        'symbol': symbol,
                        'fear_greed_index': data.get('rsi', 50),
                        'sentiment': 'neutral',
                        'source': 'fallback_file',
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return json.dumps({
                        'symbol': symbol,
                        'data': data,
                        'source': 'fallback_file',
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"❌ 降级失败: {str(e)}")
        
        # 最终降级：返回错误信息
        return json.dumps({
            'error': f"Tool failed after {self.max_retries} retries: {str(error)}",
            'symbol': symbol,
            'source': 'error_fallback',
            'timestamp': datetime.now().isoformat()
        })
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        print("🗑️  工具缓存已清空")


# 全局工具包装器实例
_global_wrapper = ToolWrapper(max_retries=3, retry_delay=1.0, cache_ttl=300)


def wrap_tool(func: Callable) -> Callable:
    """
    包装工具函数（便捷方法）
    
    Usage:
        @wrap_tool
        def my_tool(symbol: str) -> str:
            # 工具实现
            pass
    """
    return _global_wrapper.wrap(func)


def clear_tool_cache():
    """清空工具缓存"""
    _global_wrapper.clear_cache()
