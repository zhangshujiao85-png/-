# -*- coding: utf-8 -*-
"""
Tushare Token Checker - Check if your token works
"""
import tushare as ts

token = "55672a3b22ceb51d5b77f255919ce26ee691d204985118e2b133207"

print("=" * 60)
print("Testing Tushare Token")
print("=" * 60)
print(f"Token: {token[:8]}...{token[-8:]}")
print(f"Length: {len(token)} characters")

print("\n[Step 1/2] Initializing...")
try:
    ts.set_token(token)
    pro = ts.pro_api()
    print("[OK] Pro API initialized")
except Exception as e:
    print(f"[ERROR] Pro API failed: {str(e)}")
    print("\nPossible issues:")
    print("1. Token is invalid")
    print("2. Account not activated")
    print("3. No permission")
    exit(1)

print("\n[Step 2/2] Testing data query...")
try:
    # Simple query
    df = pro.trade_cal(
        exchange='SSE',
        start_date='20240101',
        end_date='20240105'
    )

    if df.empty:
        print("[OK] Query success but no data (might be non-trading days)")
    else:
        print(f"[OK] Query success! Got {len(df)} records")
        print(df)

    print("\n" + "=" * 60)
    print("[SUCCESS] Token is working!")
    print("=" * 60)
    print("\nNext step: Integrate into system...")

except Exception as e:
    print(f"[ERROR] Query failed: {str(e)}")
    print("\nPlease check:")
    print("1. Is your account activated?")
    print("2. Do you have API calls remaining?")
    print("3. Is your token the 'Interface Token'?")

print("\n" + "=" * 60)
