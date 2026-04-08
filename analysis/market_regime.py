"""
市场趋势分析模块
判断大盘趋势（牛市/熊市/震荡）
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict
import pandas as pd
import numpy as np

from data.market_data import MarketDataFetcher
from utils.indicators import calculate_ma, analyze_trend_strength


class MarketTrend(Enum):
    """市场趋势类型"""
    BULLISH = "bullish"      # 牛市
    BEARISH = "bearish"      # 熊市
    NEUTRAL = "neutral"      # 震荡


@dataclass
class MarketRegime:
    """市场状态"""
    trend: MarketTrend
    strength: float  # 趋势强度 0-1
    confidence: float  # 判断置信度 0-1
    position_advice: str  # 仓位建议
    reason: str  # 判断理由
    index_scores: Dict[str, float]  # 各指数得分


class MarketRegimeAnalyzer:
    """大盘趋势分析器"""

    def __init__(self):
        """初始化分析器"""
        self.data_fetcher = MarketDataFetcher()

    def analyze(self, index_codes: List[str] = None) -> MarketRegime:
        """
        分析市场趋势

        Args:
            index_codes: 指数代码列表

        Returns:
            市场状态对象
        """
        if index_codes is None:
            index_codes = ['000001', '399001', '399006']  # 上证、深证、创业板

        # 获取各指数数据
        index_data = {}
        for code in index_codes:
            data = self.data_fetcher.get_index_data(code, period=250)
            if not data.empty:
                index_data[code] = data

        if not index_data:
            # 如果无法获取数据，返回默认状态
            return MarketRegime(
                trend=MarketTrend.NEUTRAL,
                strength=0.5,
                confidence=0.0,
                position_advice="观望",
                reason="无法获取市场数据",
                index_scores={}
            )

        # 分析各指数趋势
        index_scores = {}
        for code, data in index_data.items():
            score = self._calculate_index_score(data)
            index_scores[code] = score

        # 综合判断市场趋势
        avg_score = np.mean(list(index_scores.values()))

        # 确定趋势类型
        if avg_score >= 60:
            trend = MarketTrend.BULLISH
        elif avg_score <= 40:
            trend = MarketTrend.BEARISH
        else:
            trend = MarketTrend.NEUTRAL

        # 计算趋势强度
        strength = min(abs(avg_score - 50) / 50, 1.0)

        # 计算置信度（基于各指数的一致性）
        score_std = np.std(list(index_scores.values()))
        confidence = max(1.0 - score_std / 50, 0.0)

        # 生成仓位建议
        position_advice = self._generate_position_advice(trend, strength, confidence)

        # 生成判断理由
        reason = self._generate_reason(index_data, index_scores, trend)

        return MarketRegime(
            trend=trend,
            strength=strength,
            confidence=confidence,
            position_advice=position_advice,
            reason=reason,
            index_scores=index_scores
        )

    def _calculate_index_score(self, data: pd.DataFrame) -> float:
        """
        计算单个指数的得分（0-100）

        Args:
            data: 指数历史数据

        Returns:
            指数得分
        """
        if len(data) < 60:
            return 50.0  # 数据不足，返回中性分数

        score = 50.0  # 基础分

        # 1. 均线系统分析（权重：30%）
        close = data['close']
        ma20 = calculate_ma(close, 20)
        ma60 = calculate_ma(close, 60)

        if not pd.isna(ma20.iloc[-1]) and not pd.isna(ma60.iloc[-1]):
            if close.iloc[-1] > ma20.iloc[-1] > ma60.iloc[-1]:
                score += 15  # 多头排列
            elif close.iloc[-1] < ma20.iloc[-1] < ma60.iloc[-1]:
                score -= 15  # 空头排列

            # 均线斜率
            if len(ma20) >= 5:
                ma20_slope = (ma20.iloc[-1] - ma20.iloc[-5]) / ma20.iloc[-5]
                score += ma20_slope * 100  # 斜率加分

        # 2. 近期涨跌幅（权重：25%）
        if len(data) >= 20:
            return_20d = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]
            score += return_20d * 100  # 涨跌幅转换为分数

        # 3. 成交量分析（权重：20%）
        if 'volume' in data.columns and len(data) >= 10:
            recent_vol = data['volume'].tail(5).mean()
            prev_vol = data['volume'].iloc[-10:-5].mean()
            vol_ratio = recent_vol / prev_vol if prev_vol > 0 else 1

            # 上涨放量加分
            if close.iloc[-1] > close.iloc[-5] and vol_ratio > 1.2:
                score += 10
            # 下跌放量减分
            elif close.iloc[-1] < close.iloc[-5] and vol_ratio > 1.2:
                score -= 10

        # 4. 波动率分析（权重：15%）
        if len(data) >= 20:
            returns = close.pct_change().tail(20)
            volatility = returns.std()
            # 低波动加分（趋势更稳定）
            score -= volatility * 100

        # 5. 相对高低位（权重：10%）
        if len(data) >= 60:
            high_60d = close.tail(60).max()
            low_60d = close.tail(60).min()
            current_position = (close.iloc[-1] - low_60d) / (high_60d - low_60d)
            score += (current_position - 0.5) * 20

        # 限制分数范围
        return max(0, min(score, 100))

    def _generate_position_advice(self, trend: MarketTrend,
                                  strength: float, confidence: float) -> str:
        """
        生成仓位建议

        Args:
            trend: 市场趋势
            strength: 趋势强度
            confidence: 置信度

        Returns:
            仓位建议
        """
        # 根据置信度调整
        if confidence < 0.5:
            return "观望（低置信度）"

        # 根据趋势和强度给出建议
        if trend == MarketTrend.BULLISH:
            if strength > 0.7:
                return "积极布局（7-8成仓位）"
            elif strength > 0.4:
                return "适度参与（5-6成仓位）"
            else:
                return "谨慎参与（3-4成仓位）"
        elif trend == MarketTrend.BEARISH:
            if strength > 0.7:
                return "空仓观望"
            elif strength > 0.4:
                return "轻仓防守（1-2成仓位）"
            else:
                return "逐步减仓"
        else:  # NEUTRAL
            return "均衡配置（4-5成仓位）"

    def _generate_reason(self, index_data: Dict[str, pd.DataFrame],
                        index_scores: Dict[str, float],
                        trend: MarketTrend) -> str:
        """
        生成判断理由

        Args:
            index_data: 各指数数据
            index_scores: 各指数得分
            trend: 市场趋势

        Returns:
            判断理由文本
        """
        reasons = []

        # 分析各指数表现
        for code, score in index_scores.items():
            if code == '000001':
                name = "上证指数"
            elif code == '399001':
                name = "深证成指"
            elif code == '399006':
                name = "创业板指"
            else:
                name = f"指数{code}"

            if score >= 60:
                reasons.append(f"{name}表现较强（{score:.0f}分）")
            elif score <= 40:
                reasons.append(f"{name}表现较弱（{score:.0f}分）")
            else:
                reasons.append(f"{name}震荡整理（{score:.0f}分）")

        # 综合分析
        if trend == MarketTrend.BULLISH:
            reasons.append("整体市场处于上升趋势，建议把握机会")
        elif trend == MarketTrend.BEARISH:
            reasons.append("整体市场处于下降趋势，注意控制风险")
        else:
            reasons.append("市场方向不明，建议耐心等待")

        return "；".join(reasons)


# 测试代码
if __name__ == "__main__":
    analyzer = MarketRegimeAnalyzer()

    print("=== 市场趋势分析 ===")
    regime = analyzer.analyze(['000001', '399001', '399006'])

    print(f"市场趋势: {regime.trend.value}")
    print(f"趋势强度: {regime.strength:.2%}")
    print(f"置信度: {regime.confidence:.2%}")
    print(f"仓位建议: {regime.position_advice}")
    print(f"判断理由: {regime.reason}")
    print(f"\n各指数得分: {regime.index_scores}")
