# 📺 TV Remote MCP Server

**Claude Code's UNIVERSAL REMOTE - ONE TOOL that controls everything**

A revolutionary Model Context Protocol (MCP) server that provides Claude Code with complete control over the EzBot trading system through natural language commands.

## 🎯 **Core Philosophy**

Just like a TV remote controls all channels and functions through simple buttons, the TV Remote MCP gives Claude Code complete control over the entire trading system through natural language commands.

**ONE TOOL. ALL CONTROL.**

## 🚀 **Features**

### 📊 **Market Intelligence**
- **Real-time market data** from all 16 data feeds through QuestDB
- **Options flow analysis** with unusual activity detection
- **Crypto correlation tracking** and cross-asset analysis
- **News sentiment analysis** with momentum detection
- **Technical indicator calculations** and pattern recognition

### 🎯 **Trading Strategies**
- **Options strategies**: 0DTE iron condors, earnings IV crush, gamma squeeze detection
- **Stock strategies**: RSI mean reversion, gap fills, news momentum, VWAP reversion
- **ETF strategies**: Sector rotation, VIX products, pairs trading
- **Crypto strategies**: BTC-SPY correlation, weekend gaps, mean reversion

### 💹 **Trade Execution**
- **Stock orders**: Market, limit, stop, stop-limit orders
- **Options orders**: Single leg and complex multi-leg strategies
- **Portfolio management**: Position sizing, rebalancing, stop losses
- **Risk management**: Real-time portfolio risk analysis

### 🛡️ **Risk Management**
- **Scenario analysis**: Market crash, volatility spike, correlation breakdown
- **Portfolio monitoring**: Real-time exposure tracking
- **Position sizing**: Intelligent capital allocation
- **Correlation analysis**: Cross-position risk assessment

## 🔧 **Installation**

```bash
cd /home/ezb0t/ezbot/mcp/tv_remote
pip install -r requirements.txt
python server.py
```

## 🎮 **Usage Examples**

### Market Intelligence Commands
```python
# Find trading opportunities
"Find unusual options activity in tech stocks with earnings this week"
"Show me RSI mean reversion opportunities in current market conditions"
"Identify crypto patterns that predict Monday equity gaps"
"What sectors are rotating based on ETF flows?"
```

### Trade Execution Commands
```python
# Execute trades
"Buy 100 shares of AAPL at market price"
"Sell 10 SPY 520 calls expiring today"
"Execute iron condor on QQQ with 30 delta strikes"
"Close all positions in TSLA"
```

### Portfolio Management Commands
```python
# Manage portfolio
"Show my current positions and P&L"
"What's my portfolio risk if SPY drops 10% and VIX spikes to 40?"
"Rebalance portfolio to 60/40 stocks/options"
"Set stop losses on all positions at 2% below current price"
```

### Strategy Analysis Commands
```python
# Analyze strategies
"Which strategies performed best this month?"
"Show earnings IV crush opportunities for tomorrow"
"Find BTC correlation breakdown trades"
"Identify gamma squeeze candidates with social sentiment"
```

## 🏗️ **Architecture**

```yaml
Data Flow:
  16 Data Feeds → QuestDB → TV Remote MCP ← Claude Code
                    ↓
                Alpaca Trading API
```

### **Components**
- **TVRemoteControl**: Core intelligence class managing all system interactions
- **Natural Language Parser**: Interprets Claude Code's commands
- **QuestDB Interface**: Accesses all market data through unified database
- **Alpaca Integration**: Executes trades and manages portfolio
- **Strategy Engine**: Implements all trading strategies as database queries

### **Key Tools**
- **`tv_remote(query)`**: Universal command interface for all system control
- **`options_intelligence()`**: Specialized options strategy analysis
- **`stock_intelligence()`**: Stock strategy identification and execution
- **`crypto_intelligence()`**: Cryptocurrency trading opportunities
- **`portfolio_risk_intelligence()`**: Risk analysis and scenario testing
- **`execute_trade_through_alpaca()`**: Direct trade execution interface

## 🔒 **Environment Variables**

```env
# QuestDB Connection
QUESTDB_HOST=localhost
QUESTDB_PG_PORT=8812
QUESTDB_USER=admin
QUESTDB_PASSWORD=quest
QUESTDB_DATABASE=qdb

# Alpaca Trading
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_PAPER_TRADING=true  # Set to false for live trading
```

## 🎯 **Natural Language Command Categories**

### **Information Queries**
- Market analysis and intelligence gathering
- Strategy performance review
- Risk assessment and scenario analysis
- Portfolio status and analytics

### **Action Commands**
- Trade execution (buy/sell stocks, options)
- Portfolio management (rebalancing, stops)
- Strategy implementation
- Risk management actions

### **Monitoring Commands**
- Real-time position tracking
- Performance monitoring
- Alert management
- System status checks

## 🔥 **Revolutionary Advantages**

### **Unified Control**
- **ONE interface** for everything (vs. multiple APIs)
- **Natural language** commands (vs. complex code)
- **Intelligent routing** (automatically determines what to do)

### **Agentic Intelligence**
- **Context awareness** (understands market conditions)
- **Adaptive strategies** (modifies based on regime)
- **Risk intelligence** (automatic portfolio protection)

### **Speed & Reliability**
- **Sub-second response** times through QuestDB
- **Real-time execution** through Alpaca integration
- **Comprehensive logging** of all decisions and trades

## 📈 **Trading Capabilities**

### **Asset Classes**
- **Stocks**: All US equities with real-time data
- **Options**: Single leg and complex strategies
- **ETFs**: Sector rotation and market timing
- **Crypto**: BTC, ETH and major cryptocurrencies

### **Order Types**
- Market orders (immediate execution)
- Limit orders (price-specific execution)
- Stop orders (risk management)
- Stop-limit orders (advanced risk control)
- Complex options strategies (spreads, condors, straddles)

### **Risk Management**
- Position sizing based on Kelly criterion
- Portfolio correlation monitoring
- Real-time VaR calculations
- Scenario stress testing

## 🎪 **Example Trading Session**

```python
# Market analysis
"What's the current market regime and which strategies work best?"

# Strategy identification
"Find earnings IV crush opportunities for this week"

# Risk assessment
"What's my portfolio exposure to tech sector volatility?"

# Trade execution
"Execute earnings IV crush on NVDA with 50 delta short straddle"

# Monitoring
"Show me real-time P&L on the NVDA position"

# Risk management
"Set stop loss on NVDA position at 25% max loss"
```

## 🏆 **Performance Benefits**

- **Faster decision making**: Natural language vs. complex programming
- **Reduced errors**: Intelligent command parsing and validation
- **Better risk management**: Real-time portfolio monitoring
- **Improved returns**: Data-driven strategy selection
- **24/7 operation**: Automated monitoring and execution

---

**The TV Remote MCP transforms Claude Code into the ultimate trading intelligence - one simple interface to control an institutional-quality trading system.** 📺🚀

Think of it as the evolution from complicated trading platforms to a simple, intelligent remote control that understands exactly what you want to do in the markets.