"""
Tushare Token 测试脚本
用于诊断 Token 问题
"""
import tushare as ts

def test_token():
    """测试 Token 是否有效"""
    token = "6c79351c2732628d7efdcd306d46acfa2622d00a580949b4fc8ccef7"

    print("=" * 60)
    print("Tushare Token 测试")
    print("=" * 60)

    print(f"Token: {token[:8]}...{token[-8:]}")  # 只显示前后8位
    print(f"Token 长度: {len(token)} 位")

    # 设置 token
    ts.set_token(token)

    print("\n[测试 1/3] 初始化 Pro API...")
    try:
        pro = ts.pro_api()
        print("✅ Pro API 初始化成功")
    except Exception as e:
        print(f"❌ Pro API 初始化失败: {e}")
        return False

    # 测试1：最简单的查询
    print("\n[测试 2/3] 测试交易日历查询...")
    try:
        df = pro.trade_cal(
            exchange='SSE',  # 上海证券交易所
            start_date='20240101',
            end_date='20240105'
        )

        if df.empty:
            print("⚠️  查询成功但无数据（可能是非交易日）")
        else:
            print(f"✅ 查询成功！获取到 {len(df)} 条数据")

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False

    # 测试2：查询股票数据
    print("\n[测试 3/3] 测试股票数据查询...")
    try:
        df = pro.daily(
            ts_code='000001.SZ',  # 上证指数
            start_date='20240101',
            end_date='20240105'
        )

        if df.empty:
            print("⚠️  查询成功但无数据")
        else:
            print(f"✅ 查询成功！获取到 {len(df)} 条数据")
            print(f"最新日期: {df['trade_date'].iloc[-1]}")
            print(f"最新收盘: {df['close'].iloc[-1]:.2f}")

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 所有测试通过！Token 正常工作！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_token()

    if success:
        print("\n下一步：集成到系统中...")
    else:
        print("\n❌ Token 有问题，请检查：")
        print("1. Token 是否正确复制？")
        print("2. 账号是否激活？")
        print("3. 是否有调用权限？")
        print("4. 是否需要实名认证？")
