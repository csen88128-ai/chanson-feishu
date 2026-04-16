"""
优化版系统Prompt模块
提供简洁、高效的Prompt模板
"""

# ==================== 缠论分析Prompt ====================

CHANSON_ANALYSIS_PROMPT = """你是专业的缠论分析师，精通缠论理论和实战应用。

【任务】对BTC进行快速缠论分析并给出明确建议。

【输入数据】
价格: ${price}
RSI: {rsi}
MACD: {macd}
MA5: ${ma5}, MA20: ${ma20}, MA60: ${ma60}

【分析要求】（简洁版）
1. 趋势: 多头/空头/震荡（1句话）
2. 结构: 笔/线段/中枢状态（50字内）
3. 信号: 有无三类买卖点（20字内）
4. 策略: 方向+点位+仓位+止损（100字内）
5. 风险: 1-5星+主要风险点（50字内）

【输出格式】
# 缠论分析 - BTC

## 趋势
[趋势判断]

## 结构
[结构描述]

## 信号
[买卖点信号]

## 策略
方向: [多/空/观望]
入场: [价格]
目标: [价格]
止损: [价格]
仓位: [百分比]

## 风险
[风险等级] - [主要风险]

【重要】
- 字数控制在300字以内
- 使用简洁的术语
- 给出明确的数值和点位
- 不要调用任何工具
"""

# ==================== 市场情绪Prompt ====================

SENTIMENT_ANALYSIS_PROMPT = """你是市场情绪分析专家。

【任务】基于RSI和价格变化快速判断市场情绪。

【输入】
RSI: {rsi}
价格变化: {change_percent}%

【输出格式】
情绪: [极度恐惧/恐惧/中性/贪婪/极度贪婪]
数值: [0-100]
建议: [1句话操作建议]

【规则】
- RSI<30 → 极度恐惧（20-30）
- 30≤RSI<40 → 恐惧（30-40）
- 40≤RSI<60 → 中性（50）
- 60≤RSI<70 → 贪婪（60-70）
- RSI≥70 → 极度贪婪（70-80）
"""

# ==================== 风险评估Prompt ====================

RISK_ASSESSMENT_PROMPT = """你是风险评估专家。

【任务】快速评估BTC当前交易风险。

【输入】
价格: ${price}
RSI: {rsi}
波动率: {volatility}

【输出格式】
风险等级: [1-5星]
主要风险:
1. [风险点1]
2. [风险点2]
3. [风险点3]

建议仓位: [百分比]
"""

# ==================== 综合决策Prompt ====================

DECISION_PROMPT = """你是交易决策专家。

【任务】整合所有分析结果，给出最终决策。

【输入】
趋势: {trend}
结构: {structure}
信号: {signal}
情绪: {sentiment}
风险: {risk}

【输出格式】
# 最终决策

## 方向
[明确方向: 做多/做空/观望]

## 理由
[核心逻辑，100字内]

## 操作计划
- 入场位: [价格]
- 目标位: [价格]
- 止损位: [价格]
- 仓位: [百分比]
- 持有周期: [时间]

## 风险提示
[主要风险，50字内]

【重要】
- 结论必须明确
- 不可模棱两可
- 必须给出具体数值
"""

# ==================== 快速分析Prompt（最精简） ====================

QUICK_ANALYSIS_PROMPT = """快速分析BTC并给出建议。

数据: 价格${price}, RSI{rsi}, MACD{macd}

输出格式:
方向: [多/空/观]
理由: [20字]
点位: 入场[价格] 止损[价格]
风险: [1-5星]

【限制】50字以内。"""

# ==================== Prompt工厂 ====================

class PromptFactory:
    """Prompt工厂类"""
    
    @staticmethod
    def get_analysis_prompt(
        price: float = 0,
        rsi: float = 50,
        macd: float = 0,
        ma5: float = 0,
        ma20: float = 0,
        ma60: float = 0,
        mode: str = "standard"
    ) -> str:
        """
        获取分析Prompt
        
        Args:
            price: 价格
            rsi: RSI
            macd: MACD
            ma5: MA5
            ma20: MA20
            ma60: MA60
            mode: 模式（standard/quick）
            
        Returns:
            格式化的Prompt
        """
        if mode == "quick":
            return QUICK_ANALYSIS_PROMPT.format(
                price=price,
                rsi=rsi,
                macd=macd
            )
        
        return CHANSON_ANALYSIS_PROMPT.format(
            price=price,
            rsi=rsi,
            macd=macd,
            ma5=ma5,
            ma20=ma20,
            ma60=ma60
        )
    
    @staticmethod
    def get_sentiment_prompt(rsi: float, change_percent: float) -> str:
        """获取情绪分析Prompt"""
        return SENTIMENT_ANALYSIS_PROMPT.format(
            rsi=rsi,
            change_percent=change_percent
        )
    
    @staticmethod
    def get_risk_prompt(price: float, rsi: float, volatility: float = 0.05) -> str:
        """获取风险评估Prompt"""
        return RISK_ASSESSMENT_PROMPT.format(
            price=price,
            rsi=rsi,
            volatility=volatility
        )
    
    @staticmethod
    def get_decision_prompt(
        trend: str,
        structure: str,
        signal: str,
        sentiment: str,
        risk: str
    ) -> str:
        """获取决策Prompt"""
        return DECISION_PROMPT.format(
            trend=trend,
            structure=structure,
            signal=signal,
            sentiment=sentiment,
            risk=risk
        )
    
    @staticmethod
    def create_multi_stage_prompt(btc_data: dict) -> list:
        """
        创建多阶段Prompt（用于分步分析）
        
        Args:
            btc_data: BTC数据
            
        Returns:
            Prompt列表
        """
        prompts = []
        
        # 阶段1: 缠论结构分析
        prompts.append({
            "stage": "structure",
            "prompt": CHANSON_ANALYSIS_PROMPT.format(
                price=btc_data['current_price'],
                rsi=btc_data['rsi'],
                macd=btc_data['macd'],
                ma5=btc_data['ma5'],
                ma20=btc_data['ma20'],
                ma60=btc_data['ma60']
            ),
            "output_limit": 100  # 限制输出字数
        })
        
        # 阶段2: 市场情绪
        prompts.append({
            "stage": "sentiment",
            "prompt": SENTIMENT_ANALYSIS_PROMPT.format(
                rsi=btc_data['rsi'],
                change_percent=btc_data['change_percent']
            ),
            "output_limit": 50
        })
        
        # 阶段3: 风险评估
        prompts.append({
            "stage": "risk",
            "prompt": RISK_ASSESSMENT_PROMPT.format(
                price=btc_data['current_price'],
                rsi=btc_data['rsi'],
                volatility=0.05
            ),
            "output_limit": 80
        })
        
        # 阶段4: 综合决策
        prompts.append({
            "stage": "decision",
            "prompt": DECISION_PROMPT.format(
                trend="待分析",
                structure="待分析",
                signal="待分析",
                sentiment="待分析",
                risk="待分析"
            ),
            "output_limit": 150
        })
        
        return prompts


# 便捷函数
def get_optimized_prompt(prompt_type: str, **kwargs) -> str:
    """
    获取优化的Prompt（便捷接口）
    
    Args:
        prompt_type: Prompt类型
        **kwargs: 参数
        
    Returns:
        格式化的Prompt
    """
    factory = PromptFactory()
    
    if prompt_type == "analysis":
        return factory.get_analysis_prompt(**kwargs)
    elif prompt_type == "sentiment":
        return factory.get_sentiment_prompt(**kwargs)
    elif prompt_type == "risk":
        return factory.get_risk_prompt(**kwargs)
    elif prompt_type == "decision":
        return factory.get_decision_prompt(**kwargs)
    else:
        return QUICK_ANALYSIS_PROMPT.format(**kwargs)


# ==================== Prompt优化对比 ====================

PROMPT_COMPARISON = """
## Prompt优化对比

### 优化前（冗长）
- 字数: ~2000字
- 分析维度: 10+
- 输出格式: 详细报告
- LLM耗时: ~35秒
- 问题: 内容冗余，用户阅读困难

### 优化后（简洁）
- 字数: ~300字
- 分析维度: 5
- 输出格式: 结构化摘要
- LLM耗时: ~15秒（预估）
- 优势: 直观易懂，快速响应

### 优化效果
- 字数减少: 85%
- 耗时预估减少: 57%
- 可读性: 大幅提升
- 决策效率: 显著提升
"""
