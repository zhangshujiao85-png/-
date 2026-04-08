"""
个股择时分析模块
提供买卖时机建议
"""
from dataclasses import dataclass
from enum import Enum
from typing import List
import pandas as pd
import numpy as np

from data.market_data import MarketDataFetcher
from utils.indicators import (
    calculate_ma, calculate_macd, calculate_rsi, calculate_kdj,
    detect_support_resistance, analyze_trend_strength
)
from analysis.market_regime import MarketRegime


class TimingAction(Enum):
    """操作建议"""
    BUY = "buy"           # 买入
    HOLD = "hold"         # 持有
    SELL = "sell"         # 卖出
    WAIT = "wait"         # 观望


@dataclass
class TimingSignal:
    """择时信号"""
    action: TimingAction
    confidence: float  # 置信度 0-100
    price_target: float  # 目标价位
    stop_loss: float  # 止损价位
    reasons: List[str]  # 原因列表
    technical_score: float  # 技术面得分 0-100
    sentiment_score: float  # 情绪面得分 0-100
    current_price: float  # 当前价格


class TimingAnalyzer:
    """个股择时分析器"""

    def __init__(self):
        """初始化分析器"""
        self.data_fetcher = MarketDataFetcher()

    def analyze(self, stock_code: str, market_regime: MarketRegime) -> TimingSignal:
        """
        分析个股买卖时机

        Args:
            stock_code: 股票代码
            market_regime: 市场状态

        Returns:
            择时信号
        """
        # 1. 获取股票数据
        history = self.data_fetcher.get_stock_history(stock_code, period=250)
        quote = self.data_fetcher.get_stock_quote(stock_code)

        if history.empty or not quote:
            return self._create_default_signal(stock_code)

        current_price = quote.get('price', history['close'].iloc[-1])

        # 2. 技术面分析
        technical_score = self._analyze_technical(history)

        # 3. 相对强弱分析
        relative_strength = self._analyze_relative_strength(history, stock_code)

        # 4. 结合市场状态
        market_factor = self._adjust_for_market(market_regime)

        # 5. 综合评分
        total_score = (
            technical_score * 0.5 +
            relative_strength * 0.3 +
            market_factor * 0.2
        )

        # 6. 生成买卖建议
        action = self._determine_action(total_score)
        confidence = self._calculate_confidence(total_score, technical_score, relative_strength)

        # 7. 计算目标价和止损价
        price_target, stop_loss = self._calculate_price_levels(history, action)

        # 8. 生成原因列表
        reasons = self._generate_reasons(
            history, technical_score, relative_strength, market_regime, action
        )

        return TimingSignal(
            action=action,
            confidence=confidence,
            price_target=price_target,
            stop_loss=stop_loss,
            reasons=reasons,
            technical_score=technical_score,
            sentiment_score=relative_strength,
            current_price=current_price
        )

    def _analyze_technical(self, history: pd.DataFrame) -> float:
        """
        技术面分析（0-100）

        Args:
            history: 历史数据

        Returns:
            技术面得分
        """
        if len(history) < 20:
            return 50.0

        score = 50.0
        close = history['close']

        # 1. MACD 分析（权重：25%）
        macd_data = calculate_macd(close)
        macd = macd_data['macd'].iloc[-1]
        signal = macd_data['signal'].iloc[-1]
        histogram = macd_data['histogram'].iloc[-1]

        if not pd.isna(macd) and not pd.isna(signal):
            if macd > signal and histogram > 0:
                score += 12.5  # 金叉且柱状图为正
            elif macd < signal and histogram < 0:
                score -= 12.5  # 死叉且柱状图为负

            # MACD 趋势
            if len(macd_data['macd']) >= 5:
                macd_trend = macd_data['macd'].iloc[-1] - macd_data['macd'].iloc[-5]
                score += min(macd_trend * 10, 10)  # 趋势加分

        # 2. RSI 分析（权重：20%）
        rsi = calculate_rsi(close)
        current_rsi = rsi.iloc[-1]

        if not pd.isna(current_rsi):
            if current_rsi < 30:
                score += 15  # 超卖，加分
            elif current_rsi > 70:
                score -= 15  # 超买，减分
            elif 40 <= current_rsi <= 60:
                score += 5  # 中性偏多

        # 3. KDJ 分析（权重：20%）
        if 'high' in history.columns and 'low' in history.columns:
            kdj_data = calculate_kdj(history['high'], history['low'], close)
            k = kdj_data['k'].iloc[-1]
            d = kdj_data['d'].iloc[-1]

            if not pd.isna(k) and not pd.isna(d):
                if k < 20 and d < 20:
                    score += 15  # 超卖区
                elif k > 80 and d > 80:
                    score -= 15  # 超买区
                elif k > d:
                    score += 5  # K线在D线上方

        # 4. 均线系统分析（权重：20%）
        ma20 = calculate_ma(close, 20)
        ma60 = calculate_ma(close, 60)

        if not pd.isna(ma20.iloc[-1]) and not pd.isna(ma60.iloc[-1]):
            if close.iloc[-1] > ma20.iloc[-1] > ma60.iloc[-1]:
                score += 15  # 多头排列
            elif close.iloc[-1] < ma20.iloc[-1] < ma60.iloc[-1]:
                score -= 15  # 空头排列

            # 价格与均线距离
            if ma20.iloc[-1] > 0:
                distance = (close.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]
                if -0.03 < distance < 0.03:
                    score += 5  # 接近均线，回调到位

        # 5. 支撑阻力位分析（权重：15%）
        if 'high' in history.columns and 'low' in history.columns:
            levels = detect_support_resistance(history)
            support = levels['support']
            resistance = levels['resistance']

            if support > 0 and resistance > 0:
                position = (close.iloc[-1] - support) / (resistance - support)
                if position < 0.3:
                    score += 10  # 接近支撑位
                elif position > 0.7:
                    score -= 10  # 接近阻力位

        return max(0, min(score, 100))

    def _analyze_relative_strength(self, history: pd.DataFrame,
                                  stock_code: str) -> float:
        """
        相对强弱分析（0-100）

        Args:
            history: 历史数据
            stock_code: 股票代码

        Returns:
            相对强弱得分
        """
        if len(history) < 20:
            return 50.0

        score = 50.0
        close = history['close']

        # 1. 近期涨跌幅（权重：40%）
        if len(history) >= 20:
            stock_return = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20]

            # 获取大盘涨跌幅
            try:
                index_data = self.data_fetcher.get_index_data('000001', period=250)
                if not index_data.empty and len(index_data) >= 20:
                    index_return = (index_data['close'].iloc[-1] -
                                  index_data['close'].iloc[-20]) / index_data['close'].iloc[-20]

                    # 相对强弱
                    relative_return = stock_return - index_return
                    score += relative_return * 100
            except:
                pass

        # 2. 近期排名（权重：30%）
        if len(history) >= 5:
            recent_return = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5]
            if recent_return > 0.03:
                score += 15  # 近期表现强势
            elif recent_return < -0.03:
                score -= 15  # 近期表现弱势

        # 3. 成交量分析（权重：30%）
        if 'volume' in history.columns and len(history) >= 10:
            recent_vol = history['volume'].tail(5).mean()
            prev_vol = history['volume'].iloc[-10:-5].mean()
            vol_ratio = recent_vol / prev_vol if prev_vol > 0 else 1

            # 放量上涨
            if close.iloc[-1] > close.iloc[-5] and vol_ratio > 1.3:
                score += 15
            # 放量下跌
            elif close.iloc[-1] < close.iloc[-5] and vol_ratio > 1.3:
                score -= 15

        return max(0, min(score, 100))

    def _adjust_for_market(self, market_regime: MarketRegime) -> float:
        """
        根据市场状态调整（0-100）

        Args:
            market_regime: 市场状态

        Returns:
            调整后的得分
        """
        base_score = 50.0

        if market_regime.trend.value == "bullish":
            # 牛市加分
            base_score += market_regime.strength * 30
        elif market_regime.trend.value == "bearish":
            # 熊市减分
            base_score -= market_regime.strength * 30

        return max(0, min(base_score, 100))

    def _determine_action(self, score: float) -> TimingAction:
        """
        根据评分确定操作

        Args:
            score: 综合评分

        Returns:
            操作建议
        """
        if score >= 70:
            return TimingAction.BUY
        elif score >= 55:
            return TimingAction.HOLD
        elif score >= 40:
            return TimingAction.WAIT
        else:
            return TimingAction.SELL

    def _calculate_confidence(self, total_score: float,
                            technical_score: float,
                            relative_score: float) -> float:
        """
        计算置信度

        Args:
            total_score: 综合评分
            technical_score: 技术面得分
            relative_score: 相对强弱得分

        Returns:
            置信度
        """
        # 基于评分的一致性
        scores = [total_score, technical_score, relative_score]
        std = np.std(scores)

        # 标准差越小，置信度越高
        confidence = max(100 - std * 2, 50)

        return min(confidence, 100)

    def _calculate_price_levels(self, history: pd.DataFrame,
                              action: TimingAction) -> tuple:
        """
        计算目标价和止损价

        Args:
            history: 历史数据
            action: 操作建议

        Returns:
            (目标价, 止损价)
        """
        if history.empty:
            return (0.0, 0.0)

        current_price = history['close'].iloc[-1]

        if action == TimingAction.BUY:
            # 买入：目标价+8%，止损价-5%
            target = current_price * 1.08
            stop_loss = current_price * 0.95
        elif action == TimingAction.SELL:
            # 卖出：目标价-5%，止损价+3%
            target = current_price * 0.95
            stop_loss = current_price * 1.03
        else:
            # 持有/观望：目标价+5%，止损价-3%
            target = current_price * 1.05
            stop_loss = current_price * 0.97

        return (round(target, 2), round(stop_loss, 2))

    def _generate_reasons(self, history: pd.DataFrame,
                         technical_score: float,
                         relative_score: float,
                         market_regime: MarketRegime,
                         action: TimingAction) -> List[str]:
        """
        生成原因列表

        Args:
            history: 历史数据
            technical_score: 技术面得分
            relative_score: 相对强弱得分
            market_regime: 市场状态
            action: 操作建议

        Returns:
            原因列表
        """
        reasons = []

        # 技术面原因
        if technical_score >= 70:
            reasons.append("技术面强势，多项指标向好")
        elif technical_score <= 30:
            reasons.append("技术面疲弱，多项指标走坏")
        else:
            reasons.append("技术面中性震荡")

        # 相对强弱原因
        if relative_score >= 70:
            reasons.append("跑赢大盘，表现强势")
        elif relative_score <= 30:
            reasons.append("弱于大盘，表现疲软")
        else:
            reasons.append("与大盘同步")

        # 市场环境原因
        if market_regime.trend.value == "bullish":
            reasons.append(f"市场处于{market_regime.trend.value}趋势，环境有利")
        elif market_regime.trend.value == "bearish":
            reasons.append(f"市场处于{market_regime.trend.value}趋势，谨慎操作")

        # 操作建议总结
        if action == TimingAction.BUY:
            reasons.append("建议逢低买入，把握机会")
        elif action == TimingAction.SELL:
            reasons.append("建议逢高减仓，控制风险")
        elif action == TimingAction.HOLD:
            reasons.append("建议继续持有，观察走势")
        else:
            reasons.append("建议耐心观望，等待信号")

        return reasons

    def _create_default_signal(self, stock_code: str) -> TimingSignal:
        """创建默认信号（数据获取失败时）"""
        return TimingSignal(
            action=TimingAction.WAIT,
            confidence=0.0,
            price_target=0.0,
            stop_loss=0.0,
            reasons=["无法获取股票数据，请检查股票代码"],
            technical_score=50.0,
            sentiment_score=50.0,
            current_price=0.0
        )


# 测试代码
if __name__ == "__main__":
    from analysis.market_regime import MarketRegimeAnalyzer

    # 创建分析器
    timing_analyzer = TimingAnalyzer()
    regime_analyzer = MarketRegimeAnalyzer()

    # 分析市场
    market_regime = regime_analyzer.analyze(['000001', '399001', '399006'])

    # 分析个股
    stock_code = "600519"  # 贵州茅台
    signal = timing_analyzer.analyze(stock_code, market_regime)

    print(f"=== {stock_code} 择时分析 ===")
    print(f"操作建议: {signal.action.value}")
    print(f"置信度: {signal.confidence:.0f}%")
    print(f"当前价格: {signal.current_price}")
    print(f"目标价位: {signal.price_target}")
    print(f"止损价位: {signal.stop_loss}")
    print(f"技术面得分: {signal.technical_score:.0f}")
    print(f"相对强弱: {signal.sentiment_score:.0f}")
    print(f"\n分析理由:")
    for i, reason in enumerate(signal.reasons, 1):
        print(f"{i}. {reason}")
