# -*- coding: utf-8 -*-
"""
短线情绪择时助手 - Streamlit Web应用
展示Phase 1-4的成果
"""
import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入混合数据获取器
from data.hybrid_fetcher import get_hybrid_fetcher

# CMES Token配置
CMES_TOKEN = "78016cb83f5e45a6b807ecb3d708db27"

# 初始化混合数据获取器
try:
    hybrid_fetcher = get_hybrid_fetcher(CMES_TOKEN)
    data_status = hybrid_fetcher.get_status()
    DATA_SOURCE_INFO = f"数据源: {data_status['primary_source']}"
except Exception as e:
    hybrid_fetcher = None
    DATA_SOURCE_INFO = f"数据源: 初始化失败 ({e})"

# 页面配置
st.set_page_config(
    page_title="短线情绪择时助手",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    .sentiment-gauge {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
    }
    .stock-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .event-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'

# 侧边栏
with st.sidebar:
    st.title("📈 短线情绪择时助手")
    st.write("基于市场情绪+事件驱动的短线波段交易辅助系统")

    st.divider()

    # 导航菜单
    page = st.radio(
        "导航",
        ["📊 情绪仪表板", "📰 事件监控", "🎯 板块扫描", "💼 持仓配置"],
        index=0,
        label_visibility="collapsed"
    )

    # 映射页面
    page_map = {
        "📊 情绪仪表板": "dashboard",
        "📰 事件监控": "event",
        "🎯 板块扫描": "sector",
        "💼 持仓配置": "portfolio"
    }
    st.session_state.current_page = page_map[page]

    st.divider()

    # 配置选项
    st.subheader("⚙️ 设置")

    auto_refresh = st.checkbox("自动刷新", value=False)
    if auto_refresh:
        refresh_interval = st.selectbox("刷新间隔", [5, 10, 30], index=0)

    # 数据源状态
    st.caption("📡 数据源状态")
    if hybrid_fetcher:
        status = hybrid_fetcher.get_status()

        # CMES状态
        if status['cmes_available']:
            st.success("✅ CMES实时行情：已连接")
            st.caption(f"延迟: ~38ms")
        else:
            st.warning("⚠️ CMES未连接")
            st.caption("使用AkShare")

        st.caption(f"主要数据源: **{status['primary_source']}**")

        if auto_refresh:
            st.caption(f"🔄 自动刷新: {refresh_interval}秒")

        st.info(status['recommendation'])
    else:
        st.error("❌ 数据源初始化失败")
        st.caption("请联系技术支持")

    st.divider()

    # 使用说明
    st.subheader("📖 使用说明")
    st.info("""
    **功能说明：**

    1. **情绪仪表板**：查看市场整体情绪

    2. **事件监控**：分析重大事件影响

    3. **板块扫描**：发现热门板块和股票

    4. **持仓配置**：生成个性化配置方案

    **注意事项：**
    - ⚠️ 本系统只提示不操作
    - ⚠️ 用户需自主决策
    - ⚠️ 投资有风险，入市需谨慎
    """)

# 主标题
st.markdown('<h1 class="main-header">短线情绪择时助手</h1>', unsafe_allow_html=True)

# 根据选择的页面显示内容
if st.session_state.current_page == 'dashboard':
    st.title("📊 市场情绪仪表板")

    # 导入情绪分析模块
    from sentiment.sentiment_scorer import SentimentScorer

    # 计算市场情绪
    with st.spinner("正在计算市场情绪..."):
        scorer = SentimentScorer()
        sentiment = scorer.calculate_overall_sentiment()
        state_display = scorer.get_market_state_display(sentiment.market_state)

    # 显示综合情绪
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div style="font-size: 1.2rem;">市场情绪</div>
            <div class="sentiment-gauge">{state_display['emoji']}</div>
            <div style="font-size: 1.5rem;">{state_display['name']}</div>
            <div style="font-size: 2rem; margin-top: 0.5rem;">{sentiment.sentiment_score:.0f}分</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric("市场宽度", f"{sentiment.breadth_score:.0f}分",
                 delta=f"权重35%", delta_color="normal")
        st.write(f"说明：涨跌家数比、涨跌停比")

    with col3:
        st.metric("资金流向", f"{sentiment.money_flow_score:.0f}分",
                 delta=f"权重40%", delta_color="normal")
        st.write(f"说明：北向资金、主力资金")

    st.divider()

    # 波动率
    col1, col2 = st.columns(2)
    with col1:
        st.metric("波动率", f"{sentiment.volatility_score:.0f}分",
                 delta=f"权重25%", delta_color="normal")
        st.write(f"说明：历史波动率、波动百分位")

    with col2:
        st.info(f"""
        **操作建议**

        {state_display['description']}

        **建议行动**：{state_display['action']}
        """)

    st.divider()

    # 热门板块
    st.subheader("🔥 热门板块")
    from sentiment.sector_sentiment import SectorSentimentAnalyzer
    sector_analyzer = SectorSentimentAnalyzer()
    hot_sectors = sector_analyzer.get_hot_sectors(top_n=5)

    if hot_sectors:
        cols = st.columns(5)
        for i, sector in enumerate(hot_sectors):
            with cols[i]:
                st.metric(
                    sector['name'],
                    f"{sector['score']:.0f}分",
                    delta=f"{sector['change_pct']:+.1f}%"
                )

    st.divider()

    # 详细数据
    with st.expander("📋 查看详细数据"):
        st.write("**情绪构成分析**")

        components_data = {
            '指标': ['市场宽度', '资金流向', '波动率'],
            '得分': [sentiment.breadth_score, sentiment.money_flow_score, sentiment.volatility_score],
            '权重': [35, 40, 25],
            '贡献': [
                sentiment.breadth_score * 0.35,
                sentiment.money_flow_score * 0.40,
                sentiment.volatility_score * 0.25
            ]
        }
        st.write(pd.DataFrame(components_data))

        st.write("**所有板块情绪**")
        all_sectors = sector_analyzer.get_all_sectors_sentiment()
        if not all_sectors.empty:
            st.dataframe(all_sectors, use_container_width=True)

elif st.session_state.current_page == 'event':
    st.title("📰 事件监控面板")

    # 事件输入
    col1, col2 = st.columns([3, 1])
    with col1:
        event_keyword = st.text_input(
            "输入事件关键词",
            value="降息",
            help="例如：降息、地缘冲突、AI突破等"
        )
    with col2:
        st.write("")
        st.write("")
        analyze_btn = st.button("🔍 分析事件", type="primary")

    if analyze_btn or event_keyword:
        from news.event_analyzer import EventAnalyzer

        with st.spinner(f"正在分析事件：{event_keyword}..."):
            analyzer = EventAnalyzer()
            analysis = analyzer.analyze_event(event_keyword, days=7)

        # 显示事件分析结果
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("事件类型", analysis.event_type)

        with col2:
            st.metric("情绪倾向", analysis.sentiment.upper())

        with col3:
            st.metric("相关新闻", f"{analysis.news_count}条")

        st.divider()

        # 影响板块
        st.subheader("📊 影响板块分析")

        if analysis.affected_sectors:
            bullish = [k for k, v in analysis.affected_sectors.items() if v == '利好']
            bearish = [k for k, v in analysis.affected_sectors.items() if v == '利空']
            neutral = [k for k, v in analysis.affected_sectors.items() if v == '中性']

            col1, col2, col3 = st.columns(3)

            with col1:
                if bullish:
                    st.success(f"**利好板块** ({len(bullish)})")
                    for sector in bullish:
                        score = analysis.current_sentiment_scores.get(sector, 50)
                        st.write(f"- {sector}: {score:.0f}分")

            with col2:
                if bearish:
                    st.error(f"**利空板块** ({len(bearish)})")
                    for sector in bearish:
                        score = analysis.current_sentiment_scores.get(sector, 50)
                        st.write(f"- {sector}: {score:.0f}分")

            with col3:
                if neutral:
                    st.info(f"**中性板块** ({len(neutral)})")
                    for sector in neutral:
                        score = analysis.current_sentiment_scores.get(sector, 50)
                        st.write(f"- {sector}: {score:.0f}分")

        st.divider()

        # 操作建议
        st.subheader("💡 操作建议")
        st.markdown(f"""
        <div class="event-card">
            {analysis.recommendation.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # 相关新闻
        if analysis.latest_news:
            st.subheader("📰 相关新闻")
            for i, news in enumerate(analysis.latest_news[:5], 1):
                st.write(f"{i}. **{news['title']}**")
                st.caption(f"来源: {news['source']} | 时间: {news['date']}")
                st.divider()

elif st.session_state.current_page == 'sector':
    st.title("🎯 板块扫描")

    # 板块选择
    col1, col2 = st.columns([2, 1])
    with col1:
        sector_name = st.selectbox(
            "选择板块",
            ['军工', '半导体', '新能源', '医药', '消费', '银行',
             '地产', '煤炭', '石油', '黄金', 'AI', '软件', '传媒']
        )
    with col2:
        st.write("")
        st.write("")
        top_n = st.number_input("选股数量", min_value=3, max_value=10, value=5)

    # 扫描按钮
    if st.button("🔍 开始扫描", type="primary"):
        from selector.stock_selector import StockSelector
        from sentiment.sector_sentiment import SectorSentimentAnalyzer

        # 分析板块情绪
        with st.spinner(f"正在扫描{sector_name}板块..."):
            sector_analyzer = SectorSentimentAnalyzer()
            sector_sentiment = sector_analyzer.calculate_sector_sentiment(sector_name)

        # 显示板块情绪
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("板块情绪", f"{sector_sentiment['sentiment_score']:.0f}分")

        with col2:
            st.metric("涨跌幅", f"{sector_sentiment['metrics']['change_pct']:.2f}%")

        with col3:
            st.metric("上涨家数", f"{sector_sentiment['metrics']['rising_stocks']}/"
                     f"{sector_sentiment['metrics']['total_stocks']}")

        st.divider()

        # 选股
        st.subheader(f"📊 {sector_name}板块 Top {top_n}")

        selector = StockSelector()
        stocks = selector.select_representative_stocks(sector_name, top_n=top_n)

        if stocks:
            # 使用混合数据获取器获取实时价格
            if hybrid_fetcher:
                try:
                    symbols = [s['code'] for s in stocks]
                    realtime_data = hybrid_fetcher.get_realtime_quotes(symbols)

                    # 更新实时价格
                    for stock in stocks:
                        if stock['code'] in realtime_data:
                            stock['price'] = realtime_data[stock['code']]['price']
                            stock['change_pct'] = realtime_data[stock['code']]['change_pct']
                            stock['data_source'] = realtime_data[stock['code']]['data_source']
                except Exception as e:
                    st.caption(f"⚠️ 实时价格获取失败: {e}")

            for i, stock in enumerate(stocks, 1):
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1, 1, 1])

                    with col1:
                        st.write(f"**#{i}**")

                    with col2:
                        # 显示数据来源标签
                        source_tag = f"🔴 实时" if stock.get('data_source') == 'CMES' else "⚡ 延迟"
                        st.write(f"**{stock['code']} {stock['name']}** {source_tag}")
                        st.caption(f"类型: {stock['type']}")

                    with col3:
                        st.metric("得分", f"{stock['score']:.0f}")

                    with col4:
                        st.metric("价格", f"{stock['price']:.2f}")

                    with col5:
                        change_color = "🔴" if stock['change_pct'] < 0 else "🟢"
                        st.write(f"{change_color} {stock['change_pct']:+.2f}%")

                    with col6:
                        if stock.get('data_source'):
                            st.caption(f"数据源: {stock['data_source']}")

                    st.write(f"*市值: {stock['market_cap']:.0f}亿 | "
                            f"换手: {stock['turnover']:.1f}%*")

                    st.divider()

            # 显示评分详情
            with st.expander("📋 评分详情"):
                scores_data = {
                    '股票': [f"{s['code']} {s['name']}" for s in stocks],
                    '总分': [s['score'] for s in stocks],
                    '情绪分': [s['sentiment_score'] for s in stocks],
                    '资金分': [s['flow_score'] for s in stocks],
                    '市值分': [s['cap_score'] for s in stocks],
                    '活跃分': [s['activity_score'] for s in stocks]
                }
                st.write(pd.DataFrame(scores_data))
        else:
            st.warning("未找到符合条件的股票")

elif st.session_state.current_page == 'portfolio':
    st.title("💼 持仓配置生成")

    # 输入参数
    col1, col2, col3 = st.columns(3)

    with col1:
        sector_name = st.selectbox(
            "选择板块",
            ['军工', '半导体', '新能源', '医药', '消费', '银行'],
            key='portfolio_sector'
        )

    with col2:
        total_capital = st.number_input(
            "投资金额(元)",
            min_value=10000,
            max_value=10000000,
            value=100000,
            step=10000
        )

    with col3:
        risk_preference = st.selectbox(
            "风险偏好",
            ['保守', '稳健', '激进'],
            key='portfolio_risk'
        )

    # 生成配置按钮
    if st.button("🎯 生成配置方案", type="primary"):
        from selector.stock_selector import StockSelector
        from selector.allocation import AllocationGenerator
        from selector.stop_loss_plans import StopLossPlansGenerator

        with st.spinner("正在生成配置方案..."):
            # 选股
            selector = StockSelector()
            stocks = selector.select_representative_stocks(sector_name, top_n=5)

            if not stocks:
                st.error("未找到符合条件的股票")
                st.stop()

            # 生成配置
            allocator = AllocationGenerator()
            allocation = allocator.generate_allocation(
                total_capital, risk_preference, stocks
            )

        # 显示配置摘要
        st.subheader("📊 配置摘要")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("总资金", f"{allocation['total_capital']:,.0f}元")

        with col2:
            st.metric("风险偏好", allocation['risk_preference'])

        with col3:
            actual_capital = sum(p['capital'] for p in allocation['positions'])
            st.metric("实际配置", f"{actual_capital:,.0f}元")

        st.divider()

        # 显示配置比例
        st.subheader("⚖️ 配置比例")

        weights = allocation['weights']
        type_names = {
            'stable': '稳定型(大市值防守)',
            'sensitive': '敏感型(中等市值弹性)',
            'active': '活跃型(小市值进攻)'
        }

        for type_key, weight in weights.items():
            capital = allocation['total_capital'] * weight
            st.write(f"- **{type_names[type_key]}**: {weight*100:.0f}% ({capital:,.0f}元)")

        st.divider()

        # 显示持仓明细
        st.subheader("📋 持仓明细")

        for i, pos in enumerate(allocation['positions'], 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

                with col1:
                    st.write(f"**#{i} {pos['code']} {pos['name']}**")
                    st.caption(f"类型: {pos['type']}")

                with col2:
                    st.metric("股数", f"{pos['shares']}股")

                with col3:
                    st.metric("金额", f"{pos['capital']:,.0f}元")

                with col4:
                    st.metric("价格", f"{pos['price']:.2f}元")

                st.info(f"💡 {pos['reason']}")

                st.divider()

        # 止损方案
        st.subheader("🛡️ 止损方案示例")

        if stocks:
            sample_stock = stocks[0]
            plan_gen = StopLossPlansGenerator()
            plans = plan_gen.generate_plans_for_stock(
                sample_stock['code'], sample_stock['price']
            )

            selected_plan = plan_gen.select_plan_by_risk(
                plans, risk_preference
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("方案", selected_plan.name)

            with col2:
                st.metric("止损价", f"{selected_plan.stop_loss_price:.2f}元")

            with col3:
                st.metric("止盈价", f"{selected_plan.take_profit_price:.2f}元")

            with col4:
                st.metric("历史胜率", f"{selected_plan.historical_win_rate}%")

            with st.expander("📋 查看全部方案"):
                for plan_name in ['保守型', '稳健型', '激进型']:
                    if plan_name in plans:
                        plan = plans[plan_name]
                        st.write(f"""
                        **{plan_name}**:
                        - 止损: {plan.stop_loss_price:.2f}元
                        - 止盈: {plan.take_profit_price:.2f}元
                        - 胜率: {plan.historical_win_rate}%
                        - 盈亏比: {plan.profit_loss_ratio}:1
                        """)
                        st.divider()

# 页脚
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;'>
    ⚠️ <strong>免责声明</strong>：本系统仅供参考，不构成投资建议。
    <br>用户需自主决策，控制风险。投资有风险，入市需谨慎。
    <br><br>
    📊 短线情绪择时助手 v1.0 | 基于 Phase 1-4 实现
</div>
""", unsafe_allow_html=True)
