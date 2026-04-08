"""
AI 大语言模型服务模块
集成千问/DeepSeek 进行智能分析
"""
import os
from typing import Dict, List, Optional
import dashscope
from dashscope import Generation


class LLMService:
    """大语言模型服务"""

    def __init__(self, api_key: str = None, model: str = "qwen-plus"):
        """
        初始化 LLM 服务

        Args:
            api_key: API 密钥
            model: 模型名称
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.model = model

        if self.api_key:
            dashscope.api_key = self.api_key
        else:
            print("警告: 未设置 DASHSCOPE_API_KEY，AI 功能将不可用")

    def is_available(self) -> bool:
        """
        检查服务是否可用

        Returns:
            是否可用
        """
        return bool(self.api_key)

    def analyze_timing_reason(self, stock_code: str, stock_name: str,
                             action: str, confidence: float,
                             technical_score: float, sentiment_score: float,
                             reasons: List[str]) -> str:
        """
        生成择时建议的详细解释

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            action: 操作建议
            confidence: 置信度
            technical_score: 技术面得分
            sentiment_score: 情绪面得分
            reasons: 分析原因列表

        Returns:
            AI 生成的解释文本
        """
        if not self.is_available():
            return self._fallback_explanation(action, confidence)

        prompt = f"""
作为专业投资顾问，请分析以下择时建议并给出简洁的解释：

股票：{stock_name}（{stock_code}）
操作建议：{action}
置信度：{confidence:.0f}%
技术面得分：{technical_score:.0f}/100
情绪面得分：{sentiment_score:.0f}/100

分析依据：
{chr(10).join([f'{i}. {r}' for i, r in enumerate(reasons, 1)])}

请用100-150字解释这个建议，包括：
1. 为什么给出这个建议
2. 当前的主要机会或风险
3. 投资者应该关注的要点

请保持专业、客观的语气。
"""

        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )

            if response.status_code == 200:
                return response.output.text.strip()
            else:
                print(f"AI 调用失败: {response.message}")
                return self._fallback_explanation(action, confidence)

        except Exception as e:
            print(f"AI 分析出错: {e}")
            return self._fallback_explanation(action, confidence)

    def analyze_market_regime(self, trend: str, strength: float,
                             confidence: float, index_scores: Dict[str, float],
                             reason: str) -> str:
        """
        分析市场状态

        Args:
            trend: 市场趋势
            strength: 趋势强度
            confidence: 置信度
            index_scores: 各指数得分
            reason: 判断理由

        Returns:
            AI 生成的市场分析
        """
        if not self.is_available():
            return self._fallback_market_analysis(trend, strength)

        prompt = f"""
作为专业市场分析师，请分析当前A股市场状态：

市场趋势：{trend}
趋势强度：{strength:.0%}
判断置信度：{confidence:.0%}

各指数得分：
{chr(10).join([f'{k}: {v:.0f}分' for k, v in index_scores.items()])}

分析依据：{reason}

请用150-200字分析：
1. 当前市场的主要特征
2. 各指数表现的差异
3. 投资者应该采取的策略
4. 需要关注的风险点

请保持专业、客观的语气。
"""

        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=600,
                temperature=0.7
            )

            if response.status_code == 200:
                return response.output.text.strip()
            else:
                print(f"AI 调用失败: {response.message}")
                return self._fallback_market_analysis(trend, strength)

        except Exception as e:
            print(f"AI 分析出错: {e}")
            return self._fallback_market_analysis(trend, strength)

    def generate_stock_summary(self, stock_code: str, stock_name: str,
                              current_price: float, change_pct: float,
                              action: str, technical_score: float,
                              sentiment_score: float) -> str:
        """
        生成股票分析摘要

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            current_price: 当前价格
            change_pct: 涨跌幅
            action: 操作建议
            technical_score: 技术面得分
            sentiment_score: 情绪面得分

        Returns:
            AI 生成的摘要
        """
        if not self.is_available():
            return f"{stock_name}（{stock_code}）当前价格{current_price}元，涨跌幅{change_pct:.2f}%。"

        prompt = f"""
请为以下股票生成一段简洁的分析摘要（80-100字）：

股票：{stock_name}（{stock_code}）
当前价格：{current_price}元
涨跌幅：{change_pct:.2f}%
操作建议：{action}
技术面得分：{technical_score:.0f}/100
情绪面得分：{sentiment_score:.0f}/100

请生成一段适合快速阅读的摘要，突出关键信息和投资建议。
"""

        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=300,
                temperature=0.7
            )

            if response.status_code == 200:
                return response.output.text.strip()
            else:
                return f"{stock_name}（{stock_code}）当前价格{current_price}元，涨跌幅{change_pct:.2f}%。"

        except Exception as e:
            print(f"AI 生成摘要出错: {e}")
            return f"{stock_name}（{stock_code}）当前价格{current_price}元，涨跌幅{change_pct:.2f}%。"

    def analyze_risk_factors(self, stock_code: str, stock_name: str,
                           technical_score: float, sentiment_score: float,
                           market_trend: str) -> List[str]:
        """
        分析风险因素

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            technical_score: 技术面得分
            sentiment_score: 情绪面得分
            market_trend: 市场趋势

        Returns:
            风险因素列表
        """
        if not self.is_available():
            return self._fallback_risk_factors(technical_score, sentiment_score, market_trend)

        prompt = f"""
作为风险管理专家，请分析以下投资风险因素：

股票：{stock_name}（{stock_code}）
技术面得分：{technical_score:.0f}/100
情绪面得分：{sentiment_score:.0f}/100
市场趋势：{market_trend}

请列出3-5个主要风险因素，每个用一句话概括。
格式：
1. 风险因素1
2. 风险因素2
...

请简明扼要，每条不超过20字。
"""

        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=400,
                temperature=0.7
            )

            if response.status_code == 200:
                text = response.output.text.strip()
                # 解析风险因素
                factors = []
                for line in text.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                        # 移除序号和符号
                        factor = line.lstrip('0123456789.•- ')
                        if factor:
                            factors.append(factor)
                return factors if factors else self._fallback_risk_factors(
                    technical_score, sentiment_score, market_trend
                )
            else:
                return self._fallback_risk_factors(technical_score, sentiment_score, market_trend)

        except Exception as e:
            print(f"AI 风险分析出错: {e}")
            return self._fallback_risk_factors(technical_score, sentiment_score, market_trend)

    def _fallback_explanation(self, action: str, confidence: float) -> str:
        """备用解释（AI不可用时）"""
        explanations = {
            "buy": f"建议买入（置信度{confidence:.0f}%）。技术面和情绪面均表现较好，适合逢低布局。",
            "sell": f"建议卖出（置信度{confidence:.0f}%）。技术面走弱，建议控制风险，及时止盈止损。",
            "hold": f"建议持有（置信度{confidence:.0f}%）。当前走势平稳，可继续持有观察。",
            "wait": f"建议观望（置信度{confidence:.0f}%）。信号不够明确，建议等待更好的入场时机。"
        }
        return explanations.get(action, "建议谨慎操作，注意风险控制。")

    def _fallback_market_analysis(self, trend: str, strength: float) -> str:
        """备用市场分析（AI不可用时）"""
        if trend == "bullish":
            return f"当前市场处于上升趋势，强度为{strength:.0%}。各指数表现较好，适合积极参与，但需注意控制仓位，做好风险管理。"
        elif trend == "bearish":
            return f"当前市场处于下降趋势，强度为{strength:.0%}。各指数表现疲弱，建议谨慎操作，控制仓位为主。"
        else:
            return f"当前市场处于震荡状态。方向不明朗，建议耐心等待，关注市场变化，寻找确定性机会。"

    def _fallback_risk_factors(self, technical_score: float,
                              sentiment_score: float,
                              market_trend: str) -> List[str]:
        """备用风险因素（AI不可用时）"""
        factors = []

        if technical_score < 40:
            factors.append("技术面疲弱，可能继续下跌")
        if sentiment_score < 40:
            factors.append("弱于大盘，资金关注度低")
        if market_trend == "bearish":
            factors.append("市场环境不佳，系统性风险较高")
        if technical_score > 80:
            factors.append("短期涨幅较大，注意回调风险")
        if sentiment_score > 80:
            factors.append("情绪过热，可能面临调整")

        if not factors:
            factors.append("整体风险可控，注意常规波动")

        return factors


# 测试代码
if __name__ == "__main__":
    # 注意：实际测试需要设置 DASHSCOPE_API_KEY 环境变量
    llm = LLMService()

    if llm.is_available():
        print("=== 测试择时建议解释 ===")
        explanation = llm.analyze_timing_reason(
            stock_code="600519",
            stock_name="贵州茅台",
            action="买入",
            confidence=75,
            technical_score=72,
            sentiment_score=68,
            reasons=[
                "技术面强势，多项指标向好",
                "跑赢大盘，表现强势",
                "市场处于bullish趋势，环境有利",
                "建议逢低买入，把握机会"
            ]
        )
        print(explanation)

        print("\n=== 测试市场状态分析 ===")
        market_analysis = llm.analyze_market_regime(
            trend="bullish",
            strength=0.65,
            confidence=0.78,
            index_scores={'000001': 68, '399001': 72, '399006': 75},
            reason="上证指数表现较强（68分）；深证成指表现较强（72分）；创业板指表现较强（75分）；整体市场处于上升趋势，建议把握机会"
        )
        print(market_analysis)
    else:
        print("未设置 API 密钥，跳过 AI 功能测试")
        print("\n=== 测试备用功能 ===")
        explanation = llm.analyze_timing_reason(
            stock_code="600519",
            stock_name="贵州茅台",
            action="买入",
            confidence=75,
            technical_score=72,
            sentiment_score=68,
            reasons=[]
        )
        print(explanation)
