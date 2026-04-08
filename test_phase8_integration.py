# -*- coding: utf-8 -*-
"""
Phase 8 集成测试套件
测试所有Phase 1-7的功能集成
"""
import sys
from pathlib import Path
import traceback

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class IntegrationTestSuite:
    """集成测试套件"""

    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        self.total_tests += 1
        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print('='*60)

        try:
            test_func()
            self.passed_tests += 1
            self.test_results[test_name] = "PASS"
            print(f"[OK] PASSED: {test_name}")
            return True
        except Exception as e:
            self.failed_tests += 1
            self.test_results[test_name] = f"FAIL: {str(e)}"
            print(f"[FAILED] {test_name}")
            print(f"Error: {e}")
            traceback.print_exc()
            return False

    def test_phase1_data_layer(self):
        """测试Phase 1: 数据层"""
        from data.cmes_market_data import get_cmes_market_data

        print("\n测试CMES数据源...")
        cmes = get_cmes_market_data()
        assert cmes is not None, "CMES初始化失败"

        print("测试市场宽度数据...")
        breadth = cmes.get_market_breadth()
        assert breadth is not None, "获取市场宽度失败"
        assert 'total_stocks' in breadth, "市场宽度数据不完整"
        print(f"  市场宽度: {breadth['breadth_score']:.0f}分")

        print("测试资金流向数据...")
        flow = cmes.get_money_flow()
        assert flow is not None, "获取资金流向失败"
        assert 'flow_score' in flow, "资金流向数据不完整"
        print(f"  资金流向: {flow['flow_score']:.0f}分")

        print("测试板块数据...")
        sector = cmes.get_sector_data('半导体')
        assert sector is not None, "获取板块数据失败"
        assert 'sentiment_score' in sector, "板块数据不完整"
        print(f"  板块情绪: {sector['sentiment_score']:.0f}分")

    def test_phase2_sentiment(self):
        """测试Phase 2: 情绪分析"""
        from sentiment.sentiment_scorer import SentimentScorer

        print("\n测试情绪评分...")
        scorer = SentimentScorer()
        sentiment = scorer.calculate_overall_sentiment()
        assert sentiment is not None, "情绪评分计算失败"
        assert sentiment.sentiment_score >= 0, "情绪得分异常"
        assert sentiment.sentiment_score <= 100, "情绪得分异常"
        print(f"  综合情绪: {sentiment.sentiment_score:.0f}分")
        print(f"  市场状态: {sentiment.market_state}")

    def test_phase3_news_event(self):
        """测试Phase 3: 新闻事件"""
        from news.event_analyzer import EventAnalyzer

        print("\n测试事件分析...")
        analyzer = EventAnalyzer()
        analysis = analyzer.analyze_event('降息', days=7)
        assert analysis is not None, "事件分析失败"
        assert analysis.event_type is not None, "事件类型为空"
        print(f"  事件类型: {analysis.event_type}")
        print(f"  情绪倾向: {analysis.sentiment}")

    def test_phase4_stock_selection(self):
        """测试Phase 4: 选股配置"""
        from selector.stock_selector import StockSelector
        from selector.allocation import AllocationGenerator
        from selector.stop_loss_plans import StopLossPlansGenerator

        print("\n测试股票选择...")
        selector = StockSelector()
        stocks = selector.select_representative_stocks('半导体', top_n=3)
        assert stocks is not None, "选股失败"
        assert len(stocks) > 0, "未找到股票"
        print(f"  选股数量: {len(stocks)}")

        print("\n测试配置生成...")
        allocator = AllocationGenerator()
        allocation = allocator.generate_allocation(100000, '稳健', stocks)
        assert allocation is not None, "配置生成失败"
        assert 'positions' in allocation, "配置数据不完整"
        print(f"  配置股票数: {len(allocation['positions'])}")

        print("\n测试止损方案...")
        plan_gen = StopLossPlansGenerator()
        if stocks:
            plans = plan_gen.generate_plans_for_stock(stocks[0]['code'], stocks[0]['price'])
            assert plans is not None, "止损方案生成失败"
            print(f"  方案数量: {len(plans)}")

    def test_phase5_monitor(self):
        """测试Phase 5: 实时监控"""
        from monitor.realtime_monitor import RealtimeMonitor
        from monitor.leading_indicator import LeadingIndicatorAnalyzer
        from monitor.circuit_breaker import CircuitBreakerEngine
        from monitor.alert_manager import AlertManager, AlertLevel, AlertCategory

        print("\n测试实时监控引擎...")
        monitor = RealtimeMonitor()
        status = monitor.get_status()
        assert status is not None, "监控状态获取失败"
        print(f"  监控状态: {'运行中' if status['is_running'] else '已停止'}")

        print("\n测试先行指标分析...")
        indicator = LeadingIndicatorAnalyzer()
        alert = indicator.generate_pre_market_alert()
        assert alert is not None, "盘前预警生成失败"
        print(f"  预警级别: {alert.level}")

        print("\n测试熔断引擎...")
        engine = CircuitBreakerEngine()
        # 测试市场崩盘检测
        result = engine.check_market_crash(-8.0)
        # 应该返回一个alert或者None
        print(f"  熔断检测: {'触发' if result else '未触发'}")

        print("\n测试预警管理器...")
        alert_mgr = AlertManager()
        alert_mgr.create_info_alert(
            AlertCategory.MARKET,
            "测试预警",
            "这是一个集成测试预警"
        )
        stats = alert_mgr.get_statistics()
        assert stats['total'] > 0, "预警统计失败"
        print(f"  预警总数: {stats['total']}")

    def test_phase6_portfolio(self):
        """测试Phase 6: 持仓管理"""
        from portfolio.position_manager import PositionManager, PositionType
        from portfolio.position_monitor import PositionMonitor
        from portfolio.storage import DataStorage

        print("\n测试持仓管理器...")
        pos_mgr = PositionManager()
        test_pos = pos_mgr.add_position(
            code='600519',
            name='Moutai Test',
            shares=100,
            buy_price=1750.0
        )
        assert test_pos is not None, "添加持仓失败"
        print(f"  持仓ID: {test_pos.id}")

        stats = pos_mgr.get_statistics()
        assert stats['total_positions'] > 0, "持仓统计失败"
        print(f"  持仓数量: {stats['total_positions']}")

        print("\n测试持仓监控器...")
        monitor = PositionMonitor(pos_mgr)
        monitor_status = monitor.get_monitoring_status()
        assert monitor_status is not None, "监控状态获取失败"
        print(f"  监控状态: {'运行中' if monitor_status['is_monitoring'] else '已停止'}")

        print("\n测试数据存储...")
        storage = DataStorage()
        info = storage.get_storage_info()
        assert info is not None, "存储信息获取失败"
        print(f"  数据目录: {info['data_dir']}")

    def test_phase7_web_interface(self):
        """测试Phase 7: Web界面"""
        print("\n测试Web界面文件...")

        web_file = project_root / "web" / "app_complete.py"
        assert web_file.exists(), "Web应用文件不存在"
        print(f"  Web应用: {web_file}")

        # 检查文件大小
        file_size = web_file.stat().st_size
        assert file_size > 10000, "Web应用文件太小"
        print(f"  文件大小: {file_size:,} 字节")

    def test_integration(self):
        """测试模块间集成"""
        print("\n测试情绪-选股集成...")
        from sentiment.sentiment_scorer import SentimentScorer
        from selector.stock_selector import StockSelector

        scorer = SentimentScorer()
        sentiment = scorer.calculate_overall_sentiment()

        selector = StockSelector()
        # 选择情绪较好的板块
        stocks = selector.select_representative_stocks('半导体', top_n=3)
        assert stocks is not None, "集成测试失败"
        print(f"  在情绪={sentiment.sentiment_score:.0f}时选股: {len(stocks)}只")

        print("\n测试持仓-监控集成...")
        from portfolio.position_manager import PositionManager
        from portfolio.position_monitor import PositionMonitor
        from monitor.alert_manager import AlertManager

        pos_mgr = PositionManager()
        pos = pos_mgr.add_position(
            code='600519',
            name='Test Stock',
            shares=100,
            buy_price=1750.0,
            stop_loss_price=1700.0
        )

        monitor = PositionMonitor(pos_mgr)
        # 模拟价格更新触发预警
        monitor.update_prices({'600519': 1690.0})
        print("  价格更新和预警检查完成")

        alert_mgr = AlertManager()
        stats = alert_mgr.get_statistics()
        print(f"  预警已记录: {stats['total']}条")

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("测试摘要 / Test Summary")
        print("="*60)

        print(f"\n总测试数: {self.total_tests}")
        print(f"通过: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)")
        print(f"失败: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)")

        print("\n详细结果 / Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "[OK]" if result == "PASS" else "[FAIL]"
            print(f"  {status} {test_name}: {result}")

        print("\n" + "="*60)

        if self.failed_tests == 0:
            print("[SUCCESS] All tests passed!")
        else:
            print(f"[WARNING] {self.failed_tests} tests failed")

        print("="*60)


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Phase 8 Integration Test Suite")
    print("短线情绪择时助手 - 综合集成测试")
    print("="*60)

    suite = IntegrationTestSuite()

    # 运行所有测试
    suite.run_test("Phase 1: 数据层", suite.test_phase1_data_layer)
    suite.run_test("Phase 2: 情绪分析", suite.test_phase2_sentiment)
    suite.run_test("Phase 3: 新闻事件", suite.test_phase3_news_event)
    suite.run_test("Phase 4: 选股配置", suite.test_phase4_stock_selection)
    suite.run_test("Phase 5: 实时监控", suite.test_phase5_monitor)
    suite.run_test("Phase 6: 持仓管理", suite.test_phase6_portfolio)
    suite.run_test("Phase 7: Web界面", suite.test_phase7_web_interface)
    suite.run_test("集成测试", suite.test_integration)

    # 打印摘要
    suite.print_summary()


if __name__ == '__main__':
    main()
