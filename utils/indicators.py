"""
技术指标计算模块
包含常用的技术分析指标计算函数
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple


def calculate_ma(data: pd.Series, period: int) -> pd.Series:
    """
    计算移动平均线

    Args:
        data: 价格序列
        period: 周期

    Returns:
        移动平均线序列
    """
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    计算指数移动平均线

    Args:
        data: 价格序列
        period: 周期

    Returns:
        指数移动平均线序列
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26,
                   signal: int = 9) -> Dict[str, pd.Series]:
    """
    计算 MACD 指标

    Args:
        data: 收盘价序列
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期

    Returns:
        包含 MACD 线、信号线、柱状图的字典
    """
    # 计算快速和慢速EMA
    ema_fast = calculate_ema(data, fast)
    ema_slow = calculate_ema(data, slow)

    # MACD 线
    macd_line = ema_fast - ema_slow

    # 信号线
    signal_line = calculate_ema(macd_line, signal)

    # 柱状图
    histogram = macd_line - signal_line

    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    计算 RSI 指标

    Args:
        data: 价格序列
        period: 周期

    Returns:
        RSI 序列
    """
    # 计算价格变化
    delta = data.diff()

    # 分离上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 计算平均涨跌幅
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # 计算RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series,
                  n: int = 9, m1: int = 3, m2: int = 3) -> Dict[str, pd.Series]:
    """
    计算 KDJ 指标

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        n: RSV 周期
        m1: K 值平滑周期
        m2: D 值平滑周期

    Returns:
        包含 K、D、J 的字典
    """
    # 计算 RSV
    low_n = low.rolling(window=n).min()
    high_n = high.rolling(window=n).max()
    rsv = (close - low_n) / (high_n - low_n) * 100

    # 计算 K 值
    k = rsv.ewm(com=m1 - 1, adjust=False).mean()

    # 计算 D 值
    d = k.ewm(com=m2 - 1, adjust=False).mean()

    # 计算 J 值
    j = 3 * k - 2 * d

    return {
        'k': k,
        'd': d,
        'j': j
    }


def calculate_bollinger_bands(data: pd.Series, period: int = 20,
                              std_dev: float = 2.0) -> Dict[str, pd.Series]:
    """
    计算布林带

    Args:
        data: 价格序列
        period: 周期
        std_dev: 标准差倍数

    Returns:
        包含上轨、中轨、下轨的字典
    """
    # 中轨（移动平均线）
    middle = calculate_ma(data, period)

    # 标准差
    std = data.rolling(window=period).std()

    # 上轨和下轨
    upper = middle + std * std_dev
    lower = middle - std * std_dev

    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def detect_support_resistance(data: pd.DataFrame, window: int = 20) -> Dict[str, float]:
    """
    检测支撑位和阻力位

    Args:
        data: 包含 high、low 列的DataFrame
        window: 检测窗口

    Returns:
        包含支撑位和阻力位的字典
    """
    if data.empty:
        return {'support': 0, 'resistance': 0}

    # 近期最高点和最低点
    recent_high = data['high'].tail(window).max()
    recent_low = data['low'].tail(window).min()

    # 当前价格
    current_price = data['close'].iloc[-1]

    # 简单判断：近期高点作为阻力位，低点作为支撑位
    resistance = recent_high
    support = recent_low

    # 更精确的支撑阻力位计算
    # 找出近期的高点和低点
    highs = data['high'].tail(window)
    lows = data['low'].tail(window)

    # 使用分位数法
    resistance_levels = highs.quantile([0.75, 0.9, 0.95])
    support_levels = lows.quantile([0.05, 0.1, 0.25])

    # 选择最近的价格水平
    if current_price < data['close'].tail(window).median():
        # 价格偏低，选择较近的阻力位
        resistance = resistance_levels.min()
        support = support_levels.min()
    else:
        # 价格偏高，选择较近的支撑位
        resistance = resistance_levels.max()
        support = support_levels.max()

    return {
        'support': support,
        'resistance': resistance
    }


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                  period: int = 14) -> pd.Series:
    """
    计算平均真实波幅（ATR）

    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 周期

    Returns:
        ATR 序列
    """
    # 计算真实波幅
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # 计算ATR
    atr = tr.rolling(window=period).mean()

    return atr


def calculate_volume_ma(volume: pd.Series, short: int = 5, long: int = 20) -> Dict[str, pd.Series]:
    """
    计算成交量移动平均线

    Args:
        volume: 成交量序列
        short: 短期周期
        long: 长期周期

    Returns:
        包含短期和长期量均线字典
    """
    return {
        'ma_short': volume.rolling(window=short).mean(),
        'ma_long': volume.rolling(window=long).mean()
    }


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    计算能量潮（OBV）

    Args:
        close: 收盘价序列
        volume: 成交量序列

    Returns:
        OBV 序列
    """
    obv = pd.Series(index=close.index, dtype=float)
    obv.iloc[0] = volume.iloc[0]

    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i - 1]:
            obv.iloc[i] = obv.iloc[i - 1] + volume.iloc[i]
        elif close.iloc[i] < close.iloc[i - 1]:
            obv.iloc[i] = obv.iloc[i - 1] - volume.iloc[i]
        else:
            obv.iloc[i] = obv.iloc[i - 1]

    return obv


def analyze_trend_strength(data: pd.DataFrame) -> Dict[str, float]:
    """
    分析趋势强度

    Args:
        data: 包含价格数据的DataFrame

    Returns:
        趋势强度指标字典
    """
    if data.empty or len(data) < 20:
        return {'trend_strength': 0, 'direction': 'neutral'}

    close = data['close']

    # 计算均线
    ma_short = calculate_ma(close, 20)
    ma_long = calculate_ma(close, 60)

    if ma_short.iloc[-1] > ma_long.iloc[-1]:
        direction = 'bullish'
        # 多头趋势强度：短期均线偏离度
        strength = (ma_short.iloc[-1] - ma_long.iloc[-1]) / ma_long.iloc[-1]
    elif ma_short.iloc[-1] < ma_long.iloc[-1]:
        direction = 'bearish'
        # 空头趋势强度
        strength = (ma_long.iloc[-1] - ma_short.iloc[-1]) / ma_long.iloc[-1]
    else:
        direction = 'neutral'
        strength = 0

    # 成交量确认
    if len(data) >= 5:
        recent_vol = data['volume'].tail(5).mean()
        prev_vol = data['volume'].iloc[-10:-5].mean() if len(data) >= 10 else recent_vol

        if recent_vol > prev_vol:
            volume_factor = 1.2  # 成交量放大
        else:
            volume_factor = 0.8
    else:
        volume_factor = 1.0

    # 综合趋势强度（0-100）
    trend_strength = min(abs(strength) * 1000 * volume_factor, 100)

    return {
        'trend_strength': trend_strength,
        'direction': direction,
        'ma_short': ma_short.iloc[-1],
        'ma_long': ma_long.iloc[-1]
    }


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 2)

    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'volume': np.random.randint(1000000, 10000000, 100)
    })

    # 测试各种指标
    print("=== 移动平均线 ===")
    ma20 = calculate_ma(data['close'], 20)
    print(ma20.tail())

    print("\n=== MACD ===")
    macd = calculate_macd(data['close'])
    print(macd['macd'].tail())

    print("\n=== RSI ===")
    rsi = calculate_rsi(data['close'])
    print(rsi.tail())

    print("\n=== KDJ ===")
    kdj = calculate_kdj(data['high'], data['low'], data['close'])
    print(kdj['k'].tail())

    print("\n=== 趋势强度 ===")
    trend = analyze_trend_strength(data)
    print(trend)
