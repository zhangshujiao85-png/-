"""
AI 智能择时助手 - Streamlit Web 应用
"""
import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis.market_regime import MarketRegimeAnalyzer
from analysis.timing_analyzer import TimingAnalyzer

# Optional AI module
try:
    from ai.llm_service import LLMService
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    LLMService = None

from output.report_generator import ReportGenerator
from config.settings import settings

# 页面配置
st.set_page_config(
    page_title="AI 智能择时助手",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'market_regime' not in st.session_state:
    st.session_state.market_regime = None
if 'timing_signal' not in st.session_state:
    st.session_state.timing_signal = None

# 侧边栏
with st.sidebar:
    st.title("🤖 AI 智能择时助手")
    st.write("基于技术分析和市场情绪的择时工具")

    st.divider()

    # AI 功能开关
    enable_ai = st.checkbox("启用 AI 分析", value=settings.ENABLE_AI and AI_AVAILABLE)
    if enable_ai and not AI_AVAILABLE:
        st.warning("AI 模块未安装（需要 dashscope），AI 功能将不可用")
    elif enable_ai and not settings.AI_API_KEY:
        st.warning("未检测到 DASHSCOPE_API_KEY，AI 功能将不可用")

    st.divider()

    # 输入股票代码
    st.subheader("个股分析")
    stock_code = st.text_input(
        "股票代码",
        value="600519",
        help="输入 6 位股票代码，如 600519（贵州茅台）",
        max_chars=6
    )

    # 批量分析
    st.subheader("批量分析")
    batch_codes = st.text_area(
        "股票代码列表（每行一个）",
        value="600519\n000858\n600036",
        help="每行输入一个 6 位股票代码",
        height=150
    )

    st.divider()

    # 分析按钮
    if st.button("🔍 开始分析", type="primary", use_container_width=True):
        st.session_state.analyzed = True
        st.rerun()

    if st.button("🔄 重置", use_container_width=True):
        st.session_state.analyzed = False
        st.session_state.market_regime = None
        st.session_state.timing_signal = None
        st.rerun()

    st.divider()

    # 使用说明
    st.subheader("📖 使用说明")
    st.info("""
    **功能说明：**

    1. **市场状态**：自动分析大盘趋势

    2. **个股分析**：输入股票代码获取择时建议

    3. **批量分析**：一次分析多只股票

    **注意事项：**
    - 仅供参考，不构成投资建议
    - 投资有风险，入市需谨慎
    """)

# 主界面
st.title("📊 AI 智能择时助手")

# 标签页
tab1, tab2, tab3 = st.tabs(["📊 市场状态", "🎯 个股分析", "📋 批量分析"])

with tab1:
    st.title("市场趋势分析")

    # 分析市场状态
    with st.spinner("正在分析市场状态..."):
        try:
            regime_analyzer = MarketRegimeAnalyzer()
            market_regime = regime_analyzer.analyze(settings.MARKET_INDEXES)
            st.session_state.market_regime = market_regime
        except Exception as e:
            st.error(f"分析失败: {e}")
            st.stop()

    # 显示市场状态
    trend_emoji = {
        "bullish": "🟢",
        "bearish": "🔴",
        "neutral": "🟡"
    }

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "市场趋势",
            f"{trend_emoji[market_regime.trend.value]} {market_regime.trend.value.upper()}",
            f"强度: {market_regime.strength:.0%}"
        )

    with col2:
        st.metric("判断置信度", f"{market_regime.confidence:.0%}")

    with col3:
        st.metric("建议仓位", market_regime.position_advice)

    with col4:
        st.info(market_regime.reason)

    st.divider()

    # 各指数得分
    st.subheader("各指数得分")
    if market_regime.index_scores:
        index_cols = st.columns(len(market_regime.index_scores))

        for i, (code, score) in enumerate(market_regime.index_scores.items()):
            with index_cols[i]:
                index_name = {
                    '000001': '上证指数',
                    '399001': '深证成指',
                    '399006': '创业板指'
                }.get(code, code)

                # 根据得分设置颜色
                if score >= 60:
                    delta = "强势"
                elif score <= 40:
                    delta = "弱势"
                else:
                    delta = "中性"

                st.metric(index_name, f"{score:.0f}分", delta)
    else:
        st.info("暂无指数数据")

    st.divider()

    # AI 分析
    if enable_ai and AI_AVAILABLE and settings.AI_API_KEY:
        st.subheader("🤖 AI 深度分析")

        try:
            llm_service = LLMService(api_key=settings.AI_API_KEY)
            ai_analysis = llm_service.analyze_market_regime(
                trend=market_regime.trend.value,
                strength=market_regime.strength,
                confidence=market_regime.confidence,
                index_scores=market_regime.index_scores,
                reason=market_regime.reason
            )

            st.markdown(f"<div class='info-box'>{ai_analysis}</div>",
                       unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"AI 分析失败: {e}")

with tab2:
    st.title("个股择时分析")

    if not st.session_state.analyzed:
        st.info("👈 请在左侧输入股票代码并点击分析按钮")
    else:
        # 获取股票代码
        code = stock_code.strip()

        if not code or len(code) != 6:
            st.error("请输入有效的 6 位股票代码")
            st.stop()

        # 分析个股
        with st.spinner(f"正在分析 {code}..."):
            try:
                # 获取市场状态
                if st.session_state.market_regime is None:
                    regime_analyzer = MarketRegimeAnalyzer()
                    market_regime = regime_analyzer.analyze(settings.MARKET_INDEXES)
                else:
                    market_regime = st.session_state.market_regime

                # 分析个股
                timing_analyzer = TimingAnalyzer()
                signal = timing_analyzer.analyze(code, market_regime)
                st.session_state.timing_signal = signal

            except Exception as e:
                st.error(f"分析失败: {e}")
                st.stop()

        # 显示结果
        action_emoji = {
            "buy": "✅ 买入",
            "hold": "⏸️ 持有",
            "sell": "❌ 卖出",
            "wait": "⏳ 观望"
        }

        action_color = {
            "buy": "success",
            "hold": "warning",
            "sell": "error",
            "wait": "info"
        }

        # 操作建议
        action_type = signal.action.value
        st.markdown(f"<div class='{action_color[action_type]}-box'>",
                   unsafe_allow_html=True)
        st.success(f"### {action_emoji[action_type]}")
        st.write(f"**置信度**: {signal.confidence:.0f}%")
        st.markdown("</div>", unsafe_allow_html=True)

        # 价格信息
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("当前价格", f"{signal.current_price:.2f} 元")

        with col2:
            st.metric("目标价位", f"{signal.price_target:.2f} 元")

        with col3:
            st.metric("止损价位", f"{signal.stop_loss:.2f} 元")

        st.divider()

        # 评分情况
        col1, col2 = st.columns(2)

        with col1:
            st.write("**技术面分析**")
            progress = signal.technical_score
            st.progress(progress / 100)
            st.caption(f"得分: {progress:.0f}/100")

        with col2:
            st.write("**相对强弱**")
            progress = signal.sentiment_score
            st.progress(progress / 100)
            st.caption(f"得分: {progress:.0f}/100")

        st.divider()

        # 分析理由
        st.subheader("分析理由")
        for i, reason in enumerate(signal.reasons, 1):
            st.write(f"{i}. {reason}")

        st.divider()

        # AI 分析
        if enable_ai and settings.AI_API_KEY:
            st.subheader("🤖 AI 深度解释")

            try:
                llm_service = LLMService(api_key=settings.AI_API_KEY)

                # 获取股票名称
                from data.market_data import MarketDataFetcher
                fetcher = MarketDataFetcher()
                quote = fetcher.get_stock_quote(code)
                stock_name = quote.get('name', code) if quote else code

                ai_explanation = llm_service.analyze_timing_reason(
                    stock_code=code,
                    stock_name=stock_name,
                    action=signal.action.value,
                    confidence=signal.confidence,
                    technical_score=signal.technical_score,
                    sentiment_score=signal.sentiment_score,
                    reasons=signal.reasons
                )

                st.markdown(f"<div class='info-box'>{ai_explanation}</div>",
                           unsafe_allow_html=True)

            except Exception as e:
                st.warning(f"AI 分析失败: {e}")

with tab3:
    st.title("批量分析")

    # 解析股票代码
    codes = [c.strip() for c in batch_codes.split('\n') if c.strip()]

    if not codes:
        st.info("👈 请在左侧输入股票代码列表")
    else:
        st.write(f"准备分析 {len(codes)} 只股票...")

        # 分析按钮
        if st.button("🚀 开始批量分析", type="primary"):
            # 获取市场状态
            if st.session_state.market_regime is None:
                with st.spinner("正在分析市场状态..."):
                    regime_analyzer = MarketRegimeAnalyzer()
                    market_regime = regime_analyzer.analyze(settings.MARKET_INDEXES)
                    st.session_state.market_regime = market_regime
            else:
                market_regime = st.session_state.market_regime

            # 分析结果
            results = []
            progress_bar = st.progress(0)

            for i, code in enumerate(codes):
                with st.spinner(f"正在分析 {code}..."):
                    try:
                        timing_analyzer = TimingAnalyzer()
                        signal = timing_analyzer.analyze(code, market_regime)

                        results.append({
                            'code': code,
                            'action': signal.action.value,
                            'confidence': signal.confidence,
                            'current_price': signal.current_price,
                            'price_target': signal.price_target,
                            'stop_loss': signal.stop_loss,
                            'technical_score': signal.technical_score,
                            'sentiment_score': signal.sentiment_score
                        })

                    except Exception as e:
                        st.warning(f"{code} 分析失败: {e}")
                        results.append({
                            'code': code,
                            'action': 'error',
                            'error': str(e)
                        })

                progress_bar.progress((i + 1) / len(codes))

            # 显示结果
            st.divider()
            st.subheader("分析结果")

            # 转换为 DataFrame
            import pandas as pd
            df = pd.DataFrame(results)

            # 操作建议映射
            action_map = {
                'buy': '✅ 买入',
                'sell': '❌ 卖出',
                'hold': '⏸️ 持有',
                'wait': '⏳ 观望',
                'error': '❌ 失败'
            }
            df['操作建议'] = df['action'].map(action_map)

            # 显示表格
            display_columns = ['code', '操作建议', 'confidence',
                             'current_price', 'price_target', 'stop_loss']
            df_display = df[display_columns].copy()
            df_display.columns = ['股票代码', '操作建议', '置信度',
                                 '当前价格', '目标价位', '止损价位']

            st.dataframe(df_display, use_container_width=True)

            # 下载按钮
            csv = df_display.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载分析结果",
                data=csv,
                file_name=f"timing_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# 页脚
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    ⚠️ 免责声明：本工具仅供参考，不构成投资建议。投资有风险，入市需谨慎。
</div>
""", unsafe_allow_html=True)
