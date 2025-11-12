# 量价突破顺势加仓CTA策略

## 📋 项目概述

这是一个基于ccxt.pro异步框架开发的量价突破顺势加仓CTA（交易顾问）策略。策略通过分析成交量和价格突破信号，实现自动化交易。

## 🎯 策略核心逻辑

### 1. 入场条件
- **成交量突破**：当前1分钟K线的成交量 >= R分钟平均成交量的N倍
- **价格突破**：当前1分钟K线的涨幅 >= M%
- **满足条件时**：使用Q%的资金买入

### 2. 加仓条件
- **顺势加仓**：持仓后价格相比入场价上涨 >= U%
- **每次加仓**：使用Q%的资金

### 3. 出场条件
- **移动止盈**：价格相比持仓期间最高价回撤 >= S%
- **追踪止损**：止损价格随最高价上移

## 📊 策略参数说明

| 参数 | 说明 | 默认值 | 建议范围 |
|------|------|--------|----------|
| **R** | 平均成交量计算周期（分钟） | 30 | 20-50 |
| **N** | 成交量突破倍数 | 2.0 | 1.5-3.0 |
| **M** | 入场价格涨幅阈值（%） | 1.5 | 1.0-3.0 |
| **Q** | 每次交易使用资金比例（%） | 10 | 5-20 |
| **U** | 加仓触发涨幅（%） | 2.0 | 1.5-5.0 |
| **S** | 止盈止损回撤阈值（%） | 3.0 | 2.0-5.0 |

## 🛠️ 技术架构

### 文件结构
```
ccxt_demo/
├── strategy_config.json          # 策略配置文件
├── volume_price_breakout_strategy.py  # 核心策略类
├── strategy_runner.py            # 策略执行器
├── strategy_demo.py              # 策略演示程序
├── test_strategy.py              # 策略测试脚本
├── simple_websocket_demo.py      # WebSocket演示
├── main.py                       # 币安现货期货演示
└── STRATEGY_README.md            # 本文档
```

### 核心类设计

#### `VolumePriceBreakoutStrategy` 类
```python
class VolumePriceBreakoutStrategy:
    """量价突破顺势加仓策略核心类"""

    def __init__(self, config_path: str)
    async def initialize_data(self)
    def check_entry_signal(self) -> Optional[Dict]
    def check_add_position_signal(self, position: Position) -> bool
    def check_exit_signal(self, position: Position) -> bool
    async def execute_entry(self, signal: Dict)
    async def execute_add_position(self, position: Position)
    async def execute_exit(self, position: Position)
    async def run(self)
```

#### 数据结构
```python
@dataclass
class Position:
    symbol: str
    side: OrderSide
    entry_price: float
    quantity: float
    entry_time: datetime
    highest_price: float
    stop_loss_price: float
    total_invested: float
    current_pnl: float = 0.0
```

## 🚀 使用方法

### 1. 环境准备
```bash
# 创建Python 3.11环境
uv init --python 3.11 ccxt_demo
cd ccxt_demo

# 安装依赖
uv add ccxt pandas numpy

# (可选) 如果需要WebSocket功能
uv add ccxt.pro  # 或 pip install ccxt-pro
```

### 2. 配置设置
编辑 `strategy_config.json` 文件：
```json
{
    "trading": {
        "symbol": "BTC/USDT",
        "api_key": "你的API密钥",
        "secret": "你的Secret密钥",
        "sandbox": true  # 建议先使用测试网
    },
    "parameters": {
        "R": 30,
        "N": 2.0,
        "M": 1.5,
        "Q": 10,
        "U": 2.0,
        "S": 3.0
    }
}
```

### 3. 运行策略

#### 演示模式（推荐首次使用）
```bash
uv run strategy_demo.py
```

#### 测试模式
```bash
uv run test_strategy.py
```

#### 实盘模式（谨慎使用）
```bash
uv run strategy_runner.py
```

#### 参数验证
```bash
uv run strategy_runner.py --validate
```

#### 查看策略状态
```bash
uv run strategy_runner.py --status
```

## 📈 策略特性

### 实时数据处理
- 基于ccxt.pro的WebSocket实时数据流
- 自动切换到轮询模式（WebSocket不可用时）
- 支持1分钟K线级别的实时分析

### 风险管理
- 最大持仓数量限制
- 最小/最大订单大小限制
- 移动止盈止损机制
- 资金使用比例控制

### 技术指标
- 滚动平均成交量
- 成交量突破比率
- 价格涨跌幅计算
- 持仓盈亏实时监控

### 异步架构
- 完全异步设计，高并发处理
- 支持多个持仓同时管理
- 非阻塞I/O操作

## 🧪 测试和回测

### 演示程序测试
- 使用模拟数据演示策略逻辑
- 可视化入场、加仓、出场过程
- 参数敏感性分析

### 配置验证
```bash
# 验证参数范围和配置完整性
uv run strategy_runner.py --validate
```

### 回测功能（开发中）
- 历史数据回测模块
- 多种评估指标
- 参数优化建议

## ⚠️ 风险提示

### 重要提醒
1. **强烈建议**先在测试网中充分测试
2. 实盘交易前请进行充分回测和风险评估
3. 数字货币交易存在高风险，可能导致资金损失
4. 请根据个人风险承受能力调整策略参数

### 安全注意事项
- 不要在代码中硬编码API密钥
- 使用环境变量或加密配置文件
- 设置适当的IP白名单和API权限
- 定期轮换API密钥

### 性能风险
- 网络延迟可能影响策略执行
- 极端市场条件下可能出现滑点
- 交易所API限制可能影响交易频率

## 🔧 自定义和扩展

### 参数调优
- 根据不同市场特性调整R、N、M参数
- 根据风险偏好调整Q、U、S参数
- 考虑市场波动性进行动态调整

### 策略扩展
- 添加更多技术指标（如RSI、MACD）
- 实现多时间框架分析
- 支持多种交易对同时运行
- 添加机器学习预测模型

### 交易所支持
- 当前支持币安（Binance）
- 可扩展支持其他ccxt支持的交易所
- 适配不同交易所的API特性

## 📞 支持和反馈

### 常见问题
1. **WebSocket连接失败**：自动切换到轮询模式
2. **API限流**：已内置频率限制机制
3. **网络中断**：支持自动重连机制
4. **订单失败**：支持重试和错误处理

### 技术支持
- 查看日志文件 `strategy.log`
- 检查配置文件格式
- 验证API密钥权限

## 📜 免责声明

本策略仅供学习和研究使用。数字货币交易具有极高风险，可能导致资金全部损失。使用者应：

1. 充分理解策略原理和风险
2. 在风险承受能力范围内投资
3. 遵守相关法律法规
4. 对投资决策自负其责

作者不对因使用本策略造成的任何损失承担责任。投资有风险，入市需谨慎！

---

**开发信息**
- 基于Python 3.11
- 使用ccxt/pro异步框架
- 支持pandas和numpy数据分析
- MIT License