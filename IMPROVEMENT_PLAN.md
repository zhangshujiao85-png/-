# AI 智能择时助手 - 完善计划

## 当前问题诊断

### ❌ 阻碍使用的核心问题

1. **数据源不可用** - AkShare 连接失败
2. **AI 功能未启用** - dashscope 未安装
3. **缺乏验证** - 策略有效性未验证
4. **功能不完整** - 缺少实用功能

---

## 🚀 完善方案（分阶段）

### 🔴 阶段一：修复数据源（必须，1-2天）

#### 方案 A：使用 Tushare（推荐）

**优点：**
- ✅ 稳定可靠
- ✅ 数据质量高
- ✅ 免费额度足够（200次/分钟）
- ✅ 官方文档完善

**步骤：**
```bash
# 1. 注册 Tushare
# 访问：https://tushare.pro/register
# 获取 Token（免费）

# 2. 安装
pip install tushare

# 3. 修改代码
# 在 config/settings.py 添加：
TUSHARE_TOKEN = "你的token"

# 4. 替换数据获取模块
# 使用 ts.pro_bar() 替代 ak.stock_zh_a_hist()
```

**代码示例：**
```python
import tushare as ts

def get_real_index_data(code, period=250):
    ts.set_token('your_token')
    pro = ts.pro_api()

    df = pro.index_daily(ts_code=code, start_date='20240101')
    return df
```

#### 方案 B：使用本地数据文件

**优点：**
- ✅ 不依赖网络
- ✅ 速度快
- ✅ 完全可控

**步骤：**
```python
# 1. 下载历史数据到本地
# 2. 存储为 CSV/Parquet 文件
# 3. 系统读取本地文件

# 示例结构：
data/
├── index_daily/
│   ├── 000001.csv  # 上证指数历史数据
│   ├── 399001.csv
│   └── 399006.csv
└── stock_daily/
    └── 600519.csv
```

#### 方案 C：使用付费数据源（适合实盘）

- Wind（万得）- 金融级
- Choice（东方财富）- 专业级
- Bloomberg - 国际级

---

### 🟡 阶段二：完善核心功能（重要，2-3天）

#### 1. 添加更多技术指标

```python
# 当前的指标
- MACD, RSI, KDJ, MA

# 建议添加
- 布林带 (BOLL)
- 威廉指标 (WR)
- 乖离率 (BIAS)
- 成交量变化率 (VOL)
- ATR (真实波幅)
```

#### 2. 优化择时算法

```python
# 当前问题
- 阈值固定（70/40）

# 改进方案
- 动态阈值（根据市场波动率调整）
- 市场环境分类（牛市/熊市不同策略）
- 止损优化（ATR 止损、时间止损）
```

#### 3. 添加风控模块

```python
class RiskManager:
    """风险管理模块"""

    def check_position_limit(self):
        """检查持仓限制"""
        # 单只股票不超过 10%
        # 总仓位不超过 80%

    def check_stop_loss(self, position):
        """检查止损"""
        # 亏损 -5% 强制平仓

    def check_market_risk(self):
        """检查市场风险"""
        # 大盘暴跌时清仓
```

---

### 🟢 阶段三：回测验证（关键，3-5天）

#### 为什么必须回测？

没有回测的策略就像"盲人摸象"，需要验证：

1. **历史表现** - 过去收益如何？
2. **最大回撤** - 最坏情况亏损多少？
3. **夏普比率** - 风险调整后收益
4. **胜率** - 盈利交易占比

#### 回测框架选择

**方案 A：使用 Backtrader（推荐）**

```python
import backtrader as bt

class TimingStrategy(bt.Strategy):
    def __init__(self):
        self.timing_analyzer = TimingAnalyzer()

    def next(self):
        # 每个交易日调用
        signal = self.timing_analyzer.analyze(
            self.data._name,
            market_regime
        )

        if signal.action == 'buy':
            self.buy()
        elif signal.action == 'sell':
            self.sell()
```

**方案 B：自己写简单回测**

```python
def backtest_strategy(signals, prices):
    """
    signals: 买卖信号列表
    prices: 价格数据
    """
    capital = 100000  # 初始资金
    position = 0      # 持仓

    for i, signal in enumerate(signals):
        if signal == 'buy' and position == 0:
            position = capital // prices[i]
        elif signal == 'sell' and position > 0:
            capital = position * prices[i]
            position = 0

    return capital  # 最终资金
```

---

### 🔵 阶段四：实用功能（可选，2-3天）

#### 1. 添加通知功能

```python
def send_alert(signal):
    """发送提醒"""
    # 钉钉
    # 微信
    # 邮件
    # 短信
```

#### 2. 添加持仓管理

```python
class PositionManager:
    """持仓管理"""

    def add_position(self, stock, quantity, price):
        """买入建仓"""

    def remove_position(self, stock, quantity, price):
        """卖出减仓"""

    def get_pnl(self):
        """计算盈亏"""
```

#### 3. 添加交易日志

```python
class TradingLogger:
    """交易日志"""

    def log_signal(self, signal):
        """记录信号"""

    def log_trade(self, trade):
        """记录成交"""

    def generate_report(self):
        """生成报告"""
```

---

### 🟣 阶段五：AI 功能增强（可选，2-3天）

#### 1. 启用千问 AI

```bash
# 安装
pip install dashscope

# 配置
echo DASHSCOPE_API_KEY=your_key > .env

# 测试
python -c "import dashscope; print('OK')"
```

#### 2. 增强 AI 能力

```python
class AIAnalyst:
    """AI 分析师"""

    def analyze_news(self, stock_code):
        """分析新闻情绪"""
        # 调用新闻 API
        # NLP 情感分析
        # 生成建议

    def analyze_report(self, stock_code):
        """分析财报"""
        # 提取财务数据
        # AI 解读财报
        # 生成解读

    def chat_qa(self, question):
        """智能问答"""
        # 用户可以问：
        # - "为什么推荐这只股票？"
        # - "风险大吗？"
        # - "什么时候买？"
```

---

### ⚫ 阶段六：实盘对接（高风险，需谨慎）

#### ⚠️ 重要警告

实盘交易需要：
1. **合法资质** - 证券从业资格
2. **模拟验证** - 至少 6 个月回测
3. **风险备案** - 风险揭示书
4. **监管合规** - 符合监管要求

#### 如果真要对接

```python
# 使用券商接口
- 华泰证券
- 国金证券
- 东方财富

# 或使用量化交易平台
- 聚宽（UQER）
- 迅投
- 米筐RQAlpha
```

---

## 📊 优先级排序

### 🔴 必须做（核心功能）
1. ✅ 修复数据源 - 使用 Tushare 或本地数据
2. ✅ 添加回测验证 - 证明策略有效
3. ✅ 优化择时算法 - 提高胜率

### 🟡 推荐做（提升体验）
4. ✅ 启用 AI 功能 - 安装 dashscope
5. ✅ 添加风控模块 - 风险管理
6. ✅ 界面优化 - 更好的可视化

### ⚪ 可选做（锦上添花）
7. ⭕ 通知功能 - 交易提醒
8. ⭕ 持仓管理 - 完整账户管理
9. ⭕ 智能问答 - 对话式交互

---

## 🎯 立即可做的事（今天就能完成）

### 1. 使用 Tushare 获取真实数据（1小时）

```python
# 安装
pip install tushare

# 修改 data/market_data.py
import tushare as ts

def get_index_data_real(self, code, period=250):
    pro = ts.pro_api('your_token')
    df = pro.index_daily(
        ts_code=f"{code}.SH" if code.startswith('00') else f"{code}.SZ",
        start_date='20240101'
    )
    return df
```

### 2. 添加简单回测（2小时）

```python
# 新建 analysis/backtest.py
def simple_backtest():
    """简单回测"""
    signals = []  # 存储历史信号

    # 模拟交易
    capital = 100000
    for i in range(len(signals) - 1):
        if signals[i] == 'buy':
            # 买入
            shares = capital // prices[i]
            capital = capital - shares * prices[i]
        elif signals[i] == 'sell':
            # 卖出
            capital = capital + shares * prices[i]

    return capital
```

### 3. 启用 AI 功能（30分钟）

```bash
pip install dashscope
echo DASHSCOPE_API_KEY=your_key > .env
```

---

## 💡 我的建议

### 优先级 1：修复数据源（最重要）

**原因：**
- 没有真实数据，一切都是空谈
- 模拟数据无法验证策略
- 面试时也会被质疑

**行动：**
今天就用 Tushare，1 小时搞定

### 优先级 2：添加回测（关键）

**原因：**
- 证明策略有效
- 给面试官看数据
- 自己也有信心

**行动：**
周末完成简单回测

### 优先级 3：启用 AI（亮点）

**原因：**
- 这是面试的亮点
- 展示 AI 能力
- 提升报告质量

**行动：**
有 time 就做，10 分钟搞定

---

## 📝 总结

### 最小可行方案（MVP）

**1 周内完成：**
1. ✅ Tushare 数据源
2. ✅ 简单回测
3. ✅ 安装 dashscope
4. ✅ 测试完整流程

**效果：**
- ✅ 真实数据
- ✅ 验证有效
- ✅ AI 增强完成
- ✅ 可以演示

### 如果想更完善（1-2周）

再添加：
- 完整回测系统
- 风控模块
- 交易日志
- 界面优化
- 更多技术指标

---

## 🚀 现在就开始？

我建议先做**阶段一**和**阶段三**：

**1. 使用 Tushare 获取真实数据**
**2. 添加简单回测验证**

这两个完成后，系统就真正可用了！

**需要我帮您实现吗？**

可以选择：
A. 帮您集成 Tushare 数据源
B. 帮您添加回测功能
C. 两个都做
D. 给您详细代码自己实现
