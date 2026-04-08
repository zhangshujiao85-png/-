# -*- coding: utf-8 -*-
"""
短线情绪择时助手 - 完整版Web应用
集成Phase 1-6的所有功能
"""
import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import time as tm

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
    .alert-critical {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-info {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 300  # 5分钟

# 侧边栏
with st.sidebar:
    st.title("📈 短线情绪择时助手")
    st.write("基于市场情绪+事件驱动的短线波段交易辅助系统")

    st.divider()

    # 导航菜单
    page = st.radio(
        "导航",
        ["📊 情绪仪表板", "📰 事件监控", "🎯 板块扫描", "💼 持仓配置", "⏰ 实时监控", "🔔 预警中心"],
        index=0,
        label_visibility="collapsed"
    )

    # 映射页面
    page_map = {
        "📊 情绪仪表板": "dashboard",
        "📰 事件监控": "event",
        "🎯 板块扫描": "sector",
        "💼 持仓配置": "portfolio_config",
        "⏰ 实时监控": "monitor",
        "🔔 预警中心": "alerts"
    }
    st.session_state.current_page = page_map[page]

    st.divider()

    # 自动刷新设置
    st.subheader("⚙️ 设置")
    st.session_state.auto_refresh = st.checkbox("自动刷新", value=False)
    if st.session_state.auto_refresh:
        st.session_state.refresh_interval = st.selectbox(
            "刷新间隔",
            [60, 300, 600],
            index=1
        )

    st.divider()

    # 使用说明
    st.subheader("📖 使用说明")
    st.info("""
    **功能说明：**

    1. **情绪仪表板**：查看市场整体情绪

    2. **事件监控**：分析重大事件影响

    3. **板块扫描**：发现热门板块和股票

    4. **持仓配置**：生成个性化配置方案

    5. **实时监控**：监控持仓和市场

    6. **预警中心**：查看所有预警信息

    **注意事项：**
    - ⚠️ 本系统只提示不操作
    - ⚠️ 用户需自主决策
    - ⚠️ 投资有风险，入市需谨慎
    """)

# 主标题
st.markdown('<h1 class="main-header">短线情绪择时助手</h1>', unsafe_allow_html=True)

# ==================== 页面内容 ====================

# 1. 情绪仪表板
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
            st.dataframe(all_sectors, width='stretch')

# 2. 事件监控
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

# 3. 板块扫描
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
        from data.cmes_market_data import get_cmes_market_data

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
            # 使用CMES获取实时价格
            cmes_fetcher = get_cmes_market_data()
            symbols = [s['code'] for s in stocks]

            try:
                realtime_data = cmes_fetcher.cmes.get_realtime_quotes(symbols)

                # 更新实时价格
                for stock in stocks:
                    if stock['code'] in realtime_data:
                        stock['price'] = realtime_data[stock['code']]['price']
                        stock['change_pct'] = realtime_data[stock['code']]['change_pct']
            except Exception as e:
                st.caption(f"⚠️ 实时价格获取失败: {e}")

            for i, stock in enumerate(stocks, 1):
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])

                    with col1:
                        st.write(f"**#{i}**")

                    with col2:
                        st.write(f"**{stock['code']} {stock['name']}**")
                        st.caption(f"类型: {stock['type']}")

                    with col3:
                        st.metric("得分", f"{stock['score']:.0f}")

                    with col4:
                        st.metric("价格", f"{stock['price']:.2f}")

                    with col5:
                        change_color = "🔴" if stock['change_pct'] < 0 else "🟢"
                        st.write(f"{change_color} {stock['change_pct']:+.2f}%")

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

# 4. 持仓配置
elif st.session_state.current_page == 'portfolio_config':
    st.title("💼 持仓配置生成")

    # 输入参数
    col1, col2, col3 = st.columns(3)

    with col1:
        sector_name = st.selectbox(
            "选择板块",
            ['军工', '半导体', '新能源', '医药', '消费', '银行'],
            key='config_sector'
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
            key='config_risk'
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

# 5. 实时监控
elif st.session_state.current_page == 'monitor':
    st.title("⏰ 实时监控")

    tab1, tab2 = st.tabs(["持仓监控", "市场监控"])

    with tab1:
        st.subheader("💼 我的持仓")

        from portfolio.position_manager import get_position_manager
        from portfolio.position_monitor import get_position_monitor

        pos_manager = get_position_manager()
        positions = pos_manager.get_all_positions()

        if not positions:
            st.info("暂无持仓，请先在'持仓配置'页面添加持仓")
        else:
            # 显示持仓统计
            stats = pos_manager.get_statistics()
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("持仓数量", f"{stats['total_positions']}个")

            with col2:
                st.metric("总市值", f"{stats['total_market_value']:,.0f}元")

            with col3:
                st.metric("总盈亏", f"{stats['total_profit_loss']:+,.0f}元",
                         delta_color="normal" if stats['total_profit_loss'] >= 0 else "inverse")

            with col4:
                st.metric("盈亏比例", f"{stats['profit_loss_pct']:+.2f}%",
                         delta_color="normal" if stats['profit_loss_pct'] >= 0 else "inverse")

            st.divider()

            # 持仓列表
            st.subheader("📋 持仓明细")

            for pos in positions:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

                    with col1:
                        st.write(f"**{pos.name}** ({pos.code})")

                    with col2:
                        st.metric("持股", f"{pos.shares}股")

                    with col3:
                        st.metric("现价", f"{pos.current_price:.2f}元")

                    with col4:
                        pl_color = "🔴" if pos.profit_loss < 0 else "🟢"
                        st.write(f"{pl_color} {pos.profit_loss:+.2f}元 ({pos.profit_loss_pct:+.2f}%)")

                    with col5:
                        if pos.stop_loss_price:
                            st.caption(f"止损: {pos.stop_loss_price:.2f}")
                        if pos.take_profit_price:
                            st.caption(f"止盈: {pos.take_profit_price:.2f}")

                    st.divider()

            # 监控按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 更新价格", type="primary"):
                    monitor = get_position_monitor()
                    monitor.monitor_all_positions()
                    st.success("价格已更新！")
                    st.rerun()

            with col2:
                if st.button("📊 导出持仓"):
                    export_data = pos_manager.export_positions()
                    st.download_button(
                        "下载持仓数据",
                        export_data,
                        "positions.json",
                        "application/json"
                    )

    with tab2:
        st.subheader("📊 市场监控状态")

        from monitor.realtime_monitor import get_global_monitor

        monitor = get_global_monitor()
        status = monitor.get_status()

        col1, col2 = st.columns(2)

        with col1:
            st.write("**监控状态**")
            st.write(f"- 运行中: {'是' if status['is_running'] else '否'}")
            st.write(f"- 交易时间: {'是' if status['is_market_time'] else '否'}")
            st.write(f"- 当前时间: {status['current_time']}")

        with col2:
            st.write("**配置信息**")
            st.write(f"- 更新间隔: {status['config']['update_interval']}秒")
            st.write(f"- 开盘时间: {status['config']['market_open']}")
            st.write(f"- 收盘时间: {status['config']['market_close']}")

        st.divider()

        if st.button("🔄 手动更新情绪数据"):
            monitor.manual_update()
            st.success("情绪数据已更新！")

# 6. 预警中心
elif st.session_state.current_page == 'alerts':
    st.title("🔔 预警中心")

    from monitor.alert_manager import get_alert_manager, AlertLevel, AlertCategory

    alert_manager = get_alert_manager()

    # 预警统计
    stats = alert_manager.get_statistics()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总预警", f"{stats['total']}条")

    with col2:
        st.metric("未读", f"{stats['unread']}条")

    with col3:
        st.metric("严重", f"{stats['critical']}条")

    with col4:
        st.metric("今日", f"{stats['today']}条")

    st.divider()

    # 预警筛选
    col1, col2, col3 = st.columns(3)

    with col1:
        level_filter = st.selectbox(
            "预警级别",
            ["全部", "CRITICAL", "WARNING", "INFO"]
        )

    with col2:
        category_filter = st.selectbox(
            "预警类别",
            ["全部", "market", "position", "sector", "system"]
        )

    with col3:
        if st.button("🗑️ 清除旧预警"):
            alert_manager.clear_old_alerts(days=7)
            st.success("已清除7天前的预警")

    st.divider()

    # 显示预警列表
    st.subheader("📋 预警列表")

    # 获取预警
    if level_filter == "全部":
        alerts = alert_manager.get_recent_alerts(20)
    else:
        alerts = alert_manager.get_alerts_by_level(AlertLevel(level_filter))

    # 进一步过滤
    if category_filter != "全部":
        alerts = [a for a in alerts if a.category.value == category_filter]

    if not alerts:
        st.info("暂无预警")
    else:
        for alert in alerts:
            # 根据级别选择样式
            if alert.level == AlertLevel.CRITICAL:
                st.markdown(f"""
                <div class="alert-critical">
                    <strong>[{alert.level.value}] {alert.title}</strong><br/>
                    时间: {datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}<br/>
                    {alert.message}<br/>
                    <strong>建议:</strong> {alert.suggestion}
                </div>
                """, unsafe_allow_html=True)
            elif alert.level == AlertLevel.WARNING:
                st.markdown(f"""
                <div class="alert-warning">
                    <strong>[{alert.level.value}] {alert.title}</strong><br/>
                    时间: {datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}<br/>
                    {alert.message}<br/>
                    <strong>建议:</strong> {alert.suggestion}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-info">
                    <strong>[{alert.level.value}] {alert.title}</strong><br/>
                    时间: {datetime.fromisoformat(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}<br/>
                    {alert.message}<br/>
                    <strong>建议:</strong> {alert.suggestion}
                </div>
                """, unsafe_allow_html=True)

            st.divider()

    # 批量操作
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ 全部标记为已读"):
            alert_manager.mark_all_as_read()
            st.success("所有预警已标记为已读")
            st.rerun()

    with col2:
        if st.button("📊 导出预警"):
            alerts_text = "\n\n".join([
                alert_manager.format_alert_text(a)
                for a in alert_manager.get_recent_alerts(50)
            ])
            st.download_button(
                "下载预警记录",
                alerts_text,
                "alerts.txt",
                "text/plain"
            )

# ==================== 自动刷新逻辑 ====================

if st.session_state.auto_refresh:
    # 显示刷新状态
    st.sidebar.caption(f"🔄 {st.session_state.refresh_interval}秒后自动刷新...")

    # 自动刷新
    tm.sleep(st.session_state.refresh_interval)
    st.rerun()

# 页脚
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;'>
    ⚠️ <strong>免责声明</strong>：本系统仅供参考，不构成投资建议。
    <br>用户需自主决策，控制风险。投资有风险，入市需谨慎。
    <br><br>
    📊 短线情绪择时助手 v2.0 | 集成 Phase 1-6 功能
</div>
""", unsafe_allow_html=True)
