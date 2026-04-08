"""
测试脚本 - 验证所有模块能否正常导入
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("AI 智能择时助手 - 模块导入测试")
print("=" * 60)

# 测试导入各个模块
modules = [
    ("配置模块", "config.settings"),
    ("数据获取模块", "data.market_data"),
    ("工具模块", "utils.indicators"),
    ("缓存模块", "utils.cache"),
    ("市场趋势分析", "analysis.market_regime"),
    ("择时分析模块", "analysis.timing_analyzer"),
    ("AI 服务模块", "ai.llm_service"),
    ("报告生成模块", "output.report_generator"),
]

success_count = 0
failed_modules = []

for name, module_path in modules:
    try:
        __import__(module_path)
        print(f"✅ {name}: 导入成功")
        success_count += 1
    except Exception as e:
        print(f"❌ {name}: 导入失败 - {e}")
        failed_modules.append((name, e))

print("=" * 60)
print(f"测试结果: {success_count}/{len(modules)} 个模块导入成功")

if failed_modules:
    print("\n失败的模块:")
    for name, error in failed_modules:
        print(f"  - {name}: {error}")
else:
    print("\n🎉 所有模块导入成功！")

print("=" * 60)
