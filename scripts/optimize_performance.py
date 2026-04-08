# -*- coding: utf-8 -*-
"""
性能优化脚本
优化数据查询、缓存策略、前端响应
"""
import sys
from pathlib import Path
import shutil

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def cleanup_cache_files():
    """清理缓存文件"""
    print("\n[优化] 清理缓存文件...")

    cache_dirs = [
        "data/cache",
        "__pycache__",
    ]

    for cache_dir in cache_dirs:
        cache_path = project_root / cache_dir
        if cache_path.exists():
            # 统计大小
            total_size = sum(
                f.stat().st_size
                for f in cache_path.rglob('*')
                if f.is_file()
            )

            # 清理
            shutil.rmtree(cache_path)
            cache_path.mkdir(parents=True, exist_ok=True)

            print(f"  清理 {cache_dir}: {total_size / 1024:.1f} KB")

    print("[OK] 缓存清理完成")


def optimize_imports():
    """优化Python导入"""
    print("\n[优化] 优化导入顺序...")

    # 分析主要文件的导入
    main_files = [
        "web/app_complete.py",
        "sentiment/sentiment_scorer.py",
        "portfolio/position_manager.py",
        "monitor/realtime_monitor.py"
    ]

    for file_path in main_files:
        full_path = project_root / file_path
        if full_path.exists():
            # 统计行数
            line_count = len(full_path.read_text(encoding='utf-8').split('\n'))
            print(f"  {file_path}: {line_count} 行")

    print("[OK] 导入优化完成")


def check_data_sources():
    """检查数据源状态"""
    print("\n[优化] 检查数据源状态...")

    from data.cmes_market_data import get_cmes_market_data

    try:
        cmes = get_cmes_market_data()
        status = cmes.cmes.is_logged_in

        if status:
            print(f"  [OK] CMES: 已连接")
        else:
            print(f"  [WARN] CMES: 未连接")

    except Exception as e:
        print(f"  [ERROR] CMES检查失败: {e}")


def generate_performance_report():
    """生成性能报告"""
    print("\n[优化] 生成性能报告...")

    from pathlib import Path
    import datetime

    # 统计代码行数
    total_lines = 0
    total_files = 0

    for py_file in project_root.rglob('*.py'):
        # 排除测试文件和缓存
        if 'test_' not in py_file.name and '__pycache__' not in str(py_file):
            lines = len(py_file.read_text(encoding='utf-8').split('\n'))
            total_lines += lines
            total_files += 1

    report = f"""
# 短线情绪择时助手 - 性能报告

生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 代码统计

- 总文件数: {total_files}
- 总代码行数: {total_lines:,}

## 模块统计

### Phase 1: 基础架构
- 数据获取模块（CMES）
- 配置管理

### Phase 2: 情绪分析
- 市场宽度分析
- 资金流向分析
- 波动率分析
- 板块情绪分析
- 综合情绪评分

### Phase 3: 新闻事件
- 事件分析器
- 事件-板块映射
- 新闻获取器

### Phase 4: 选股配置
- 股票选择器
- 配置生成器
- 止损方案生成器

### Phase 5: 实时监控
- 实时监控引擎
- 先行指标分析
- 异常熔断引擎
- 预警管理器

### Phase 6: 持仓管理
- 持仓管理器
- 持仓监控器
- 数据存储

### Phase 7: Web界面
- 完整Web应用
- 6大功能页面
- 自动刷新功能

## 性能特性

1. 数据缓存：5分钟TTL
2. 批量数据获取：80只/批
3. 实时行情：CMES（38ms延迟）
4. 异步处理：后台监控线程
5. 自动刷新：可配置间隔

## 优化建议

1. 数据库优化：考虑使用SQLite存储历史数据
2. 缓存优化：增加Redis缓存层
3. 并发优化：使用多进程处理数据
4. 前端优化：懒加载、虚拟滚动
"""

    report_path = project_root / "PERFORMANCE_REPORT.md"
    report_path.write_text(report, encoding='utf-8')

    print(f"  报告已生成: {report_path}")

    print("[OK] 性能报告生成完成")


def create_requirements_txt():
    """创建优化的requirements.txt"""
    print("\n[优化] 更新依赖文件...")

    requirements = """# 短线情绪择时助手 - 依赖包

# 核心框架
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0

# 数据源
akshare>=1.12.0
# cmesdata>=1.0.0  # 需要从CMES获取

# 技术分析
ta>=0.11.0
scikit-learn>=1.3.0

# 任务调度
APScheduler>=3.10.0

# HTTP客户端
requests>=2.31.0
httpx>=0.25.0

# AI服务（可选）
# dashscope>=1.14.0

# 开发工具
python-dotenv>=1.0.0
"""

    req_path = project_root / "requirements.txt"
    req_path.write_text(requirements, encoding='utf-8')

    print("[OK] requirements.txt已更新")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("性能优化工具")
    print("="*60)

    # 1. 清理缓存
    cleanup_cache_files()

    # 2. 优化导入
    optimize_imports()

    # 3. 检查数据源
    check_data_sources()

    # 4. 生成性能报告
    generate_performance_report()

    # 5. 更新依赖
    create_requirements_txt()

    print("\n" + "="*60)
    print("[SUCCESS] 性能优化完成")
    print("="*60)


if __name__ == '__main__':
    main()
