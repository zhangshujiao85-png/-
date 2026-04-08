# -*- coding: utf-8 -*-
"""
Simple test script - Verify all modules can be imported
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("AI Timing Assistant - Module Import Test")
print("=" * 60)

# Test importing each module
modules = [
    ("Config", "config.settings"),
    ("Market Data", "data.market_data"),
    ("Indicators", "utils.indicators"),
    ("Cache", "utils.cache"),
    ("Market Regime", "analysis.market_regime"),
    ("Timing Analyzer", "analysis.timing_analyzer"),
    ("AI Service", "ai.llm_service"),
    ("Report Generator", "output.report_generator"),
]

success_count = 0
failed_modules = []

for name, module_path in modules:
    try:
        __import__(module_path)
        print(f"[OK] {name}: Import successful")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] {name}: Import failed - {e}")
        failed_modules.append((name, e))

print("=" * 60)
print(f"Test Result: {success_count}/{len(modules)} modules imported successfully")

if failed_modules:
    print("\nFailed modules:")
    for name, error in failed_modules:
        print(f"  - {name}: {error}")
else:
    print("\nAll modules imported successfully!")

print("=" * 60)
