"""
AI 智能择时助手 - 命令行入口
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from analysis.market_regime import MarketRegimeAnalyzer
from analysis.timing_analyzer import TimingAnalyzer
# 延迟导入 AI 相关模块
try:
    from ai.llm_service import LLMService
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("警告: AI 模块不可用（未安装 dashscope），将使用基础功能")

from output.report_generator import ReportGenerator
from config.settings import settings


def analyze_market():
    """分析市场状态"""
    print("=== 市场趋势分析 ===\n")

    try:
        analyzer = MarketRegimeAnalyzer()
        regime = analyzer.analyze(settings.MARKET_INDEXES)

        # 生成报告
        enable_ai = settings.ENABLE_AI and AI_AVAILABLE
        generator = ReportGenerator(enable_ai=enable_ai)
        report = generator.generate_market_report(regime)

        # 打印报告
        print(generator.format_market_report_text(report))

    except Exception as e:
        print(f"分析失败: {e}")
        return 1

    return 0


def analyze_stock(stock_code: str):
    """分析个股择时"""
    print(f"=== 个股择时分析: {stock_code} ===\n")

    try:
        # 分析市场
        regime_analyzer = MarketRegimeAnalyzer()
        market_regime = regime_analyzer.analyze(settings.MARKET_INDEXES)

        # 分析个股
        timing_analyzer = TimingAnalyzer()
        signal = timing_analyzer.analyze(stock_code, market_regime)

        # 获取股票名称
        from data.market_data import MarketDataFetcher
        fetcher = MarketDataFetcher()
        quote = fetcher.get_stock_quote(stock_code)
        stock_name = quote.get('name', stock_code) if quote else stock_code

        # 生成报告
        enable_ai = settings.ENABLE_AI and AI_AVAILABLE
        generator = ReportGenerator(enable_ai=enable_ai)
        report = generator.generate_timing_report(stock_code, stock_name, signal)

        # 打印报告
        print(generator.format_timing_report_text(report))

    except Exception as e:
        print(f"分析失败: {e}")
        return 1

    return 0


def analyze_batch(stock_codes: list, output_file: str = None):
    """批量分析股票"""
    print(f"=== 批量分析 {len(stock_codes)} 只股票 ===\n")

    try:
        # 分析市场
        regime_analyzer = MarketRegimeAnalyzer()
        market_regime = regime_analyzer.analyze(settings.MARKET_INDEXES)

        # 生成报告
        enable_ai = settings.ENABLE_AI and AI_AVAILABLE
        generator = ReportGenerator(enable_ai=enable_ai)
        timing_analyzer = TimingAnalyzer()

        # 分析结果
        results = []
        timing_reports = []

        for i, code in enumerate(stock_codes):
            print(f"[{i+1}/{len(stock_codes)}] 正在分析 {code}...")

            try:
                # 分析个股
                signal = timing_analyzer.analyze(code, market_regime)

                # 获取股票名称
                from data.market_data import MarketDataFetcher
                fetcher = MarketDataFetcher()
                quote = fetcher.get_stock_quote(code)
                stock_name = quote.get('name', code) if quote else code

                # 生成报告
                report = generator.generate_timing_report(code, stock_name, signal)
                timing_reports.append(report)

                # 保存简略结果
                results.append({
                    'code': code,
                    'name': stock_name,
                    'action': signal.action.value,
                    'confidence': signal.confidence,
                    'current_price': signal.current_price,
                    'price_target': signal.price_target,
                    'stop_loss': signal.stop_loss,
                    'technical_score': signal.technical_score,
                    'sentiment_score': signal.sentiment_score
                })

                # 打印简略信息
                action_map = {
                    'buy': '✅ 买入',
                    'sell': '❌ 卖出',
                    'hold': '⏸️ 持有',
                    'wait': '⏳ 观望'
                }
                print(f"  操作: {action_map[signal.action.value]}, "
                      f"置信度: {signal.confidence:.0f}%, "
                      f"当前价: {signal.current_price:.2f}")

            except Exception as e:
                print(f"  分析失败: {e}")
                results.append({
                    'code': code,
                    'name': '未知',
                    'action': 'error',
                    'error': str(e)
                })

        # 打印汇总
        print("\n=== 分析汇总 ===")
        import pandas as pd
        df = pd.DataFrame(results)

        action_map = {
            'buy': '✅ 买入',
            'sell': '❌ 卖出',
            'hold': '⏸️ 持有',
            'wait': '⏳ 观望',
            'error': '❌ 失败'
        }
        df['操作建议'] = df['action'].map(action_map)

        display_columns = ['code', 'name', '操作建议', 'confidence',
                          'current_price', 'price_target', 'stop_loss']
        df_display = df[display_columns].copy()
        df_display.columns = ['代码', '名称', '操作建议', '置信度',
                             '当前价', '目标价', '止损价']

        print(df_display.to_string(index=False))

        # 输出文件
        if output_file:
            if output_file.endswith('.csv'):
                df_display.to_csv(output_file, index=False, encoding='utf-8-sig')
                print(f"\n结果已保存到: {output_file}")
            elif output_file.endswith('.html'):
                # 生成 HTML 报告
                market_report = generator.generate_market_report(market_regime)
                html = generator.generate_html_report(market_report, timing_reports)

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"\nHTML 报告已保存到: {output_file}")

    except Exception as e:
        print(f"批量分析失败: {e}")
        return 1

    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI 智能择时助手 - 基于技术分析和市场情绪的择时工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析市场状态
  python main.py --market

  # 分析单只股票
  python main.py --stock 600519

  # 批量分析股票
  python main.py --batch 600519,000858,600036

  # 批量分析并导出 CSV
  python main.py --batch 600519,000858,600036 --output results.csv

  # 批量分析并导出 HTML 报告
  python main.py --batch 600519,000858,600036 --output report.html
        """
    )

    parser.add_argument('--market', action='store_true',
                       help='分析市场状态')
    parser.add_argument('--stock', type=str,
                       help='分析单只股票（输入6位代码）')
    parser.add_argument('--batch', type=str,
                       help='批量分析股票（用逗号分隔的6位代码）')
    parser.add_argument('--output', type=str,
                       help='输出文件路径（支持 .csv 和 .html 格式）')
    parser.add_argument('--no-ai', action='store_true',
                       help='禁用 AI 分析功能')

    args = parser.parse_args()

    # 检查参数
    if not any([args.market, args.stock, args.batch]):
        parser.print_help()
        return 1

    # 更新设置
    if args.no_ai:
        settings.ENABLE_AI = False

    # 执行相应的命令
    if args.market:
        return analyze_market()
    elif args.stock:
        return analyze_stock(args.stock)
    elif args.batch:
        codes = [c.strip() for c in args.batch.split(',') if c.strip()]
        if not codes:
            print("错误: 未提供有效的股票代码")
            return 1
        return analyze_batch(codes, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
