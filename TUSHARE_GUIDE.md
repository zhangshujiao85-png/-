# Tushare 配置指南 - 3步即可

## 第一步：配置 Token（2分钟）

### 方法 A：创建 .env 文件（推荐）

```bash
# 在 D:\ai_timing_assistant 目录创建 .env 文件
cd D:\ai_timing_assistant

# 创建 .env 文件并添加 Token
echo TUSHARE_TOKEN=你的32位token > .env
```

### 方法 B：设置环境变量（临时）

```bash
# Windows CMD
set TUSHARE_TOKEN=你的token

# Windows PowerShell
$env:TUSHARE_TOKEN="你的token"

# 或者直接在代码中设置（修改 config/settings.py）
```

---

## 第二步：安装 Tushare（1分钟）

```bash
cd D:\ai_timing_assistant
pip install tushare
```

---

## 第三步：测试数据获取（2分钟）

```bash
cd D:\ai_timing_assistant
python -c "
import tushare as ts
import os

# 设置 token
token = '你的token'
ts.set_token(token)
pro = ts.pro_api()

# 测试获取上证指数数据
df = pro.index_daily(ts_code='000001.SH', start_date='20240101')
print(f'✅ 成功获取 {len(df)} 条数据')
print(df.head())
"
```

---

## 如果成功

您会看到：
```
✅ 成功获取 250+ 条数据
     ts_code       trade_date     open    high     low    close        vol
0  000001.SH  2024-01-02  2962.31  ...  ...  ...  ...  ...
```

然后：

1. **重启 Streamlit 应用**
2. **刷新浏览器**
3. **查看真实数据！**

---

## 快速验证（一键测试）

创建一个测试脚本：

```python
# test_tushare.py
import tushare as ts

token = "你的token"
ts.set_token(token)
pro = ts.pro_api()

# 获取上证指数
df = pro.index_daily(ts_code='000001.SH', start_date='20240101')
print(f"上证指数: {len(df)} 条数据")
print(df[['trade_date', 'close']].tail())

# 获取股票数据
df2 = pro.daily(ts_code='600519.SH', start_date='20240101')
print(f"\n贵州茅台: {len(df2)} 条数据")
print(df2[['trade_date', 'close', 'vol']].tail())
```

---

## 需要帮助？

**告诉我：**
- "我的 Token 是：xxxxxxxx"（我会帮您配置）
- "测试失败了，错误信息是：xxx"
- "怎么查看我的 Token？"

**我会立即帮您解决！**
