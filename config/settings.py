"""
AI 智能择时助手 - 配置文件
"""
import os
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Settings:
    """系统配置"""

    # ==================== 数据源配置 ====================
    # 是否使用 Tushare（需要 API Token）
    USE_TUSHARE: bool = False
    TUSHARE_TOKEN: str = os.getenv("TUSHARE_TOKEN", "")

    # ==================== AI 配置 ====================
    # 是否启用 AI 分析
    ENABLE_AI: bool = True
    # AI 服务提供商: dashscope, deepseek
    AI_PROVIDER: str = "dashscope"
    # 模型名称
    AI_MODEL: str = "qwen-plus"
    # API 密钥
    AI_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")

    # ==================== 市场配置 ====================
    # 监控的市场指数代码
    MARKET_INDEXES: List[str] = None  # 上证指数、深证成指、创业板指

    # ==================== 技术指标参数 ====================
    # 均线周期
    MA_SHORT: int = 20
    MA_LONG: int = 60
    MA_VERY_LONG: int = 120

    # RSI 参数
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0

    # MACD 参数
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9

    # KDJ 参数
    KDJ_N: int = 9
    KDJ_M1: int = 3
    KDJ_M2: int = 3

    # ==================== 择时配置 ====================
    # 买入阈值
    BUY_THRESHOLD: float = 70.0
    # 卖出阈值
    SELL_THRESHOLD: float = 30.0
    # 观望阈值
    WAIT_THRESHOLD: float = 50.0

    # ==================== 缓存配置 ====================
    # 缓存过期时间（秒）
    CACHE_TTL: int = 3600  # 1小时
    # 是否启用缓存
    ENABLE_CACHE: bool = True

    # ==================== Web 配置 ====================
    # 应用标题
    APP_TITLE: str = "AI 智能择时助手"
    # 应用图标
    APP_ICON: str = "📈"

    # ==================== 情绪分析配置 ====================
    # 情绪评分权重
    SENTIMENT_WEIGHT_MARKET_BREADTH: float = 0.35  # 市场宽度权重
    SENTIMENT_WEIGHT_MONEY_FLOW: float = 0.40  # 资金流向权重
    SENTIMENT_WEIGHT_VOLATILITY: float = 0.25  # 波动率权重

    # 市场状态阈值
    MARKET_EXTREME_GREED: float = 80.0  # 极度贪婪
    MARKET_GREED: float = 65.0  # 贪婪
    MARKET_NEUTRAL: float = 45.0  # 中性
    MARKET_FEAR: float = 30.0  # 恐慌

    # ==================== 监控配置 ====================
    # 监控更新频率（秒）
    MONITOR_UPDATE_INTERVAL: int = 300  # 5分钟
    # 是否启用实时监控
    ENABLE_REALTIME_MONITOR: bool = True
    # 监控的交易时间段（9:30-15:00）
    TRADING_HOURS_START: str = "09:30"
    TRADING_HOURS_END: str = "15:00"

    # ==================== 事件驱动配置 ====================
    # 事件热度衰减（天数）
    EVENT_DECAY_DAYS: int = 3
    # 板块情绪阈值
    SECTOR_SENTIMENT_THRESHOLD: float = 60.0
    # 板块情绪升温阈值（单日提升）
    SECTOR_SENTIMENT_RISE: float = 15.0

    # ==================== 持仓配置 ====================
    # 持仓数据存储路径
    POSITION_DATA_PATH: str = "data/positions.json"
    # 预警数据存储路径
    ALERT_DATA_PATH: str = "data/alerts.json"

    # ==================== 选股配置 ====================
    # 选股评分权重
    SELECTION_WEIGHT_SENTIMENT: float = 0.30  # 情绪得分权重
    SELECTION_WEIGHT_MONEY_FLOW: float = 0.30  # 资金流向权重
    SELECTION_WEIGHT_MARKET_CAP: float = 0.20  # 市值权重
    SELECTION_WEIGHT_ACTIVITY: float = 0.20  # 活跃度权重

    # 股票分类阈值（市值，亿元）
    STABLE_CAP_THRESHOLD: float = 500.0  # 稳定型市值阈值
    ACTIVE_CAP_THRESHOLD: float = 200.0  # 活跃型市值阈值

    # ==================== 风险偏好配置 ====================
    # 风险偏好模板
    RISK_PREFERENCES: Dict[str, Dict[str, float]] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.MARKET_INDEXES is None:
            # 默认监控上证指数、深证成指、创业板指
            self.MARKET_INDEXES = ['000001', '399001', '399006']

        # 从环境变量读取 AI 配置
        if not self.AI_API_KEY:
            self.AI_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

        # 初始化风险偏好模板
        if self.RISK_PREFERENCES is None:
            self.RISK_PREFERENCES = {
                '保守': {'stable': 0.50, 'sensitive': 0.30, 'active': 0.20},
                '稳健': {'stable': 0.30, 'sensitive': 0.40, 'active': 0.30},
                '激进': {'stable': 0.20, 'sensitive': 0.30, 'active': 0.50}
            }


# 全局配置实例
settings = Settings()
