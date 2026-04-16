"""
数据验证模块
确保数据质量和有效性
"""
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    score: float
    timestamp: str
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'score': self.score,
            'timestamp': self.timestamp
        }


class DataValidator:
    """数据验证器"""
    
    def __init__(
        self,
        max_age_seconds: int = 600,
        required_fields: List[str] = None
    ):
        """
        初始化数据验证器
        
        Args:
            max_age_seconds: 数据最大有效期（秒）
            required_fields: 必需字段列表
        """
        self.max_age_seconds = max_age_seconds
        self.required_fields = required_fields or [
            'current_price',
            'rsi',
            'macd',
            'ma5',
            'ma20',
            'ma60'
        ]
    
    def validate_btc_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证BTC数据
        
        Args:
            data: BTC数据
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        score = 100.0
        
        # 1. 检查必需字段
        for field in self.required_fields:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")
                score -= 20
            elif data[field] is None:
                errors.append(f"字段值为空: {field}")
                score -= 15
        
        # 2. 检查价格有效性
        if 'current_price' in data:
            price = data['current_price']
            if price <= 0:
                errors.append(f"价格无效: {price}")
                score -= 30
            elif price < 1000:
                warnings.append(f"价格过低: {price}")
                score -= 10
            elif price > 1000000:
                warnings.append(f"价格过高: {price}")
                score -= 10
        
        # 3. 检查RSI有效性
        if 'rsi' in data and data['rsi'] is not None:
            rsi = data['rsi']
            if not (0 <= rsi <= 100):
                errors.append(f"RSI超出范围(0-100): {rsi}")
                score -= 20
            elif rsi < 5:
                warnings.append(f"RSI极低: {rsi}")
                score -= 5
            elif rsi > 95:
                warnings.append(f"RSI极高: {rsi}")
                score -= 5
        
        # 4. 检查MACD有效性
        if 'macd' in data and data['macd'] is not None:
            macd = data['macd']
            if abs(macd) > 10000:
                warnings.append(f"MACD异常: {macd}")
                score -= 5
        
        # 5. 检查均线逻辑
        if all(k in data for k in ['ma5', 'ma20', 'ma60']):
            ma5 = data['ma5']
            ma20 = data['ma20']
            ma60 = data['ma60']
            
            # 检查均线是否为空
            if ma5 is None or ma20 is None or ma60 is None:
                errors.append("均线数据不完整")
                score -= 10
            
            # 检查均线是否为0
            elif ma5 == 0 or ma20 == 0 or ma60 == 0:
                errors.append("均线值为0")
                score -= 15
            
            # 检查均线偏差（不应相差太大）
            else:
                deviation = max(abs(ma5 - ma20), abs(ma20 - ma60))
                if deviation > ma5 * 0.5:  # 偏差超过50%
                    warnings.append(f"均线偏差过大: {deviation:.2f}")
                    score -= 5
        
        # 6. 检查数据时效性
        if 'data_time' in data and data['data_time']:
            try:
                data_time = datetime.fromisoformat(data['data_time'])
                age = (datetime.now() - data_time).total_seconds()
                
                if age > self.max_age_seconds:
                    warnings.append(f"数据过期: {age:.1f}秒（最大允许: {self.max_age_seconds}秒）")
                    score -= 15
            except Exception as e:
                warnings.append(f"数据时间格式错误: {str(e)}")
                score -= 5
        
        # 7. 检查涨跌幅合理性
        if 'change_percent' in data and data['change_percent'] is not None:
            change = data['change_percent']
            if abs(change) > 50:  # 涨跌幅超过50%
                errors.append(f"涨跌幅异常: {change}%")
                score -= 25
            elif abs(change) > 20:  # 涨跌幅超过20%
                warnings.append(f"涨跌幅较大: {change}%")
                score -= 10
        
        # 8. 检查成交量
        if 'volume' in data and data['volume'] is not None:
            volume = data['volume']
            if volume < 0:
                errors.append(f"成交量为负: {volume}")
                score -= 20
            elif volume == 0:
                warnings.append("成交量为0")
                score -= 10
        
        # 确保分数在0-100之间
        score = max(0, min(100, score))
        
        # 判断是否有效（分数>=60且无错误）
        is_valid = score >= 60 and len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            score=score,
            timestamp=datetime.now().isoformat()
        )
    
    def validate_and_fix(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], ValidationResult]:
        """
        验证数据并尝试修复
        
        Args:
            data: 原始数据
            
        Returns:
            修复后的数据和验证结果
        """
        # 先验证
        result = self.validate_btc_data(data)
        
        if result.is_valid:
            return data, result
        
        # 尝试修复
        fixed_data = data.copy()
        
        # 修复价格
        if 'current_price' not in fixed_data or fixed_data['current_price'] is None:
            if 'close' in fixed_data:
                fixed_data['current_price'] = fixed_data['close']
            elif 'close' not in fixed_data and 'ma5' in fixed_data:
                fixed_data['current_price'] = fixed_data['ma5']
        
        # 修复RSI
        if 'rsi' not in fixed_data or fixed_data['rsi'] is None:
            fixed_data['rsi'] = 50  # 默认值
        
        # 修复MACD
        if 'macd' not in fixed_data or fixed_data['macd'] is None:
            fixed_data['macd'] = 0.0
        
        # 修复均线
        for ma_key in ['ma5', 'ma20', 'ma60']:
            if ma_key not in fixed_data or fixed_data[ma_key] is None:
                if 'current_price' in fixed_data:
                    fixed_data[ma_key] = fixed_data['current_price']
        
        # 重新验证
        result = self.validate_btc_data(fixed_data)
        
        return fixed_data, result
    
    def get_quality_level(self, score: float) -> str:
        """
        获取质量等级
        
        Args:
            score: 质量分数
            
        Returns:
            质量等级
        """
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "中等"
        elif score >= 60:
            return "及格"
        else:
            return "差"


class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.history: List[Dict] = []
    
    def monitor(self, data: Dict[str, Any], save: bool = True) -> ValidationResult:
        """
        监控数据质量
        
        Args:
            data: 数据
            save: 是否保存到历史记录
            
        Returns:
            验证结果
        """
        result = self.validator.validate_btc_data(data)
        
        if save:
            self.history.append({
                'timestamp': datetime.now().isoformat(),
                'result': result.to_dict(),
                'price': data.get('current_price', 0)
            })
            
            # 只保留最近100条记录
            if len(self.history) > 100:
                self.history.pop(0)
        
        return result
    
    def get_quality_trend(self, last_n: int = 10) -> Dict[str, Any]:
        """
        获取质量趋势
        
        Args:
            last_n: 最近N条记录
            
        Returns:
            质量趋势数据
        """
        recent = self.history[-last_n:]
        
        if not recent:
            return {
                'avg_score': 0,
                'trend': 'unknown',
                'min_score': 0,
                'max_score': 0
            }
        
        scores = [r['result']['score'] for r in recent]
        avg_score = sum(scores) / len(scores)
        
        # 判断趋势
        if len(scores) >= 3:
            recent_3 = scores[-3:]
            if all(recent_3[i] < recent_3[i+1] for i in range(2)):
                trend = 'improving'
            elif all(recent_3[i] > recent_3[i+1] for i in range(2)):
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'unknown'
        
        return {
            'avg_score': avg_score,
            'trend': trend,
            'min_score': min(scores),
            'max_score': max(scores),
            'sample_count': len(recent)
        }
    
    def print_monitor_report(self):
        """打印监控报告"""
        print(f"\n{'='*70}")
        print("  📊 数据质量监控报告")
        print(f"{'='*70}\n")
        
        if not self.history:
            print("暂无监控数据")
            return
        
        trend = self.get_quality_trend()
        
        print(f"最近记录数: {len(self.history)}")
        print(f"平均质量分: {trend['avg_score']:.1f}")
        print(f"质量趋势: {trend['trend']}")
        print(f"最低分: {trend['min_score']:.1f}")
        print(f"最高分: {trend['max_score']:.1f}")
        
        print(f"\n最近5条记录:")
        for i, record in enumerate(self.history[-5:]):
            result = record['result']
            status = "✅" if result['is_valid'] else "❌"
            print(f"  {status} {record['timestamp']}: 分数={result['score']:.1f}")
        
        print(f"{'='*70}\n")


# 全局监控器实例
_global_monitor: Optional[DataQualityMonitor] = None


def get_validator() -> DataValidator:
    """获取全局验证器"""
    return DataValidator()


def get_monitor() -> DataQualityMonitor:
    """获取全局监控器"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = DataQualityMonitor()
    return _global_monitor


def validate_data(data: Dict[str, Any]) -> ValidationResult:
    """
    验证数据（便捷接口）
    
    Args:
        data: 数据
        
    Returns:
        验证结果
    """
    validator = get_validator()
    return validator.validate_btc_data(data)


def validate_and_fix_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], ValidationResult]:
    """
    验证并修复数据（便捷接口）
    
    Args:
        data: 数据
        
    Returns:
        修复后的数据和验证结果
    """
    validator = get_validator()
    return validator.validate_and_fix(data)
