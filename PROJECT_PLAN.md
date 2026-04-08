# 短线情绪择时助手 - 完整项目方案

> 项目路径：`D:\ai_timing_assistant`
> 更新时间：2025-04-08
> 下次启动：告诉 Claude "读取 D:\ai_timing_assistant\PROJECT_PLAN.md 继续开发"

---

## 📋 项目概述

**系统名称**：短线情绪择时助手

**核心定位**：
- 基于市场情绪 + 重大事件驱动的短线波段交易辅助系统
- **只提示不操作**，用户自主决策
- 不做基本面分析（PE、ROE等），只看情绪和资金

**差异化优势**：
- ✅ 具体股票推荐（不是泛泛的板块）
- ✅ 个性化持仓配置（根据资金量）
- ✅ 3套止盈止损方案 + 历史胜率
- ✅ 实时砸盘预警 + 操作建议
- ✅ 持仓全天候监控

---

## 🎯 核心功能清单

### 1. 重大事件识别（半自动）
**用户输入关键词 → 系统自动分析**

```python
# 流程
用户输入："美以冲突"
  ↓
系统自动搜索相关新闻
  ↓
AI分析内容，判断：
  - 事件类型（地缘/政策/行业/监管）
  - 影响板块（军工/石油/黄金等）
  - 情绪倾向（利好/利空）
  ↓
开始监控相关板块情绪
```

**事件类型**：
- 地缘冲突：战争、制裁、外交摩擦
- 宏观政策：货币政策、财政政策、监管政策
- 行业突发：行业利好/利空、重大技术突破
- 监管公告：IPO、再融资、停复牌、退市

**事件-板块映射**：
```python
EVENT_SECTOR_MAPPING = {
    '地缘冲突': {
        '军工': '利好',
        '石油': '利好',
        '黄金': '利好',
        '航运': '利空'
    },
    '降息': {
        '银行': '中性',
        '地产': '利好',
        '成长股': '利好'
    },
    'AI突破': {
        '半导体': '利好',
        '软件': '利好',
        '传媒': '利好'
    }
}
```

---

### 2. 市场情绪评分（三大维度）

**综合评分公式**：
```python
总得分 = 市场宽度得分 × 35% + 资金流向得分 × 40% + 波动率得分 × 25%
```

#### 2.1 市场宽度（35%权重）
- 涨跌家数比
- 涨跌停比
- 上涨家数占比

#### 2.2 资金流向（40%权重）
- 北向资金净流入
- 主力资金净流入
- 超大单净流入

#### 2.3 波动率（25%权重）
- 20日历史波动率
- 波动率百分位
- 波动率状态

**市场状态分类**：
- ≥80分：极度贪婪
- ≥65分：贪婪
- ≥45分：中性
- ≥30分：恐慌
- <30分：极度恐慌

---

### 3. 双模式运行

#### 模式1：事件驱动（有重大事件）

```python
# 建仓信号触发条件
if 事件存在 and 板块情绪分 > 60:
    触发建仓提示

# 空仓信号触发条件
if 板块情绪分 < 60:
    触发空仓提示

# 持续监控
while 事件热度未消散:
    实时更新板块情绪分
    if 情绪分跌破60:
        立即弹出预警
```

#### 模式2：轮动捕捉（无重大事件）

**捕捉4类短线机会**：

1. **板块轮动识别**
   - 计算所有板块情绪得分
   - 捕捉情绪突然升温的板块（单日提升>15分）
   - 提示："XX板块情绪突然升温（55→75分）"

2. **突破形态**
   - 股价突破60日高点
   - 成交量放大（>1.5倍）
   - 站稳支撑位

3. **资金异动**
   - 主力资金净流入>5000万
   - 连续3天流入
   - 股价涨幅<5%（还没涨起来）

4. **超跌反弹**
   - 10日跌幅>20%
   - 近2日企稳
   - 出现止跌信号

---

### 4. 选股推荐

**不做财务分析，只看情绪和资金**

```python
def select_representative_stocks(sector_name, top_n=5):
    """
    选取板块代表性股票
    """
    # 综合评分（不看PE/ROE）
    score = (
        情绪得分 × 0.3 +
        资金流向 × 0.3 +
        市值（选龙头）× 0.2 +
        活跃度 × 0.2
    )

    # 股票分类
    if 市值>500亿 and 成交量稳定:
        type = '稳定型'  # 如中国石油
    elif 市值>500亿 and 成交量波动大:
        type = '敏感型'  # 如中国海油
    elif 市值<200亿 and 成交活跃:
        type = '活跃型'  # 小盘股

    return Top 5股票
```

**输出示例**：
```
📊 半导体板块 Top 5：

1. 600460 土兰微（78分）- 活跃型
2. 603986 兆易创新（75分）- 活跃型
3. 688981 中芯国际（72分）- 稳定型
4. 002049 紫光国微（70分）- 敏感型
5. 300343 联创股份（68分）- 活跃型
```

---

### 5. 持仓配置建议

**根据用户资金量和风险偏好**

```python
# 用户输入
投资资金：10万元
风险偏好：稳健型

# 生成配置
1️⃣ 稳定型（30%，3万元）
   688981 中芯国际 - 400股
   理由：大市值龙头，防守型配置

2️⃣ 敏感型（40%，4万元）
   002049 紫光国微 - 500股
   理由：对市场情绪敏感，弹性大

3️⃣ 活跃型（30%，3万元）
   600460 土兰微 - 1000股（15%）
   300343 联创股份 - 1200股（15%）
   理由：小盘活跃股，进攻型配置
```

**风险偏好模板**：
- 保守：稳定50% + 敏感30% + 活跃20%
- 稳健：稳定30% + 敏感40% + 活跃30%
- 激进：稳定20% + 敏感30% + 活跃50%

---

### 6. 止盈止损方案（3套+胜率）

**每只股票提供3套方案**

```python
方案 = {
    '保守型': {
        '止损价': 买入价 - ATR×1,
        '止盈价': 买入价 × 1.08,
        '最多持有': 3天,
        '历史胜率': 72.5%,
        '盈亏比': 1.6,
        '平均盈利': +7.8%,
        '平均亏损': -4.9%
    },
    '稳健型': {
        '止损价': 买入价 - ATR×1.5,
        '止盈价': 买入价 × 1.15,
        '最多持有': 7天,
        '历史胜率': 61.3%,
        '盈亏比': 2.1
    },
    '激进型': {
        '止损价': 买入价 - ATR×2,
        '止盈价': 买入价 × 1.25,
        '最多持有': 10天,
        '历史胜率': 48.7%,
        '盈亏比': 2.8
    }
}
```

**用户选择方案后，系统按方案监控持仓**

---

### 7. 简化版阶梯仓位管理

```python
def calculate_position(event_heat, sector_sentiment):
    if event_heat == '无':
        return 0  # 无事件，不建仓

    elif event_heat == '升温':
        if sector_sentiment > 60:
            return 50  # 事件升温 + 情绪向好 → 50%仓位
        else:
            return 0

    elif event_heat == '爆发':
        if sector_sentiment > 70:
            return 100  # 事件爆发 + 情绪高涨 → 100%仓位
        elif sector_sentiment > 60:
            return 70
        else:
            return 0
```

**事件热度判断**：
- 事件天数（越新越热）
- 新闻数量（越多越热）
- 板块情绪变化（升温越快越热）

---

### 8. 盘中实时监控

**监控时间表**：
- 盘前：09:00（先行指标分析）
- 盘中：每5分钟（实时监控）
- 盘后：15:05（复盘）

**监控内容**：
1. 市场情绪数据
2. 板块情绪数据
3. 持仓股票价格
4. 异常情况检测

**先行指标预警**：
```python
# A50期货（提前15分钟开盘）
if A50 > +2%:
    alert("⚠️ A50大涨+2%，A股可能高开")
elif A50 < -2%:
    alert("⚠️ A50大跌-2%，A股可能低开")

# 隔夜美股（中概股表现）
if 中概股 > +3%:
    alert("⚠️ 中概股大涨+3%，A股或受提振")
elif 中概股 < -3%:
    alert("⚠️ 中概股大跌-3%，A股或承压")
```

---

### 9. 异常情况熔断（仅提醒）

**检测4类异常**：

1. **极端砸盘**（5分钟内跌超3%）
   ```
   ⛔ 600519 5分钟内暴跌超3%，请立即关注！
   建议：建议立即查看持仓，考虑止损
   ```

2. **涨停/跌停**
   ```
   🔺 600460 已涨停，请考虑是否止盈
   建议：建议关注是否打开涨停
   ```

3. **跌破止损价**
   ```
   ⚠️ 600519 跌破止损价 1550.0，当前价 1548.5
   建议：建议考虑止损
   ```

4. **到达目标价**
   ```
   ✅ 600519 到达目标价 1800.0，当前价 1802.3
   建议：建议考虑止盈
   ```

**所有预警只弹窗提醒，绝不代替用户操作**

---

### 10. 事件驱动砸盘预警

**配合盘前分析，识别4类风险**：

1. **A50大跌预警**
   ```
   ⚠️ A50期货大跌-2.5%，可能低开
   建议：建议集合竞价观察，若低开超-2%则暂不建仓
   ```

2. **中概股大跌预警**
   ```
   ⚠️ 隔夜中概股大跌-3.2%，情绪承压
   建议：建议观望，等待市场情绪稳定
   ```

3. **事件过期预警**
   ```
   ⚠️ 事件已发生3天，利好可能出尽
   建议：警惕"利好出尽是利空"，建议逐步减仓或空仓
   ```

4. **高开低走预警**
   ```
   ⛔ 高开+3%但回落至+1%
   典型"利好出尽"形态，建议立即止盈或止损
   ```

**综合风险等级**：
- 高：多重风险叠加，强烈建议空仓
- 中：存在风险，建议谨慎操作
- 低：暂无风险，正常操作

---

### 11. 持仓管理（类似"养基宝"）

**用户手动记录持仓**：
```python
持仓信息 = {
    'stock_code': '600519',
    'stock_name': '贵州茅台',
    'buy_price': 1650.0,
    'buy_date': '2025-04-08',
    'quantity': 100,
    'target_price': 1800.0,
    'stop_loss': 1550.0,
    'related_event': '降息',
    'selected_plan': '稳健型'  # 用户选择的止盈止损方案
}
```

**全天候监控**：
- 实时更新当前价格
- 计算实时盈亏
- 检查止盈止损条件
- 检查持仓天数
- 检查关联事件情绪
- 检查异常情况

**数据持久化**（JSON存储）

---

### 12. Web界面

**5个主要页面**：

1. **事件监控面板**
   - 输入事件关键词
   - 显示当前活跃事件
   - 显示影响板块
   - 盘前分析
   - 砸盘风险预警

2. **情绪仪表板**
   - 市场情绪总评分
   - 三大维度得分
   - 板块情绪排行榜
   - 历史趋势图

3. **持仓管理**
   - 添加持仓表单
   - 持仓列表展示
   - 实时盈亏显示
   - 预警信息展示

4. **板块扫描**
   - 热门板块列表
   - 板块代表股票
   - 板块情绪趋势

5. **预警中心**
   - 预警历史记录
   - 预警统计分析

**自动刷新**：每5分钟（可开关）

---

## 📁 文件结构

### 新增文件（28个）

```
D:\ai_timing_assistant\
├── sentiment/                    # 情绪分析模块
│   ├── __init__.py
│   ├── market_breadth.py        # 市场宽度分析
│   ├── money_flow.py            # 资金流向分析
│   ├── volatility.py            # 波动率分析
│   ├── sector_sentiment.py      # 板块情绪分析
│   └── sentiment_scorer.py      # 综合情绪评分
│
├── news/                        # 新闻事件分析模块
│   ├── __init__.py
│   ├── event_analyzer.py        # 事件分析器
│   ├── sector_mapper.py         # 事件-板块映射
│   └── news_fetcher.py          # 新闻获取器
│
├── monitor/                     # 实时监控模块
│   ├── __init__.py
│   ├── realtime_monitor.py      # 实时监控引擎
│   ├── circuit_breaker.py       # 异常熔断引擎
│   ├── leading_indicator.py     # 先行指标分析
│   └── alert_manager.py         # 预警管理器
│
├── portfolio/                   # 持仓管理模块
│   ├── __init__.py
│   ├── position_manager.py      # 持仓管理器
│   ├── position_monitor.py      # 持仓监控器
│   └── storage.py               # 持仓存储（JSON）
│
├── selector/                    # 选股配置模块
│   ├── __init__.py
│   ├── stock_selector.py        # 股票选择器
│   ├── allocation.py            # 持仓配置生成
│   └── stop_loss_plans.py       # 止盈止损方案
│
├── timing/                      # 择时模块
│   ├── __init__.py
│   ├── signal_generator.py      # 信号生成器
│   └── ladder_strategy.py       # 阶梯策略
│
└── web/                         # Web界面
    ├── app.py                   # Streamlit主应用
    ├── pages/
    │   ├── event_monitor.py     # 事件监控面板
    │   ├── sentiment_dashboard.py  # 情绪仪表板
    │   ├── portfolio.py         # 持仓管理页面
    │   ├── sector_scanner.py    # 板块扫描页面
    │   └── alert_center.py      # 预警中心页面
    └── components/
        ├── event_card.py        # 事件卡片组件
        ├── sentiment_gauge.py   # 情绪仪表盘
        ├── position_table.py    # 持仓表格
        ├── allocation_card.py   # 配置卡片组件
        ├── stop_loss_selector.py # 止损方案选择器
        └── alert_popup.py       # 预警弹窗组件
```

### 修改文件（4个）

```
D:\ai_timing_assistant\
├── data/
│   └── market_data.py          # 扩展：新增板块数据、实时行情
├── config/
│   └── settings.py             # 扩展：新增监控、持仓配置
├── main.py                     # 修改：命令行入口
└── requirements.txt            # 扩展：新增依赖
```

---

## 📝 实施步骤

### Phase 1: 基础架构（第1-3天）

**任务**：
1. 创建目录结构
2. 扩展数据层（`market_data.py`）
   - `get_sector_data(sector_name)` - 获取板块数据
   - `get_sector_constituents(sector_name)` - 获取板块成分股
   - `get_realtime_quote(stock_code)` - 获取实时行情
   - `get_pre_market_data()` - 获取盘前数据（A50、美股）

**验证**：
```bash
python -c "from data.market_data import MarketDataFetcher; f = MarketDataFetcher(); print(f.get_sector_data('军工'))"
```

---

### Phase 2: 情绪分析模块（第4-8天）

**任务**：
1. `market_breadth.py` - 市场宽度分析
2. `money_flow.py` - 资金流向分析
3. `volatility.py` - 波动率分析
4. `sector_sentiment.py` - 板块情绪分析
5. `sentiment_scorer.py` - 综合情绪评分

**验证**：
```bash
python -c "from sentiment.sentiment_scorer import SentimentScorer; s = SentimentScorer(); score = s.calculate_overall_sentiment(); print(f'得分: {score.sentiment_score:.0f}')"
```

---

### Phase 3: 新闻事件分析（第9-12天）

**任务**：
1. `sector_mapper.py` - 事件-板块映射表
2. `event_analyzer.py` - 事件分析器（半自动）
3. `news_fetcher.py` - 新闻获取器

**实现**：
- 用户输入关键词
- 搜索相关新闻
- AI分析内容（可选，或用规则引擎）
- 返回事件类型、影响板块

---

### Phase 4: 选股配置模块（第13-17天）

**任务**：
1. `stock_selector.py` - 股票选择器
   - 综合评分（情绪+资金+市值+活跃度）
   - 股票分类（稳定/敏感/活跃）

2. `allocation.py` - 持仓配置生成
   - 根据资金量和风险偏好
   - 生成具体配置（股数、金额）

3. `stop_loss_plans.py` - 止盈止损方案
   - 3套方案（保守/稳健/激进）
   - 回测历史胜率
   - 计算盈亏比

---

### Phase 5: 实时监控模块（第18-22天）

**任务**：
1. `realtime_monitor.py` - 实时监控引擎
   - 5分钟更新一次
   - 监控交易时间
   - 更新情绪数据
   - 监控持仓

2. `leading_indicator.py` - 先行指标分析
   - A50期货监控
   - 美股中概股监控
   - 亚太市场监控
   - 生成盘前预警

3. `circuit_breaker.py` - 异常熔断引擎
   - 极端砸盘检测
   - 止损/止盈检测
   - 涨停/跌停检测

4. `alert_manager.py` - 预警管理器
   - 预警分级（CRITICAL/WARNING/INFO）
   - 预警弹窗
   - 预警历史记录

---

### Phase 6: 持仓管理模块（第23-25天）

**任务**：
1. `position_manager.py` - 持仓管理器
   - 添加/删除持仓
   - 更新持仓价格

2. `position_monitor.py` - 持仓监控器
   - 全天候监控
   - 实时盈亏计算
   - 检查预警条件

3. `storage.py` - 数据存储
   - JSON持久化
   - 数据导入/导出

---

### Phase 7: Web界面开发（第26-33天）

**任务**：
1. `app.py` - 主应用框架
2. `event_monitor.py` - 事件监控面板
3. `sentiment_dashboard.py` - 情绪仪表板
4. `portfolio.py` - 持仓管理页面
5. `sector_scanner.py` - 板块扫描页面
6. `alert_center.py` - 预警中心页面
7. 各组件开发

**验证**：
```bash
cd D:\ai_timing_assistant
streamlit run web/app.py
```

---

### Phase 8: 集成与测试（第34-38天）

**任务**：
1. 集成所有模块
2. 完整流程测试
3. 性能优化
4. Bug修复
5. 文档完善

---

## 🔧 关键技术决策

### 1. 数据源

| 数据需求 | 数据源 | 成本 |
|---------|-------|------|
| 行情数据 | AkShare | 免费 |
| 板块数据 | AkShare | 免费 |
| 实时行情 | AkShare | 免费 |
| 盘前数据 | 东方财富 | 免费 |
| 新闻搜索 | Web API | 免费 |

### 2. 更新频率

| 数据类型 | 更新频率 | 说明 |
|---------|---------|------|
| 市场情绪 | 5分钟 | 盘中实时 |
| 板块情绪 | 5分钟 | 盘中实时 |
| 持仓监控 | 5分钟 | 盘中实时 |
| 先行指标 | 9:00 | 盘前一次 |
| 事件热度 | 每日 | 每天更新 |

### 3. 预警级别

| 级别 | 触发条件 | 提示方式 |
|-----|---------|---------|
| CRITICAL | 极端砸盘、崩盘 | 红色弹窗 |
| WARNING | 跌破止损、情绪转弱 | 黄色提示 |
| INFO | 到达目标价、涨停 | 蓝色提示 |

### 4. 合规原则

**绝对遵守**：
- ✅ 只提示不操作
- ✅ 用户自主决策
- ✅ 明确风险提示
- ✅ 不承诺收益

---

## ⚠️ 关键边界（不做的事项）

- ❌ 不做价值投资分析（PE、ROE等）
- ❌ 不做财务报表分析
- ❌ 不做长期主题追踪（只捕捉短期变化）
- ❌ 不代替用户操作
- ❌ 不做自动交易
- ❌ 不承诺收益

---

## 📊 预期成果

### 功能交付

1. **事件监控面板** 📰
2. **情绪仪表板** 📊
3. **持仓管理** 📋
4. **实时监控** ⏰
5. **预警中心** 🔔
6. **选股配置** 🎯
7. **砸盘预警** ⚠️

### 性能指标

- 数据更新：5分钟/次
- 扫描速度：< 30秒
- 界面响应：< 3秒
- 预警延迟：< 10秒

### 代码规模

- 新增代码：约6500行
- 新增文件：28个
- 修改文件：4个

---

## 🚀 开发时间表

| 阶段 | 任务 | 天数 |
|-----|------|------|
| Phase 1 | 基础架构 | 3天 |
| Phase 2 | 情绪分析 | 5天 |
| Phase 3 | 新闻事件 | 4天 |
| Phase 4 | 选股配置 | 5天 |
| Phase 5 | 实时监控 | 5天 |
| Phase 6 | 持仓管理 | 3天 |
| Phase 7 | Web界面 | 8天 |
| Phase 8 | 集成测试 | 5天 |
| **总计** | | **38天** |

---

## 📌 关键文件清单

### 核心文件（10个）

1. `sentiment/sentiment_scorer.py` - 综合情绪评分
2. `sentiment/sector_sentiment.py` - 板块情绪分析
3. `news/event_analyzer.py` - 事件分析器
4. `selector/stock_selector.py` - 股票选择器
5. `selector/allocation.py` - 持仓配置
6. `selector/stop_loss_plans.py` - 止盈止损方案
7. `monitor/realtime_monitor.py` - 实时监控
8. `monitor/circuit_breaker.py` - 异常熔断
9. `portfolio/position_manager.py` - 持仓管理
10. `web/pages/portfolio.py` - Web主界面

### 需要修改的文件（3个）

1. `data/market_data.py` - 扩展数据获取
2. `config/settings.py` - 新增配置
3. `requirements.txt` - 新增依赖

---

## ✅ 验证方法

### 功能测试

```bash
# 1. 测试情绪评分
python -c "
from sentiment.sentiment_scorer import SentimentScorer
s = SentimentScorer()
score = s.calculate_overall_sentiment()
print(f'得分: {score.sentiment_score:.0f}')
"

# 2. 测试事件分析
python -c "
from news.event_analyzer import EventAnalyzer
a = EventAnalyzer()
event = a.analyze_event('美以冲突')
print(event)
"

# 3. 测试选股
python -c "
from selector.stock_selector import StockSelector
s = StockSelector()
stocks = s.select_representative_stocks('半导体', top_n=5)
for stock in stocks:
    print(f\"{stock['code']} {stock['name']} - {stock['score']:.0f}分\")
"

# 4. 测试持仓配置
python -c "
from selector.allocation import AllocationGenerator
from selector.stock_selector import StockSelector
stock_selector = StockSelector()
stocks = stock_selector.select_representative_stocks('半导体', top_n=5)
allocator = AllocationGenerator()
allocation = allocator.generate_allocation(100000, '稳健', stocks)
print(allocation)
"

# 5. 启动Web界面
cd D:\ai_timing_assistant
streamlit run web/app.py
```

---

## 📞 下次启动说明

**如何继续开发**：

方法1：告诉 Claude
```
"读取 D:\ai_timing_assistant\PROJECT_PLAN.md 继续开发"
```

方法2：只告诉项目路径
```
"继续开发 D:\ai_timing_assistant 项目"
```

方法3：直接说具体任务
```
"开始实现 Phase 1：基础架构"
```

---

**项目准备好了！让我们开始构建"短线情绪择时助手"！** 🚀
