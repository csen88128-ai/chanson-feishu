"""
数据预加载模块
在系统启动时预加载常用交易对数据
"""
import os
import json
import time
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class DataPreloader:
    """数据预加载器"""
    
    def __init__(
        self,
        symbols: List[str] = None,
        data_dir: str = "/workspace/chanson-feishu",
        ttl: int = 600
    ):
        """
        初始化数据预加载器
        
        Args:
            symbols: 要预加载的交易对列表
            data_dir: 数据目录
            ttl: 数据有效期（秒）
        """
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        self.data_dir = data_dir
        self.ttl = ttl
        self.cache: Dict[str, Dict] = {}
        self.preloaded = False
        
        # 添加文件名映射
        self.file_mapping = {
            "BTCUSDT": ["btc_latest_realtime_v2.json", "btc_latest_realtime.json", "btc_latest.json"],
            "ETHUSDT": ["eth_latest_realtime_v2.json", "eth_latest_realtime.json"],
            "SOLUSDT": ["sol_latest_realtime_v2.json", "sol_latest_realtime.json"]
        }
    
    async def preload(self, force: bool = False) -> Dict[str, bool]:
        """
        预加载数据
        
        Args:
            force: 是否强制重新加载
            
        Returns:
            预加载结果 {symbol: success}
        """
        print(f"\n{'='*70}")
        print("  📦 开始预加载数据")
        print(f"{'='*70}\n")
        
        results = {}
        start_time = time.time()
        
        for symbol in self.symbols:
            print(f"🔍 预加载 {symbol}...")
            
            try:
                # 检查是否需要重新加载
                if not force and symbol in self.cache:
                    cached = self.cache[symbol]
                    age = time.time() - cached['timestamp']
                    if age < self.ttl:
                        print(f"  ✅ 使用缓存（缓存时长: {age:.1f}秒）")
                        results[symbol] = True
                        continue
                
                # 从文件加载数据
                data = await self._load_from_file(symbol)
                
                if data:
                    self.cache[symbol] = {
                        'value': data,
                        'timestamp': time.time()
                    }
                    print(f"  ✅ 预加载成功（价格: ${data.get('current_price', 0):,.2f}）")
                    results[symbol] = True
                else:
                    print(f"  ⚠️  预加载失败（数据文件不存在）")
                    results[symbol] = False
                    
            except Exception as e:
                print(f"  ❌ 预加载失败: {str(e)}")
                results[symbol] = False
        
        elapsed = time.time() - start_time
        self.preloaded = True
        
        print(f"\n{'='*70}")
        print(f"  ✅ 预加载完成（耗时: {elapsed:.2f}秒）")
        print(f"  成功: {sum(results.values())}/{len(results)}")
        print(f"{'='*70}\n")
        
        return results
    
    async def _load_from_file(self, symbol: str) -> Optional[Dict]:
        """
        从文件加载数据
        
        Args:
            symbol: 交易对
            
        Returns:
            数据字典
        """
        # 使用文件名映射
        if symbol in self.file_mapping:
            for filename in self.file_mapping[symbol]:
                filepath = os.path.join(self.data_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r') as f:
                        return json.load(f)
        
        # 如果映射中没有，尝试默认文件名
        possible_files = [
            f"{self.data_dir}/{symbol.lower()}_latest_realtime_v2.json",
            f"{self.data_dir}/{symbol.lower()}_latest_realtime.json",
            f"{self.data_dir}/data/{symbol.lower()}_latest.json"
        ]
        
        for filepath in possible_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        
        return None
    
    def get(self, symbol: str) -> Optional[Dict]:
        """
        获取预加载的数据
        
        Args:
            symbol: 交易对
            
        Returns:
            数据字典
        """
        if symbol in self.cache:
            cached = self.cache[symbol]
            age = time.time() - cached['timestamp']
            
            if age < self.ttl:
                return cached['value']
            else:
                # 缓存过期，删除
                del self.cache[symbol]
        
        return None
    
    def get_all(self) -> Dict[str, Dict]:
        """
        获取所有预加载的数据
        
        Returns:
            所有数据字典
        """
        return {
            symbol: self.get(symbol)
            for symbol in self.symbols
            if self.get(symbol) is not None
        }
    
    def refresh(self, symbol: Optional[str] = None) -> Dict[str, bool]:
        """
        刷新数据
        
        Args:
            symbol: 要刷新的交易对，None表示刷新所有
            
        Returns:
            刷新结果
        """
        if symbol:
            return asyncio.run(self.preload(force=True))
        else:
            symbols = [symbol] if symbol else self.symbols
            old_symbols = self.symbols
            self.symbols = symbols
            results = asyncio.run(self.preload(force=True))
            self.symbols = old_symbols
            return results
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        print("🗑️  预加载缓存已清空")
    
    def get_stats(self) -> Dict:
        """
        获取预加载统计信息
        
        Returns:
            统计信息
        """
        stats = {
            'symbols_count': len(self.symbols),
            'cached_count': len(self.cache),
            'preloaded': self.preloaded,
            'cache_age': {}
        }
        
        for symbol, cached in self.cache.items():
            stats['cache_age'][symbol] = time.time() - cached['timestamp']
        
        return stats
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        
        print(f"\n{'='*70}")
        print("  📊 预加载统计")
        print(f"{'='*70}")
        print(f"配置的交易对: {stats['symbols_count']}")
        print(f"已缓存数量: {stats['cached_count']}")
        print(f"已预加载: {'是' if stats['preloaded'] else '否'}")
        
        if stats['cache_age']:
            print(f"\n缓存时长:")
            for symbol, age in stats['cache_age'].items():
                print(f"  {symbol}: {age:.1f}秒")
        
        print(f"{'='*70}\n")


# 全局实例
_global_preloader: Optional[DataPreloader] = None


def get_preloader() -> DataPreloader:
    """
    获取全局预加载器实例
    
    Returns:
        数据预加载器实例
    """
    global _global_preloader
    if _global_preloader is None:
        _global_preloader = DataPreloader()
    return _global_preloader


async def initialize_preload(symbols: List[str] = None) -> Dict[str, bool]:
    """
    初始化预加载
    
    Args:
        symbols: 要预加载的交易对列表
        
    Returns:
        预加载结果
    """
    preloader = get_preloader()
    
    if symbols:
        preloader.symbols = symbols
    
    return await preloader.preload()


def get_preloaded_data(symbol: str) -> Optional[Dict]:
    """
    获取预加载的数据（同步接口）
    
    Args:
        symbol: 交易对
        
    Returns:
        数据字典
    """
    preloader = get_preloader()
    return preloader.get(symbol)


def get_all_preloaded_data() -> Dict[str, Dict]:
    """
    获取所有预加载的数据（同步接口）
    
    Returns:
        所有数据字典
    """
    preloader = get_preloader()
    return preloader.get_all()


def refresh_preloaded_data(symbol: Optional[str] = None) -> Dict[str, bool]:
    """
    刷新预加载的数据（同步接口）
    
    Args:
        symbol: 要刷新的交易对，None表示刷新所有
        
    Returns:
        刷新结果
    """
    preloader = get_preloader()
    return preloader.refresh(symbol)
