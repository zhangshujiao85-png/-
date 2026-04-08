# -*- coding: utf-8 -*-
"""
先行指标分析
分析A50期货美股中概股亚太市场等先行指标
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


@dataclass
class LeadingIndicator:
    """先行指标数据"""
    name: str
    code: str
    current_price: float
    change_pct: float
    timestamp: str
    significance: str  # high/medium/low


@dataclass
class PreMarketAlert:
    """盘前预警"""
    level: str  # CRITICAL/WARNING/INFO
    message: str
    indicators: List[LeadingIndicator]
    suggestion: str
    timestamp: str


class LeadingIndicatorAnalyzer:
    """先行指标分析器

    功能
    1. A50期货监控
    2. 美股中概股监控
    3. 亚太市场监控
    4. 生成盘前预警报告
    """

    def __init__(self):
        """初始化"""
        # 先行指标定义
        self.a50_future = {
            'name': 'A50期货',
            'code': 'CNXH',  # 新加坡A50期货
            'significance': 'high'
        }

        self.us_chinese_stocks = {
            'name': '美股中概股',
            'indices': {
                '中概股指数': 'KWEB',
                '纳斯达克中国金龙指数': 'HXC',
                '阿里巴巴': 'BABA',
                '京东': 'JD',
                '拼多多': 'PDD',
                '百度': 'BIDU',
                '网易': 'NTES'
            },
            'significance': 'high'
        }

        self.asia_markets = {
            'name': '亚太市场',
            'markets': {
                '日经225': 'NKY',
                '韩国KOSPI': 'KOSPI',
                '恒生指数': 'HSI',
                '台湾加权': 'TWII'
            },
            'significance': 'medium'
        }

        print("[先行指标] 分析器初始化完成")

    def analyze_a50_future(self) -> Optional[LeadingIndicator]:
        """
        分析A50期货

        Returns:
            A50期货指标数据
        """
        try:
            # 这里应该连接实时数据源
            # 由于没有真实数据源使用模拟数据

            np.random.seed(int(datetime.now().timestamp()))
            change_pct = np.random.uniform(-3, 3)
            current_price = 13000 + np.random.uniform(-200, 200)

            indicator = LeadingIndicator(
                name=self.a50_future['name'],
                code=self.a50_future['code'],
                current_price=round(current_price, 2),
                change_pct=round(change_pct, 2),
                timestamp=datetime.now().isoformat(),
                significance=self.a50_future['significance']
            )

            print(f"[先行指标] A50期货: {change_pct:+.2f}%")

            return indicator

        except Exception as e:
            print(f"[先行指标] 获取A50期货失败: {e}")
            return None

    def analyze_us_chinese_stocks(self) -> List[LeadingIndicator]:
        """
        分析美股中概股

        Returns:
            中概股指标数据列表
        """
        indicators = []

        try:
            # 模拟数据
            np.random.seed(int(datetime.now().timestamp()))

            for name, code in self.us_chinese_stocks['indices'].items():
                change_pct = np.random.uniform(-5, 5)
                current_price = np.random.uniform(50, 200)

                indicator = LeadingIndicator(
                    name=name,
                    code=code,
                    current_price=round(current_price, 2),
                    change_pct=round(change_pct, 2),
                    timestamp=datetime.now().isoformat(),
                    significance='medium'
                )
                indicators.append(indicator)

            # 计算平均涨跌幅
            avg_change = np.mean([ind.change_pct for ind in indicators])
            print(f"[先行指标] 美股中概股平均: {avg_change:+.2f}%")

            return indicators

        except Exception as e:
            print(f"[先行指标] 获取美股中概股失败: {e}")
            return []

    def analyze_asia_markets(self) -> List[LeadingIndicator]:
        """
        分析亚太市场

        Returns:
            亚太市场指标数据列表
        """
        indicators = []

        try:
            # 模拟数据
            np.random.seed(int(datetime.now().timestamp()) + 1)

            for name, code in self.asia_markets['markets'].items():
                change_pct = np.random.uniform(-3, 3)
                current_price = np.random.uniform(15000, 30000)

                indicator = LeadingIndicator(
                    name=name,
                    code=code,
                    current_price=round(current_price, 2),
                    change_pct=round(change_pct, 2),
                    timestamp=datetime.now().isoformat(),
                    significance='medium'
                )
                indicators.append(indicator)

            avg_change = np.mean([ind.change_pct for ind in indicators])
            print(f"[先行指标] 亚太市场平均: {avg_change:+.2f}%")

            return indicators

        except Exception as e:
            print(f"[先行指标] 获取亚太市场失败: {e}")
            return []

    def generate_pre_market_alert(self) -> PreMarketAlert:
        """
        生成盘前预警

        Returns:
            盘前预警对象
        """
        all_indicators = []

        # 1. A50期货
        a50 = self.analyze_a50_future()
        if a50:
            all_indicators.append(a50)

        # 2. 美股中概股
        us_stocks = self.analyze_us_chinese_stocks()
        all_indicators.extend(us_stocks)

        # 3. 亚太市场
        asia_markets = self.analyze_asia_markets()
        all_indicators.extend(asia_markets)

        # 计算整体情绪
        if not all_indicators:
            return self._create_info_alert("无先行指标数据", [])

        # 计算加权平均涨跌幅
        weighted_changes = []
        weights = []

        for ind in all_indicators:
            if ind.significance == 'high':
                weight = 2.0
            elif ind.significance == 'medium':
                weight = 1.0
            else:
                weight = 0.5

            weighted_changes.append(ind.change_pct * weight)
            weights.append(weight)

        overall_change = np.sum(weighted_changes) / np.sum(weights) if weights else 0

        # 判断预警级别
        if overall_change <= -2:
            return self._create_critical_alert(overall_change, all_indicators)
        elif overall_change <= -1:
            return self._create_warning_alert(overall_change, all_indicators)
        elif overall_change >= 2:
            return self._create_positive_alert(overall_change, all_indicators)
        else:
            return self._create_info_alert("市场情绪平稳", all_indicators)

    def _create_critical_alert(self, change: float, indicators: List[LeadingIndicator]) -> PreMarketAlert:
        """创建严重预警大跌"""
        message = f" 盘前预警先行指标大跌 {change:.2f}%预计A股低开"

        # 分析具体影响
        details = []
        for ind in indicators:
            if ind.change_pct < -2:
                details.append(f"{ind.name}大跌{ind.change_pct:.2f}%")

        if details:
            message += "\n" + "".join(details)

        suggestion = (
            "建议操作\n"
            "1. 持币观望等待市场企稳\n"
            "2. 不宜追涨杀跌\n"
            "3. 关注开盘后市场反应"
        )

        return PreMarketAlert(
            level='CRITICAL',
            message=message,
            indicators=indicators,
            suggestion=suggestion,
            timestamp=datetime.now().isoformat()
        )

    def _create_warning_alert(self, change: float, indicators: List[LeadingIndicator]) -> PreMarketAlert:
        """创建警告预警下跌"""
        message = f" 盘前提醒先行指标下跌 {change:.2f}%A股可能承压"

        suggestion = (
            "建议操作\n"
            "1. 谨慎开仓控制仓位\n"
            "2. 关注抗跌板块\n"
            "3. 等待明确的企稳信号"
        )

        return PreMarketAlert(
            level='WARNING',
            message=message,
            indicators=indicators,
            suggestion=suggestion,
            timestamp=datetime.now().isoformat()
        )

    def _create_positive_alert(self, change: float, indicators: List[LeadingIndicator]) -> PreMarketAlert:
        """创建积极预警上涨"""
        message = f" 盘前利好先行指标上涨 {change:.2f}%A股有望高开"

        suggestion = (
            "建议操作\n"
            "1. 可适当参与热门板块\n"
            "2. 注意追高风险\n"
            "3. 及时止盈"
        )

        return PreMarketAlert(
            level='INFO',
            message=message,
            indicators=indicators,
            suggestion=suggestion,
            timestamp=datetime.now().isoformat()
        )

    def _create_info_alert(self, message: str, indicators: List[LeadingIndicator]) -> PreMarketAlert:
        """创建信息提示"""
        suggestion = (
            "建议操作\n"
            "1. 正常交易关注板块轮动\n"
            "2. 严格执行止盈止损\n"
            "3. 理性投资控制风险"
        )

        return PreMarketAlert(
            level='INFO',
            message=message,
            indicators=indicators,
            suggestion=suggestion,
            timestamp=datetime.now().isoformat()
        )

    def format_alert_report(self, alert: PreMarketAlert) -> str:
        """
        格式化预警报告

        Args:
            alert: 预警对象

        Returns:
            格式化的报告文本
        """
        report = f"""
{'='*60}
 盘前先行指标分析报告
{'='*60}
时间: {datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}

预警级别{' ' + alert.level if alert.level == 'CRITICAL' else ' ' + alert.level if alert.level == 'WARNING' else ' ' + alert.level}

预警信息
{alert.message}

先行指标详情
"""

        for ind in alert.indicators:
            emoji = "" if ind.change_pct < -2 else "" if ind.change_pct < 0 else ""
            report += f"{emoji} {ind.name}: {ind.change_pct:+.2f}%\n"

        report += f"""
操作建议
{alert.suggestion}

{'='*60}
"""
        return report


# 测试代码
if __name__ == '__main__':
    analyzer = LeadingIndicatorAnalyzer()

    # 生成盘前预警
    alert = analyzer.generate_pre_market_alert()

    # 打印报告
    print(analyzer.format_alert_report(alert))

    # 测试单独分析
    print("\n单独测试:")
    a50 = analyzer.analyze_a50_future()
    if a50:
        print(f"A50期货: {a50.change_pct:+.2f}%")

    us_stocks = analyzer.analyze_us_chinese_stocks()
    print(f"美股中概股数量: {len(us_stocks)}")

    asia_markets = analyzer.analyze_asia_markets()
    print(f"亚太市场数量: {len(asia_markets)}")
