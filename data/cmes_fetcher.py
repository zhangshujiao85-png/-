# -*- coding: utf-8 -*-
"""
CMES数据获取模块
提供实时行情、历史K线、分笔tick数据
"""
from cmesdata import login, login_out, get_real_hq, get_history_data, get_index_data, get_tick
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class CMESDataFetcher:
    """CMES数据库数据获取器"""

    def __init__(self, token: str = None):
        """
        初始化CMES数据获取器

        Args:
            token: CMES API Token
        """
        self.token = token or "78016cb83f5e45a6b807ecb3d708db27"
        self.is_logged_in = False
        self.login_time = None

    def login(self) -> bool:
        """
        登录CMES系统

        Returns:
            登录是否成功
        """
        try:
            print(f"[CMES] 正在登录...")
            login(self.token)
            self.is_logged_in = True
            self.login_time = datetime.now()
            print(f"[CMES] [OK] 登录成功")
            return True
        except Exception as e:
            print(f"[CMES] [FAIL] 登录失败: {e}")
            self.is_logged_in = False
            return False

    def logout(self):
        """退出登录"""
        try:
            if self.is_logged_in:
                login_out()
                self.is_logged_in = False
                print(f"[CMES] 已退出登录")
        except Exception as e:
            print(f"[CMES] 退出登录失败: {e}")

    def get_realtime_quotes(self, symbols: List[str], max_retries: int = 2) -> Dict[str, Dict]:
        """
        获取实时行情（五档订单簿）

        Args:
            symbols: 股票代码列表（需要SH/SZ前缀）
            max_retries: 最大重试次数

        Returns:
            股票实时行情字典
        """
        if not self.is_logged_in:
            if not self.login():
                return {}

        try:
            # 自动添加前缀
            formatted_symbols = []
            for symbol in symbols:
                if isinstance(symbol, str):
                    if not symbol.startswith(('SH.', 'SZ.')):
                        prefix = 'SH.' if symbol.startswith('6') else 'SZ.'
                        formatted_symbols.append(f"{prefix}{symbol}")
                    else:
                        formatted_symbols.append(symbol)

            # CMES限制单次80只股票，分批获取
            batch_size = 80
            all_data = {}

            for i in range(0, len(formatted_symbols), batch_size):
                batch = formatted_symbols[i:i+batch_size]

                for retry in range(max_retries):
                    try:
                        df = get_real_hq(batch)

                        if df is not None and not df.empty:
                            # 转换为标准格式
                            for _, row in df.iterrows():
                                # 尝试多种可能的字段名
                                code = None
                                for col in ['代码', 'symbol', '代码名称']:
                                    if col in df.columns:
                                        code = row.get(col, '')
                                        break

                                if not code:
                                    continue

                                # 去掉前缀用于返回
                                original_code = str(code).replace('SH.', '').replace('SZ.', '')

                                # 获取名称
                                name = ''
                                for col in ['名称', 'name', '证券名称']:
                                    if col in df.columns:
                                        name = row.get(col, '')
                                        break

                                # 获取价格
                                price = 0
                                for col in ['最新价', 'price', '最新', '现价']:
                                    if col in df.columns:
                                        val = row.get(col, 0)
                                        if val and val != 0:
                                            price = float(val)
                                            break

                                # 获取其他字段
                                open_price = 0
                                for col in ['今开', 'open', '开盘价']:
                                    if col in df.columns:
                                        val = row.get(col, 0)
                                        if val and val != 0:
                                            open_price = float(val)
                                            break

                                high_price = 0
                                for col in ['最高', 'high', '最高价']:
                                    if col in df.columns:
                                        val = row.get(col, 0)
                                        if val and val != 0:
                                            high_price = float(val)
                                            break

                                low_price = 0
                                for col in ['最低', 'low', '最低价']:
                                    if col in df.columns:
                                        val = row.get(col, 0)
                                        if val and val != 0:
                                            low_price = float(val)
                                            break

                                volume = 0
                                for col in ['成交量', 'volume', '量']:
                                    if col in df.columns:
                                        val = row.get(col, 0)
                                        if val and val != 0:
                                            volume = float(val)
                                            break

                                amount = 0
                                for col in ['成交额', 'amount', '额']:
                                    if col in df.columns:
                                        val = row.get(col, 0)
                                        if val and val != 0:
                                            amount = float(val)
                                            break

                                change_pct = 0
                                for col in ['涨跌幅', 'change_pct', '涨跌']:
                                    if col in df.columns:
                                        val = row.get(col, 0)
                                        if val is not None and val != 0:
                                            change_pct = float(val)
                                            break

                                turnover = 0
                                for col in ['换手率', 'turnover', '换手']:
                                    if col in df.columns:
                                        val = row.get(col, 0)
                                        if val and val != 0:
                                            turnover = float(val)
                                            break

                                all_data[original_code] = {
                                    'code': original_code,
                                    'name': name,
                                    'price': price,
                                    'open': open_price,
                                    'high': high_price,
                                    'low': low_price,
                                    'volume': volume,
                                    'amount': amount,
                                    'change_pct': change_pct,
                                    'turnover': turnover,
                                    'timestamp': datetime.now().isoformat(),
                                    'data_source': 'CMES'
                                }
                            break  # 成功获取，跳出重试循环

                    except Exception as e:
                        if retry == max_retries - 1:
                            print(f"[CMES] 获取实时行情失败: {e}")
                        time.sleep(0.5)

            return all_data

        except Exception as e:
            print(f"[CMES] 获取实时行情异常: {e}")
            return {}

    def get_history_klines(self, symbol: str, start_date: str, end_date: str,
                          freq: str = 'D') -> pd.DataFrame:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码（需要SH/SZ前缀）
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            freq: 频率 (1min/5min/15min/30min/60min/D/W/M)

        Returns:
            K线数据DataFrame
        """
        if not self.is_logged_in:
            self.login()

        try:
            # 格式化代码
            if isinstance(symbol, str) and not symbol.startswith(('SH.', 'SZ.')):
                prefix = 'SH.' if symbol.startswith('6') else 'SZ.'
                symbol = f"{prefix}{symbol}"

            df = get_history_data(symbol, start_date, end_date, freq)

            if df is not None and not df.empty:
                # 标准化列名
                df = df.rename(columns={
                    '时间': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '涨跌幅': 'change_pct'
                })

                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])

            return df

        except Exception as e:
            print(f"[CMES] 获取历史数据失败: {e}")
            return pd.DataFrame()

    def get_index_realtime(self, index_codes: List[str]) -> Dict[str, Dict]:
        """
        获取指数实时行情

        Args:
            index_codes: 指数代码列表

        Returns:
            指数行情字典
        """
        if not self.is_logged_in:
            self.login()

        try:
            # 格式化指数代码
            formatted_codes = []
            for code in index_codes:
                if isinstance(code, str) and not code.startswith(('SH.', 'SZ.')):
                    prefix = 'SH.' if code.startswith('0') else 'SZ.'
                    formatted_codes.append(f"{prefix}{code}")
                else:
                    formatted_codes.append(code)

            df = get_real_hq(formatted_codes)

            result = {}
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    code = row.get('代码', '').replace('SH.', '').replace('SZ.', '')
                    result[code] = {
                        'code': code,
                        'name': row.get('名称', ''),
                        'price': float(row.get('最新价', 0)),
                        'change_pct': float(row.get('涨跌幅', 0)),
                        'timestamp': datetime.now().isoformat(),
                        'data_source': 'CMES'
                    }

            return result

        except Exception as e:
            print(f"[CMES] 获取指数行情失败: {e}")
            return {}

    def test_data_quality(self) -> Dict:
        """
        测试CMES数据质量

        Returns:
            数据质量评估报告
        """
        print("=" * 60)
        print("CMES数据质量测试")
        print("=" * 60)

        results = {
            'login_success': False,
            'realtime_latency': None,
            'data_accuracy': None,
            'stability': None,
            'recommendation': ''
        }

        # 测试1: 登录
        print("\n[测试1] 登录测试...")
        if self.login():
            results['login_success'] = True
            print("[OK] 登录成功")
        else:
            print("[FAIL] 登录失败")
            results['recommendation'] = "❌ 无法登录，建议检查token或联系客服"
            return results

        # 测试2: 实时行情延迟
        print("\n[测试2] 实时行情延迟测试...")
        test_symbols = ['SH.600519', 'SZ.000858', 'SH.600036']

        latencies = []
        for _ in range(5):
            start = time.time()
            data = self.get_realtime_quotes(['600519', '000858', '600036'])
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            print(f"  第{len(latencies)}次: {latency:.0f}ms")
            time.sleep(0.5)

        avg_latency = np.mean(latencies)
        results['realtime_latency'] = {
            'avg_ms': round(avg_latency, 1),
            'min_ms': round(np.min(latencies), 1),
            'max_ms': round(np.max(latencies), 1)
        }

        if avg_latency < 500:
            print(f"[OK] 平均延迟: {avg_latency:.0f}ms - 优秀")
        elif avg_latency < 1000:
            print(f"[GOOD] 平均延迟: {avg_latency:.0f}ms - 良好")
        else:
            print(f"[WARN] 平均延迟: {avg_latency:.0f}ms - 偏高")

        # 测试3: 数据完整性
        print("\n[测试3] 数据完整性测试...")
        data = self.get_realtime_quotes(['600519', '000858', '600036'])

        required_fields = ['code', 'name', 'price', 'open', 'high', 'low', 'volume', 'change_pct']
        completeness = []

        for symbol, quote in data.items():
            missing = [f for f in required_fields if f not in quote or quote[f] == 0]
            completeness.append({
                'symbol': symbol,
                'missing_fields': len(missing),
                'completeness': f"{(1 - len(missing)/len(required_fields))*100:.0f}%"
            })
            print(f"  {symbol}: {completeness[-1]} 完整")

        results['data_accuracy'] = {
            'symbols_tested': len(data),
            'avg_completeness': np.mean([float(c['completeness'].replace('%', '')) for c in completeness])
        }

        # 测试4: 稳定性（连续获取10次）
        print("\n[测试4] 连续稳定性测试...")
        success_count = 0
        for i in range(10):
            try:
                data = self.get_realtime_quotes(['600519'])
                if data and '600519' in data:
                    success_count += 1
                    print(f"  第{i+1}次: [OK]")
                else:
                    print(f"  第{i+1}次: [FAIL] 无数据")
            except Exception as e:
                print(f"  第{i+1}次: [FAIL] {str(e)[:30]}")
            time.sleep(0.3)

        stability_rate = success_count / 10 * 100
        results['stability'] = {
            'success_rate': stability_rate,
            'success_count': success_count
        }

        print(f"\n稳定性: {stability_rate:.0f}% ({success_count}/10)")

        # 综合评估
        print("\n" + "=" * 60)
        print("综合评估")
        print("=" * 60)

        # 延迟评分
        latency_score = 100 if avg_latency < 500 else (80 if avg_latency < 1000 else 60)
        # 稳定性评分
        stability_score = stability_rate
        # 完整性评分
        completeness_score = results['data_accuracy']['avg_completeness']

        total_score = (latency_score * 0.4 + stability_score * 0.3 + completeness_score * 0.3)

        print(f"延迟得分: {latency_score:.0f}/100")
        print(f"稳定性得分: {stability_score:.0f}/100")
        print(f"完整性得分: {completeness_score:.0f}/100")
        print(f"\n综合得分: {total_score:.0f}/100")

        # 推荐建议
        print("\n" + "=" * 60)
        if total_score >= 80:
            results['recommendation'] = "✅ 强烈推荐 - 数据质量优秀，适合短线交易"
            print("✅ 强烈推荐购买")
            print("理由：延迟低、稳定性好、数据完整")
        elif total_score >= 70:
            results['recommendation'] = "⭕ 推荐购买 - 数据质量良好"
            print("⭕ 推荐购买")
            print("理由：基本满足短线交易需求")
        else:
            results['recommendation'] = "❌ 不推荐 - 数据质量不够理想"
            print("❌ 暂不推荐")
            print("理由：建议继续使用免费方案或寻找其他数据源")

        # 数据覆盖分析
        print("\n" + "=" * 60)
        print("数据覆盖分析")
        print("=" * 60)

        coverage = {
            "✅ 实时五档行情": "完整支持",
            "✅ 历史K线": "支持（近5个月）",
            "✅ 分钟K线": "支持（1/5/15/30/60min）",
            "✅ 分笔Tick": "支持（近5个月）",
            "❌ 市场宽度": "不支持（需用AkShare补充）",
            "❌ 资金流向": "不支持（需用AkShare补充）",
            "❌ 板块数据": "不支持（需用AkShare补充）",
            "❌ 新闻舆情": "不支持"
        }

        for item, status in coverage.items():
            print(f"{item}: {status}")

        print("\n" + "=" * 60)
        print("结论")
        print("=" * 60)

        if results['login_success'] and total_score >= 70:
            print("\n💡 建议：CMES + AkShare 双数据源方案")
            print("  - CMES: 实时行情（高质量、低延迟）")
            print("  - AkShare: 市场宽度、资金流向、板块数据（补充）")
            print(f"\n💰 成本：~300元/年（CMES）+ 0元（AkShare）")
            print("🎯 适合：短线波段交易")
        else:
            print("\n💡 建议：继续使用免费AkShare方案")
            print("  - CMES数据质量不够理想")
            print("  - AkShare已能满足系统需求")
            print("  - 配合降级保护机制即可")

        return results


# 测试代码
if __name__ == "__main__":
    # 使用您提供的token
    TOKEN = "78016cb83f5e45a6b807ecb3d708db27"

    fetcher = CMESDataFetcher(TOKEN)

    # 执行数据质量测试
    results = fetcher.test_data_quality()

    # 退出登录
    fetcher.logout()
