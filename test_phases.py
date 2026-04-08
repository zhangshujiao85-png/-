"""
Test script for Phases 1-4 implementation
Tests the core functionality of the sentiment timing assistant
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_phase1_data_layer():
    """Test Phase 1: Extended data layer"""
    print("=" * 60)
    print("Testing Phase 1: Data Layer Extensions")
    print("=" * 60)

    try:
        from data.market_data import MarketDataFetcher

        fetcher = MarketDataFetcher()

        # Test get_sector_data
        print("\n1. Testing get_sector_data()...")
        sector_data = fetcher.get_sector_data('半导体')
        print(f"   ✓ Sector: {sector_data.get('name')}")
        print(f"   ✓ Change: {sector_data.get('change_pct', 0):.2f}%")

        # Test get_sector_constituents
        print("\n2. Testing get_sector_constituents()...")
        constituents = fetcher.get_sector_constituents('军工')
        print(f"   ✓ Found {len(constituents)} stocks")

        # Test get_realtime_quote
        print("\n3. Testing get_realtime_quote()...")
        quote = fetcher.get_realtime_quote('600519')
        if quote:
            print(f"   ✓ {quote.get('name')}: {quote.get('price', 0):.2f}")

        # Test get_pre_market_data
        print("\n4. Testing get_pre_market_data()...")
        pre_market = fetcher.get_pre_market_data()
        print(f"   ✓ A50: {pre_market.get('a50', {}).get('price', 0):.2f}")
        print(f"   ✓ US stocks: {len(pre_market.get('us_stocks', {}))} symbols")

        print("\n[PASS] Phase 1: PASSED")
        return True

    except Exception as e:
        print(f"\n[FAIL] Phase 1: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase2_sentiment():
    """Test Phase 2: Sentiment analysis"""
    print("\n" + "=" * 60)
    print("Testing Phase 2: Sentiment Analysis")
    print("=" * 60)

    try:
        from sentiment.sentiment_scorer import SentimentScorer

        scorer = SentimentScorer()

        # Test overall sentiment
        print("\n1. Testing calculate_overall_sentiment()...")
        sentiment = scorer.calculate_overall_sentiment()
        print(f"   ✓ Overall Score: {sentiment.sentiment_score:.1f}")
        print(f"   ✓ Market State: {sentiment.market_state}")
        print(f"   ✓ Breadth: {sentiment.breadth_score:.1f}")
        print(f"   ✓ Money Flow: {sentiment.money_flow_score:.1f}")
        print(f"   ✓ Volatility: {sentiment.volatility_score:.1f}")

        # Test sector sentiment
        print("\n2. Testing sector sentiment...")
        from sentiment.sector_sentiment import SectorSentimentAnalyzer
        sector_analyzer = SectorSentimentAnalyzer()
        sector_sentiment = sector_analyzer.calculate_sector_sentiment('半导体')
        print(f"   ✓ Sector Score: {sector_sentiment['sentiment_score']:.1f}")

        # Test hot sectors
        print("\n3. Testing get_hot_sectors()...")
        hot = sector_analyzer.get_hot_sectors(top_n=3)
        print(f"   ✓ Found {len(hot)} hot sectors")
        for sector in hot:
            print(f"      - {sector['name']}: {sector['score']:.1f}分")

        print("\n[PASS] Phase 2: PASSED")
        return True

    except Exception as e:
        print(f"\n[FAIL] Phase 2: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase3_news():
    """Test Phase 3: News and event analysis"""
    print("\n" + "=" * 60)
    print("Testing Phase 3: News & Event Analysis")
    print("=" * 60)

    try:
        from news.event_analyzer import EventAnalyzer
        from news.sector_mapper import SectorMapper

        # Test sector mapper
        print("\n1. Testing SectorMapper...")
        mapper = SectorMapper()

        affected = mapper.get_affected_sectors('地缘冲突')
        print(f"   ✓ Found {len(affected)} affected sectors")

        event_type = mapper.get_event_type('降息')
        print(f"   ✓ Event type: {event_type}")

        # Test event analyzer
        print("\n2. Testing EventAnalyzer...")
        analyzer = EventAnalyzer()

        analysis = analyzer.analyze_event('降息', days=7)
        print(f"   ✓ Event: {analysis.event_keyword}")
        print(f"   ✓ Type: {analysis.event_type}")
        print(f"   ✓ Sentiment: {analysis.sentiment}")
        print(f"   ✓ News count: {analysis.news_count}")
        print(f"   ✓ Affected sectors: {len(analysis.affected_sectors)}")

        print("\n[PASS] Phase 3: PASSED")
        return True

    except Exception as e:
        print(f"\n[FAIL] Phase 3: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phase4_selection():
    """Test Phase 4: Stock selection and allocation"""
    print("\n" + "=" * 60)
    print("Testing Phase 4: Stock Selection & Allocation")
    print("=" * 60)

    try:
        from selector.stock_selector import StockSelector
        from selector.allocation import AllocationGenerator
        from selector.stop_loss_plans import StopLossPlansGenerator

        # Test stock selector
        print("\n1. Testing StockSelector...")
        selector = StockSelector()

        stocks = selector.select_representative_stocks('半导体', top_n=3)
        print(f"   ✓ Selected {len(stocks)} stocks")
        for stock in stocks:
            print(f"      - {stock['code']} {stock['name']}: {stock['score']:.1f}分 ({stock['type']})")

        # Test allocation generator
        print("\n2. Testing AllocationGenerator...")
        allocator = AllocationGenerator()

        # Use mock stocks if real stocks not available
        if not stocks:
            mock_stocks = [
                {'code': '600460', 'name': '土兰微', 'price': 25.50, 'score': 78.5,
                 'market_cap': 50000000000, 'turnover': 8.5, 'type': '活跃型',
                 'change_pct': 3.2, 'sentiment_score': 75, 'flow_score': 80,
                 'cap_score': 70, 'activity_score': 85},
                {'code': '603986', 'name': '兆易创新', 'price': 120.30, 'score': 75.2,
                 'market_cap': 80000000000, 'turnover': 6.2, 'type': '敏感型',
                 'change_pct': 2.8, 'sentiment_score': 72, 'flow_score': 75,
                 'cap_score': 80, 'activity_score': 70},
            ]
            stocks = mock_stocks

        allocation = allocator.generate_allocation(100000, '稳健', stocks)
        print(f"   ✓ Generated allocation with {len(allocation['positions'])} positions")
        print(f"   ✓ Total capital: {allocation['total_capital']:,.0f}元")

        # Test stop-loss plans
        print("\n3. Testing StopLossPlansGenerator...")
        plan_generator = StopLossPlansGenerator()

        plans = plan_generator.generate_plans_for_stock('600519', 1650.0)
        print(f"   ✓ Generated {len(plans)} plans")

        for plan_name in ['保守型', '稳健型', '激进型']:
            if plan_name in plans:
                plan = plans[plan_name]
                print(f"      - {plan_name}: 止损{plan.stop_loss_price:.2f} "
                      f"止盈{plan.take_profit_price:.2f} 胜率{plan.historical_win_rate}%")

        print("\n[PASS] Phase 4: PASSED")
        return True

    except Exception as e:
        print(f"\n[FAIL] Phase 4: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integrated workflow"""
    print("\n" + "=" * 60)
    print("Testing Integrated Workflow")
    print("=" * 60)

    try:
        print("\n📊 Scenario: User wants to invest in 半导体 sector")
        print("   Investment: 100,000元")
        print("   Risk preference: 稳健")
        print("   Event: AI突破\n")

        # 1. Check market sentiment
        print("1️⃣ Checking market sentiment...")
        from sentiment.sentiment_scorer import SentimentScorer
        scorer = SentimentScorer()
        market_sentiment = scorer.calculate_overall_sentiment()
        state_display = scorer.get_market_state_display(market_sentiment.market_state)
        print(f"   Market: {state_display['emoji']} {state_display['name']} "
              f"({market_sentiment.sentiment_score:.1f}分)")

        # 2. Analyze event impact
        print("\n2️⃣ Analyzing event impact...")
        from news.event_analyzer import EventAnalyzer
        event_analyzer = EventAnalyzer()
        event_analysis = event_analyzer.analyze_event('AI突破')
        print(f"   Event: {event_analysis.event_keyword}")
        print(f"   Sentiment: {event_analysis.sentiment}")

        # 3. Check sector sentiment
        print("\n3️⃣ Checking sector sentiment...")
        from sentiment.sector_sentiment import SectorSentimentAnalyzer
        sector_analyzer = SectorSentimentAnalyzer()
        sector_sentiment = sector_analyzer.calculate_sector_sentiment('半导体')
        print(f"   Semiconductor: {sector_sentiment['sentiment_score']:.1f}分")

        # 4. Select stocks
        print("\n4️⃣ Selecting stocks...")
        from selector.stock_selector import StockSelector
        selector = StockSelector()
        stocks = selector.select_representative_stocks('半导体', top_n=5)
        print(f"   Selected {len(stocks)} stocks:")
        for stock in stocks[:3]:
            print(f"      - {stock['code']} {stock['name']}: {stock['score']:.0f}分")

        # 5. Generate allocation
        print("\n5️⃣ Generating allocation...")
        from selector.allocation import AllocationGenerator
        allocator = AllocationGenerator()

        if stocks:
            allocation = allocator.generate_allocation(100000, '稳健', stocks)
            print(f"   Generated {len(allocation['positions'])} positions:")
            for pos in allocation['positions'][:3]:
                print(f"      - {pos['code']} {pos['name']}: "
                      f"{pos['shares']}股 ({pos['capital']:,.0f}元)")

        # 6. Generate stop-loss plans
        print("\n6️⃣ Generating stop-loss plans...")
        from selector.stop_loss_plans import StopLossPlansGenerator
        plan_gen = StopLossPlansGenerator()

        if stocks:
            sample_stock = stocks[0]
            plans = plan_gen.generate_plans_for_stock(sample_stock['code'], sample_stock['price'])
            selected_plan = plan_gen.select_plan_by_risk(plans, '稳健')
            print(f"   Stock: {sample_stock['code']} {sample_stock['name']}")
            print(f"   Plan: {selected_plan.name}")
            print(f"   Stop loss: {selected_plan.stop_loss_price:.2f}")
            print(f"   Take profit: {selected_plan.take_profit_price:.2f}")

        print("\n[PASS] Integration Test: PASSED")
        print("\n" + "=" * 60)
        print("[OK] Core workflow test completed successfully!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n[FAIL] Integration Test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("   AI TIMING ASSISTANT - PHASE 1-4 TEST SUITE")
    print("=" * 60)

    results = {
        'Phase 1 - Data Layer': test_phase1_data_layer(),
        'Phase 2 - Sentiment': test_phase2_sentiment(),
        'Phase 3 - News & Events': test_phase3_news(),
        'Phase 4 - Selection & Allocation': test_phase4_selection(),
        'Integration Test': test_integration()
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for phase, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{phase}: {status}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n[OK] All tests passed! System is ready for next phase.")
    else:
        print(f"\n[WARN] {total - passed} test(s) failed. Please review the errors above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
