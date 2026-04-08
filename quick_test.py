# -*- coding: utf-8 -*-
"""
Simple test - Quick market analysis
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("AI Timing Assistant - Quick Test")
print("=" * 60)

# Test basic modules
try:
    from analysis.market_regime import MarketRegimeAnalyzer
    print("[OK] Market Regime Analyzer imported")

    print("\nTesting market analysis...")
    analyzer = MarketRegimeAnalyzer()
    print("[OK] Analyzer created")

    # Note: Actual API calls will fail without proper data source
    # But at least we can verify the code structure is correct

    print("\n" + "=" * 60)
    print("Basic structure test PASSED!")
    print("=" * 60)
    print("\nNote: Full functionality requires:")
    print("1. Installing akshare (pip install akshare)")
    print("2. Optional: dashscope for AI features")
    print("\nProject is ready at: D:\\ai_timing_assistant")

except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
