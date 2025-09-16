#!/usr/bin/env python3
"""
EzBot TV Remote MCP Server
Claude Code's UNIVERSAL REMOTE - ONE TOOL that controls everything:
- Market intelligence queries through QuestDB
- All trading strategies (stocks, options, ETFs, crypto)
- Risk analysis and portfolio management
- Trade execution through Alpaca
- Complete trading system control
"""

import asyncio
import json
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv
from fastmcp import FastMCP
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from project root
logger.info("Loading environment variables from /home/ezb0t/ezbot/.env")
load_dotenv("/home/ezb0t/ezbot/.env")
logger.info("Environment variables loaded")

# Initialize FastMCP server
mcp = FastMCP(
    name="tv-remote",
    instructions="""
    Claude Code's UNIVERSAL TV REMOTE - ONE TOOL that controls the entire trading system.

    This is your ONLY interface to:
    • Market intelligence (all 16 data feeds through QuestDB)
    • Trading strategies (stocks, options, ETFs, crypto)
    • Risk analysis and portfolio management
    • Trade execution (buy/sell through Alpaca)
    • System monitoring and control

    Use natural language to control everything - like a TV remote for trading.
    """
)

class TVRemoteControl:
    """
    Claude Code's Universal Trading System Remote Control
    ONE interface to control EVERYTHING - data, strategies, trades, risk
    """

    def __init__(self):
        logger.info("Initializing TV Remote Control - Universal Trading Interface")
        # QuestDB connection parameters
        self.host = os.getenv("QUESTDB_HOST", "localhost")
        self.port = int(os.getenv("QUESTDB_PG_PORT", "8812"))  # PostgreSQL wire protocol port
        self.user = os.getenv("QUESTDB_USER", "admin")
        self.password = os.getenv("QUESTDB_PASSWORD", "quest")
        self.database = os.getenv("QUESTDB_DATABASE", "qdb")

        # Alpaca connection for execution (proxied through this MCP)
        self.alpaca_api_key = os.getenv("ALPACA_API_KEY")
        self.alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.alpaca_paper = os.getenv("ALPACA_PAPER_TRADING", "true").lower() == "true"

        if self.alpaca_paper:
            self.alpaca_base_url = "https://paper-api.alpaca.markets"
        else:
            self.alpaca_base_url = "https://api.alpaca.markets"

        logger.info(f"Connected to QuestDB at {self.host}:{self.port}")
        logger.info(f"Alpaca trading mode: {'Paper' if self.alpaca_paper else 'Live'}")

    async def _get_connection(self):
        """Get QuestDB connection"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                cursor_factory=RealDictCursor
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to QuestDB: {e}")
            raise

    async def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SQL query on QuestDB"""
        try:
            conn = await self._get_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            cursor.close()
            conn.close()

            # Convert to list of dicts
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def parse_natural_language_intent(self, query: str) -> Dict[str, Any]:
        """Parse Claude Code's natural language query intent"""
        intent = {
            'type': 'general_query',
            'asset_class': None,
            'strategy': None,
            'timeframe': None,
            'filters': {}
        }

        query_lower = query.lower()

        # Determine asset class
        if any(word in query_lower for word in ['option', 'call', 'put', 'strike', 'expiry', 'iv', 'gamma', 'delta']):
            intent['asset_class'] = 'options'
        elif any(word in query_lower for word in ['etf', 'sector', 'spy', 'qqq', 'iwm', 'vix']):
            intent['asset_class'] = 'etf'
        elif any(word in query_lower for word in ['crypto', 'bitcoin', 'btc', 'ethereum', 'eth']):
            intent['asset_class'] = 'crypto'
        else:
            intent['asset_class'] = 'stock'

        # Determine query type
        if any(word in query_lower for word in ['find', 'show', 'identify', 'search']):
            intent['type'] = 'opportunity_discovery'
        elif any(word in query_lower for word in ['risk', 'portfolio', 'exposure', 'correlation']):
            intent['type'] = 'risk_analysis'
        elif any(word in query_lower for word in ['performance', 'strategy', 'backtest']):
            intent['type'] = 'strategy_performance'
        elif any(word in query_lower for word in ['execute', 'trade', 'buy', 'sell']):
            intent['type'] = 'execution'

        return intent

@mcp.tool()
async def news_sentiment_intelligence(query: str = None) -> dict:
    """
    Real-time news sentiment analysis with market impact prediction

    Examples:
    - "Show negative sentiment stocks with oversold RSI"
    - "Find positive earnings surprises with momentum"
    - "Identify news catalysts causing unusual options activity"
    """
    remote = TVRemoteControl()

    sentiment_query = """
    SELECT DISTINCT s.symbol, s.current_price, n.sentiment_score, n.headline,
           n.impact_score, s.volume_ratio, t.rsi_14, o.unusual_activity,
           n.publish_time, s.price_change_1min, s.price_change_5min
    FROM stock_data s
    JOIN news_sentiment n ON s.symbol = n.symbol
    LEFT JOIN technical_indicators t ON s.symbol = t.symbol
    LEFT JOIN options_flow o ON s.symbol = o.symbol
    WHERE
        n.publish_time > NOW() - INTERVAL '2 hours' AND
        ABS(n.sentiment_score) > 0.4 AND
        s.volume_ratio > 1.5
    ORDER BY n.impact_score DESC, n.publish_time DESC
    LIMIT 20
    """

    results = await remote.execute_query(sentiment_query)

    return {
        "query": query,
        "news_sentiment_opportunities": results,
        "market_regime": await _detect_market_sentiment_regime(remote),
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def pattern_momentum_intelligence(timeframe: str = "multi", pattern_type: str = "all") -> dict:
    """
    Multi-timeframe momentum and pattern recognition

    Args:
        timeframe: "5m", "15m", "1h", "4h", "1d", "multi"
        pattern_type: "breakout", "reversal", "continuation", "divergence", "all"
    """
    remote = TVRemoteControl()

    pattern_query = """
    SELECT symbol, current_price, pattern_type, pattern_strength,
           momentum_5m, momentum_15m, momentum_1h, momentum_4h,
           volume_surge, price_target, confidence_score, risk_reward_ratio
    FROM pattern_recognition p
    JOIN momentum_analysis m ON p.symbol = m.symbol
    WHERE
        pattern_strength > 0.7 AND
        confidence_score > 0.6 AND
        risk_reward_ratio > 2.0
    ORDER BY pattern_strength DESC, momentum_1h DESC
    LIMIT 15
    """

    results = await remote.execute_query(pattern_query)

    return {
        "timeframe": timeframe,
        "pattern_type": pattern_type,
        "patterns": results,
        "momentum_summary": await _analyze_market_momentum(remote),
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def intelligent_position_sizing(symbol: str, strategy: str, risk_tolerance: float = 0.02) -> dict:
    """
    Kelly Criterion-based intelligent position sizing

    Args:
        symbol: Stock/option symbol
        strategy: Strategy name for historical performance lookup
        risk_tolerance: Maximum portfolio risk per trade (default 2%)
    """
    remote = TVRemoteControl()

    # Get strategy historical performance
    performance_query = """
    SELECT strategy_name, win_rate, avg_win_pct, avg_loss_pct,
           sharpe_ratio, max_drawdown, trade_count
    FROM strategy_performance
    WHERE strategy_name = %s AND trade_count >= 30
    ORDER BY timestamp DESC
    LIMIT 1
    """

    # Get current portfolio metrics
    portfolio_query = """
    SELECT total_portfolio_value, current_cash, total_exposure,
           portfolio_beta, portfolio_var_95
    FROM portfolio_summary
    ORDER BY timestamp DESC
    LIMIT 1
    """

    performance = await remote.execute_query(performance_query, (strategy,))
    portfolio = await remote.execute_query(portfolio_query)

    if performance and portfolio:
        # Calculate Kelly Criterion position size
        kelly_size = await _calculate_kelly_position_size(
            performance[0], portfolio[0], risk_tolerance
        )

        return {
            "symbol": symbol,
            "strategy": strategy,
            "recommended_position_size": kelly_size,
            "risk_metrics": performance[0],
            "portfolio_impact": await _calculate_portfolio_impact(remote, symbol, kelly_size),
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {"error": "Insufficient data for position sizing calculation"}

@mcp.tool()
async def real_time_greeks_monitor(portfolio_only: bool = True) -> dict:
    """
    Real-time portfolio Greeks monitoring and alerts

    Args:
        portfolio_only: Monitor only current positions vs all market
    """
    remote = TVRemoteControl()

    if portfolio_only:
        greeks_query = """
        SELECT p.symbol, p.position_size, o.delta, o.gamma, o.theta, o.vega,
               o.implied_volatility, p.entry_price, p.current_pnl,
               o.days_to_expiry, o.moneyness
        FROM portfolio_positions p
        JOIN options_greeks o ON p.symbol = o.symbol
        WHERE p.position_size != 0 AND o.days_to_expiry <= 45
        ORDER BY ABS(o.gamma) DESC
        """
    else:
        greeks_query = """
        SELECT symbol, delta, gamma, theta, vega, implied_volatility,
               options_volume, unusual_activity, days_to_expiry, moneyness
        FROM options_greeks
        WHERE days_to_expiry <= 45 AND options_volume > avg_volume * 1.5
        ORDER BY ABS(gamma) DESC
        LIMIT 50
        """

    results = await remote.execute_query(greeks_query)

    # Calculate portfolio-level Greeks
    portfolio_greeks = await _calculate_portfolio_greeks(remote, results)

    return {
        "individual_positions": results,
        "portfolio_greeks": portfolio_greeks,
        "risk_alerts": await _generate_greeks_alerts(portfolio_greeks),
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def ml_prediction_engine(prediction_type: str = "next_move", symbol: str = "SPY", timeframe: str = "1h") -> dict:
    """
    Machine learning-powered market prediction engine

    Args:
        prediction_type: "next_move", "volatility", "breakout", "reversal"
        symbol: Symbol to predict
        timeframe: "5m", "15m", "1h", "4h", "1d"
    """
    remote = TVRemoteControl()

    prediction_query = """
    SELECT symbol, timeframe, prediction_type, predicted_direction,
           confidence_score, price_target, stop_loss, risk_reward_ratio,
           key_features, model_accuracy, prediction_horizon_minutes
    FROM ml_predictions
    WHERE
        symbol = %s AND
        timeframe = %s AND
        prediction_type = %s AND
        timestamp > NOW() - INTERVAL '30 minutes'
    ORDER BY confidence_score DESC
    LIMIT 5
    """

    results = await remote.execute_query(prediction_query, (symbol, timeframe, prediction_type))

    # Get model performance metrics
    model_performance = await _get_ml_model_performance(remote, prediction_type)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "prediction_type": prediction_type,
        "predictions": results,
        "model_performance": model_performance,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def cross_asset_correlation_matrix(base_assets: str = "SPY,QQQ,IWM,VIX,BTC-USD") -> dict:
    """
    Real-time cross-asset correlation analysis with regime detection

    Args:
        base_assets: Comma-separated list of assets to analyze
    """
    remote = TVRemoteControl()

    assets_list = base_assets.split(",")

    correlation_query = """
    SELECT asset1, asset2, correlation_1h, correlation_4h, correlation_1d,
           correlation_1w, correlation_stability, regime_dependent,
           correlation_breakdown_alert, divergence_signal
    FROM cross_asset_correlations
    WHERE
        asset1 IN %s AND asset2 IN %s AND
        timestamp > NOW() - INTERVAL '1 hour'
    ORDER BY ABS(correlation_1h) DESC
    """

    results = await remote.execute_query(correlation_query, (tuple(assets_list), tuple(assets_list)))

    # Detect correlation regime changes
    regime_changes = await _detect_correlation_regime_changes(remote, assets_list)

    # Generate trading opportunities from correlation breaks
    correlation_opportunities = await _find_correlation_arbitrage_opportunities(remote, results)

    return {
        "base_assets": assets_list,
        "correlation_matrix": results,
        "regime_changes": regime_changes,
        "arbitrage_opportunities": correlation_opportunities,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def adaptive_strategy_selector(market_conditions: dict = None, portfolio_state: dict = None) -> dict:
    """
    AI-powered strategy selection based on current market regime

    Automatically selects optimal strategies for current conditions
    """
    remote = TVRemoteControl()

    # Get current market regime
    if not market_conditions:
        market_conditions = await _get_comprehensive_market_regime(remote)

    # Get current portfolio state
    if not portfolio_state:
        portfolio_state = await _get_current_portfolio_state(remote)

    # Get strategy performance in similar regimes
    regime_strategy_query = """
    SELECT s.strategy_name, s.avg_return_pct, s.win_rate, s.sharpe_ratio,
           s.max_drawdown, r.regime_match_score, s.trades_in_regime
    FROM strategy_regime_performance s
    JOIN market_regime_similarity r ON s.regime_id = r.historical_regime_id
    WHERE
        r.current_regime_similarity > 0.7 AND
        s.trades_in_regime >= 10
    ORDER BY s.sharpe_ratio DESC, r.regime_match_score DESC
    LIMIT 10
    """

    strategy_recommendations = await remote.execute_query(regime_strategy_query)

    # Calculate optimal strategy allocation
    optimal_allocation = await _calculate_optimal_strategy_allocation(
        remote, strategy_recommendations, portfolio_state, market_conditions
    )

    return {
        "market_conditions": market_conditions,
        "portfolio_state": portfolio_state,
        "recommended_strategies": strategy_recommendations,
        "optimal_allocation": optimal_allocation,
        "execution_plan": await _generate_strategy_execution_plan(remote, optimal_allocation),
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def market_microstructure_intelligence(symbol: str, analysis_depth: str = "full") -> dict:
    """
    Deep market microstructure analysis for optimal execution

    Args:
        symbol: Symbol to analyze
        analysis_depth: "basic", "standard", "full", "institutional"
    """
    remote = TVRemoteControl()

    microstructure_query = """
    SELECT symbol, bid_ask_spread, order_book_depth, market_impact_cost,
           liquidity_score, volume_profile, price_improvement_opportunity,
           hidden_liquidity_estimate, algo_activity_score, retail_flow_ratio,
           institutional_flow_ratio, dark_pool_ratio
    FROM market_microstructure_analysis
    WHERE
        symbol = %s AND
        timestamp > NOW() - INTERVAL '15 minutes'
    ORDER BY timestamp DESC
    LIMIT 10
    """

    results = await remote.execute_query(microstructure_query, (symbol,))

    # Generate optimal execution recommendations
    execution_recommendations = await _generate_execution_recommendations(remote, symbol, results)

    # Detect institutional activity patterns
    institutional_patterns = await _detect_institutional_patterns(remote, symbol)

    return {
        "symbol": symbol,
        "analysis_depth": analysis_depth,
        "microstructure_data": results,
        "execution_recommendations": execution_recommendations,
        "institutional_patterns": institutional_patterns,
        "optimal_entry_zones": await _identify_optimal_entry_zones(remote, symbol),
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def autonomous_trading_command(
    command_type: str,
    natural_language_query: str,
    risk_tolerance: float = 0.02,
    execution_mode: str = "autonomous"
) -> dict:
    """
    Universal autonomous trading interface - Full Agentic AI System

    Command Types:
    - "market_analysis": Deep multi-agent market analysis
    - "strategy_discovery": Find optimal strategies for conditions
    - "autonomous_execution": Full autonomous trading
    - "risk_scenario": Portfolio stress testing
    - "regime_adaptation": Auto-adapt to regime changes
    - "learning_optimization": Optimize from historical performance

    Examples:
    - "Find tech momentum with unusual options flow and earnings catalysts"
    - "Execute optimal strategy for current regime with 2% max risk"
    - "Adapt portfolio for detected market regime change"
    """
    try:
        remote = TVRemoteControl()
        agent_coordinator = AutonomousAgentCoordinator(remote)

        # Route to appropriate multi-agent system
        result = await agent_coordinator.process_command(
            command_type=command_type,
            query=natural_language_query,
            risk_tolerance=risk_tolerance,
            execution_mode=execution_mode
        )

        return result

    except Exception as e:
        return {"error": str(e), "command_type": command_type, "query": natural_language_query}

@mcp.tool()
async def multi_agent_analysis(analysis_type: str = "comprehensive", symbols: str = "SPY,QQQ,IWM") -> dict:
    """
    Multi-agent market analysis system

    Analysis Types:
    - "comprehensive": All agents analyze market
    - "fundamental": Company/economic analysis
    - "technical": Pattern and momentum analysis
    - "sentiment": News and social sentiment
    - "options_flow": Unusual activity and institutional flow
    """
    remote = TVRemoteControl()
    agent_coordinator = AutonomousAgentCoordinator(remote)

    agents_results = await agent_coordinator.run_multi_agent_analysis(
        analysis_type=analysis_type,
        symbols=symbols.split(",")
    )

    return {
        "analysis_type": analysis_type,
        "symbols": symbols,
        "agent_results": agents_results,
        "synthesis": await agent_coordinator.synthesize_agent_insights(agents_results),
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def tv_remote(query: str) -> dict:
    """
    Claude Code's UNIVERSAL TV REMOTE - ONE TOOL that controls everything

    Args:
        query: Natural language command to control the entire trading system

    MARKET INTELLIGENCE Examples:
        - "Find unusual options activity in tech stocks with earnings this week"
        - "Show me RSI mean reversion opportunities in current market conditions"
        - "What's my portfolio risk if SPY drops 10% and VIX spikes to 40?"
        - "Identify crypto patterns that predict Monday equity gaps"

    TRADE EXECUTION Examples:
        - "Buy 100 shares of AAPL at market price"
        - "Sell 10 SPY 520 calls expiring today"
        - "Close all positions in TSLA"
        - "Execute iron condor on QQQ with 30 delta strikes"

    PORTFOLIO MANAGEMENT Examples:
        - "Show my current positions and P&L"
        - "Rebalance portfolio to 60/40 stocks/options"
        - "Set stop losses on all positions at 2% below current price"

    Returns:
        Complete system response based on command
    """
    try:
        remote = TVRemoteControl()
        intent = await remote.parse_natural_language_intent(query)

        # Route to appropriate system control based on intent
        if intent['type'] == 'opportunity_discovery':
            return await _find_trading_opportunities(remote, intent, query)
        elif intent['type'] == 'risk_analysis':
            return await _analyze_portfolio_risk(remote, intent, query)
        elif intent['type'] == 'strategy_performance':
            return await _analyze_strategy_performance(remote, intent, query)
        elif intent['type'] == 'execution':
            return await _execute_trading_decision(remote, intent, query)
        else:
            return await _general_market_analysis(remote, intent, query)

    except Exception as e:
        logger.error(f"TV Remote command failed: {e}")
        return {"error": str(e), "query": query}

@mcp.tool()
async def options_intelligence(strategy_type: str, market_conditions: str = None) -> dict:
    """
    Claude Code options strategy intelligence through QuestDB

    Args:
        strategy_type: Options strategy to analyze
            - "0dte_iron_condor": Same-day iron condors on SPY/QQQ/IWM
            - "earnings_iv_crush": IV crush plays around earnings
            - "gamma_squeeze": Gamma squeeze opportunities
            - "flow_following": Follow unusual options activity
            - "volatility_mean_reversion": Sell high IV, buy low IV

    Returns:
        Options opportunities with detailed analysis
    """

    remote = TVRemoteControl()

    strategy_queries = {
        "0dte_iron_condor": """
        SELECT DISTINCT symbol, current_price, implied_volatility, gamma_exposure,
               options_volume, put_call_ratio, vix_level, expiry_date
        FROM options_data o
        JOIN market_data m ON o.symbol = m.symbol
        JOIN volatility_data v ON o.symbol = v.symbol
        WHERE
            expiry_date = CURRENT_DATE AND
            symbol IN ('SPY', 'QQQ', 'IWM') AND
            implied_volatility < 20 AND
            gamma_exposure > 0.1 AND
            vix_level < 25
        ORDER BY gamma_exposure DESC
        LIMIT 5
        """,

        "earnings_iv_crush": """
        SELECT DISTINCT o.symbol, o.current_price, o.implied_volatility,
               e.earnings_date, e.earnings_time, e.expected_move,
               h.avg_iv_crush_pct, o.options_volume
        FROM options_data o
        JOIN earnings_calendar e ON o.symbol = e.symbol
        JOIN historical_earnings h ON o.symbol = h.symbol
        WHERE
            e.earnings_date = CURRENT_DATE AND
            o.implied_volatility > 80 AND
            h.avg_iv_crush_pct > 30 AND
            o.options_volume > o.avg_volume * 2
        ORDER BY h.avg_iv_crush_pct DESC
        LIMIT 10
        """,

        "gamma_squeeze": """
        SELECT symbol, current_price, total_gamma, call_volume, put_volume,
               unusual_call_activity, price_momentum, social_sentiment
        FROM options_flow_summary
        WHERE
            total_gamma > 0.5 AND
            call_volume > put_volume * 3 AND
            unusual_call_activity = true AND
            price_momentum > 0.02 AND
            social_sentiment > 0.3
        ORDER BY total_gamma DESC
        LIMIT 8
        """
    }

    query = strategy_queries.get(strategy_type, "SELECT 'Strategy not found' as error")
    results = await remote.execute_query(query)

    return {
        "strategy": strategy_type,
        "market_conditions": market_conditions,
        "opportunities": results,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def stock_intelligence(strategy_type: str, market_regime: str = None) -> dict:
    """
    Claude Code stock strategy intelligence through QuestDB

    Args:
        strategy_type: Stock strategy to analyze
            - "rsi_mean_reversion": RSI < 25 or > 75 opportunities
            - "gap_fill": 2-4% gap fill opportunities
            - "news_momentum": News catalyst momentum plays
            - "vwap_reversion": VWAP deviation trades
            - "breakout_continuation": Momentum continuation setups

    Returns:
        Stock opportunities with entry/exit analysis
    """

    remote = TVRemoteControl()

    strategy_queries = {
        "rsi_mean_reversion": """
        SELECT s.symbol, s.current_price, t.rsi_14, s.volume_ratio,
               t.support_level, t.resistance_level, n.sentiment_score,
               s.sector, s.market_cap
        FROM stock_data s
        JOIN technical_indicators t ON s.symbol = t.symbol
        LEFT JOIN news_sentiment n ON s.symbol = n.symbol
        WHERE
            (t.rsi_14 < 25 OR t.rsi_14 > 75) AND
            s.volume_ratio > 1.5 AND
            (n.sentiment_score > -0.3 OR n.sentiment_score IS NULL) AND
            s.market_cap > 1000000000
        ORDER BY ABS(t.rsi_14 - 50) DESC
        LIMIT 15
        """,

        "gap_fill": """
        SELECT symbol, current_price, gap_percentage, gap_direction,
               previous_close, news_catalyst_present, sector_performance,
               premarket_volume_ratio, gap_quality_score
        FROM gap_analysis
        WHERE
            ABS(gap_percentage) BETWEEN 2.0 AND 4.0 AND
            news_catalyst_present = false AND
            gap_quality_score > 0.7 AND
            premarket_volume_ratio < 1.2
        ORDER BY gap_quality_score DESC
        LIMIT 12
        """,

        "news_momentum": """
        SELECT DISTINCT s.symbol, s.current_price, n.headline, n.sentiment_score,
               s.volume_surge, s.price_change_5min, f.unusual_activity_score
        FROM stock_data s
        JOIN news_feed n ON s.symbol = n.symbol
        LEFT JOIN flow_data f ON s.symbol = f.symbol
        WHERE
            n.publish_time > NOW() - INTERVAL '30 minutes' AND
            n.sentiment_score > 0.6 AND
            s.volume_surge > 2.5 AND
            s.price_change_5min > 1.5
        ORDER BY n.publish_time DESC
        LIMIT 8
        """
    }

    query = strategy_queries.get(strategy_type, "SELECT 'Strategy not found' as error")
    results = await remote.execute_query(query)

    return {
        "strategy": strategy_type,
        "market_regime": market_regime,
        "opportunities": results,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def crypto_intelligence(strategy_type: str, correlation_analysis: bool = True) -> dict:
    """
    Claude Code crypto strategy intelligence through QuestDB

    Args:
        strategy_type: Crypto strategy to analyze
            - "btc_spy_correlation": BTC-SPY correlation trades
            - "weekend_gap_prediction": Weekend crypto → Monday equity gaps
            - "crypto_mean_reversion": Crypto RSI extremes
            - "defi_momentum": DeFi token momentum

    Returns:
        Crypto opportunities and correlation analysis
    """

    remote = TVRemoteControl()

    strategy_queries = {
        "btc_spy_correlation": """
        SELECT btc_price, spy_price, correlation_4h, correlation_24h,
               btc_momentum_4h, spy_momentum_4h, divergence_signal,
               prediction_accuracy, confidence_score
        FROM crypto_equity_correlation
        WHERE
            ABS(divergence_signal) > 0.02 AND
            correlation_24h > 0.6 AND
            confidence_score > 0.7
        ORDER BY timestamp DESC
        LIMIT 5
        """,

        "weekend_gap_prediction": """
        SELECT weekend_start_price, weekend_end_price, weekend_change_pct,
               predicted_spy_gap, historical_accuracy, volume_weekend,
               sentiment_shift, confidence_level
        FROM weekend_gap_analysis
        WHERE
            ABS(weekend_change_pct) > 3.0 AND
            historical_accuracy > 0.65
        ORDER BY confidence_level DESC
        LIMIT 8
        """,

        "crypto_mean_reversion": """
        SELECT symbol, current_price, rsi_4h, rsi_1d, rsi_1w,
               fear_greed_index, social_sentiment_24h, volume_24h_ratio,
               support_level, resistance_level
        FROM crypto_technical_data
        WHERE
            (rsi_4h < 30 OR rsi_4h > 70) AND
            symbol IN ('BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD') AND
            volume_24h_ratio > 1.2
        ORDER BY ABS(rsi_4h - 50) DESC
        LIMIT 10
        """
    }

    query = strategy_queries.get(strategy_type, "SELECT 'Strategy not found' as error")
    results = await remote.execute_query(query)

    return {
        "strategy": strategy_type,
        "correlation_analysis": correlation_analysis,
        "opportunities": results,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def portfolio_risk_intelligence(scenario: str, current_positions: str = None) -> dict:
    """
    Claude Code portfolio risk analysis through QuestDB

    Args:
        scenario: Risk scenario to analyze
            - "market_crash_10pct": SPY drops 10%
            - "volatility_spike_vix40": VIX spikes to 40
            - "sector_rotation": Major sector rotation event
            - "correlation_breakdown": Asset correlation breakdown

    Returns:
        Comprehensive risk analysis and recommendations
    """

    remote = TVRemoteControl()

    risk_queries = {
        "market_crash_10pct": """
        SELECT symbol, current_position_size, beta_spy, correlation_spy,
               estimated_pnl_10pct_drop, portfolio_weight, hedge_ratio,
               sector_exposure, max_loss_estimate
        FROM portfolio_risk_analysis
        WHERE scenario_type = 'market_crash_10pct'
        ORDER BY estimated_pnl_10pct_drop ASC
        """,

        "volatility_spike_vix40": """
        SELECT symbol, position_type, vega_exposure, gamma_exposure,
               theta_decay, portfolio_var_95, stress_test_pnl,
               hedge_suggestions, iv_impact
        FROM volatility_risk_scenarios
        WHERE vix_target = 40
        ORDER BY stress_test_pnl ASC
        """,

        "correlation_breakdown": """
        SELECT asset_pair, current_correlation, historical_correlation,
               correlation_stability, portfolio_impact, diversification_benefit,
               rebalance_recommendation
        FROM correlation_analysis
        WHERE correlation_stability < 0.5
        ORDER BY portfolio_impact DESC
        """
    }

    query = risk_queries.get(scenario, "SELECT 'Scenario not found' as error")
    results = await remote.execute_query(query)

    return {
        "risk_scenario": scenario,
        "current_positions": current_positions,
        "risk_analysis": results,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def execute_trade_through_alpaca(
    strategy: str,
    symbol: str,
    action: str,
    quantity: str,
    order_type: str = "market",
    reasoning: str = None
) -> dict:
    """
    Claude Code trade execution through Alpaca (proxied through market_data_mcp)

    Args:
        strategy: Strategy name that generated this trade
        symbol: Symbol to trade (e.g., 'AAPL', 'SPY', 'AAPL240315C00180000')
        action: "buy", "sell", "buy_to_open", "sell_to_close", etc.
        quantity: Position size or number of contracts/shares
        order_type: "market", "limit", "stop", "stop_limit"
        reasoning: Claude Code's reasoning for this trade

    Returns:
        Trade execution result and confirmation
    """

    remote = TVRemoteControl()

    # Log Claude Code's trading decision to QuestDB first
    trade_decision = {
        'timestamp': datetime.now(),
        'strategy': strategy,
        'symbol': symbol,
        'action': action,
        'quantity': quantity,
        'order_type': order_type,
        'reasoning': reasoning,
        'claude_decision': True,
        'execution_status': 'pending'
    }

    # Insert trade decision into QuestDB
    log_query = """
    INSERT INTO claude_trade_decisions
    (timestamp, strategy, symbol, action, quantity, order_type, reasoning, claude_decision, execution_status)
    VALUES (%(timestamp)s, %(strategy)s, %(symbol)s, %(action)s, %(quantity)s, %(order_type)s, %(reasoning)s, %(claude_decision)s, %(execution_status)s)
    """

    try:
        await remote.execute_query(log_query, tuple(trade_decision.values()))

        # Execute trade through Alpaca
        execution_result = await _execute_alpaca_trade(remote, trade_decision)

        # Update execution status in QuestDB
        update_query = """
        UPDATE claude_trade_decisions
        SET execution_status = %(status)s, execution_result = %(result)s
        WHERE timestamp = %(timestamp)s AND symbol = %(symbol)s
        """

        await remote.execute_query(update_query, (
            execution_result.get('status', 'failed'),
            json.dumps(execution_result),
            trade_decision['timestamp'],
            symbol
        ))

        return {
            "trade_decision": trade_decision,
            "execution_result": execution_result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Trade execution failed: {e}")
        return {
            "error": str(e),
            "trade_decision": trade_decision,
            "timestamp": datetime.now().isoformat()
        }

# Helper functions for TV Remote control
async def _find_trading_opportunities(remote, intent, query):
    """Find trading opportunities based on natural language query"""
    asset_class = intent.get('asset_class', 'stock')

    if asset_class == 'options':
        return await options_intelligence("flow_following")
    elif asset_class == 'crypto':
        return await crypto_intelligence("btc_spy_correlation")
    else:
        return await stock_intelligence("rsi_mean_reversion")

async def _analyze_portfolio_risk(remote, intent, query):
    """Analyze portfolio risk based on natural language query"""
    if "crash" in query.lower():
        return await portfolio_risk_intelligence("market_crash_10pct")
    elif "volatility" in query.lower() or "vix" in query.lower():
        return await portfolio_risk_intelligence("volatility_spike_vix40")
    else:
        return await portfolio_risk_intelligence("correlation_breakdown")

async def _analyze_strategy_performance(remote, intent, query):
    """Analyze strategy performance based on natural language query"""
    performance_query = """
    SELECT strategy_name, total_trades, win_rate, avg_return_pct,
           sharpe_ratio, max_drawdown, profit_factor, calmar_ratio,
           last_30_days_pnl, ytd_pnl
    FROM strategy_performance_summary
    WHERE total_trades >= 10
    ORDER BY sharpe_ratio DESC
    LIMIT 15
    """

    results = await remote.execute_query(performance_query)
    return {
        "strategy_performance": results,
        "top_performer": results[0] if results else None,
        "timestamp": datetime.now().isoformat()
    }

async def _execute_trading_decision(remote, intent, query):
    """Execute trading decision based on natural language query"""
    # Parse execution parameters from natural language
    symbols = _extract_symbols_from_query(query)
    action = _extract_action_from_query(query)
    quantity = _extract_quantity_from_query(query)

    if symbols and action and quantity:
        return await execute_trade_through_alpaca(
            strategy="claude_nlp_decision",
            symbol=symbols[0],
            action=action,
            quantity=str(quantity),
            reasoning=f"Claude Code decision from: {query}"
        )
    else:
        return {"error": "Could not parse trade parameters from query", "query": query}

async def _general_market_analysis(remote, intent, query):
    """General market analysis based on natural language query"""
    analysis_query = """
    SELECT
        (SELECT value FROM market_indicators WHERE indicator = 'SPY_price') as spy_price,
        (SELECT value FROM market_indicators WHERE indicator = 'VIX_level') as vix_level,
        (SELECT value FROM market_indicators WHERE indicator = 'market_sentiment') as sentiment,
        (SELECT value FROM market_indicators WHERE indicator = 'fear_greed_index') as fear_greed,
        (SELECT COUNT(*) FROM unusual_options_activity WHERE timestamp > NOW() - INTERVAL '1 hour') as unusual_activity_count
    """

    results = await remote.execute_query(analysis_query)
    return {
        "market_overview": results[0] if results else {},
        "query": query,
        "timestamp": datetime.now().isoformat()
    }

async def _execute_alpaca_trade(remote, trade_decision):
    """Execute trade through Alpaca API"""
    headers = {
        "APCA-API-KEY-ID": remote.alpaca_api_key,
        "APCA-API-SECRET-KEY": remote.alpaca_secret_key,
        "Content-Type": "application/json"
    }

    # Build Alpaca order payload
    order_payload = {
        "symbol": trade_decision['symbol'],
        "side": trade_decision['action'],
        "type": trade_decision['order_type'],
        "time_in_force": "day"
    }

    # Add quantity (shares vs notional)
    if trade_decision['quantity'].isdigit():
        order_payload["qty"] = trade_decision['quantity']
    else:
        order_payload["notional"] = trade_decision['quantity']

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{remote.alpaca_base_url}/v2/orders",
                headers=headers,
                json=order_payload
            )

            if response.status_code == 201:
                return {
                    "status": "success",
                    "order_id": response.json().get("id"),
                    "order_details": response.json()
                }
            else:
                return {
                    "status": "failed",
                    "error": response.text,
                    "status_code": response.status_code
                }

    except Exception as e:
        return {"status": "failed", "error": str(e)}

# Advanced helper functions for enhanced capabilities
async def _detect_market_sentiment_regime(remote):
    """Detect current market sentiment regime"""
    regime_query = """
    SELECT market_regime, confidence_score, regime_duration_hours,
           key_indicators, transition_probability
    FROM market_regime_detection
    ORDER BY timestamp DESC
    LIMIT 1
    """

    results = await remote.execute_query(regime_query)
    return results[0] if results else {"regime": "unknown", "confidence": 0.0}

async def _analyze_market_momentum(remote):
    """Analyze multi-timeframe market momentum"""
    momentum_query = """
    SELECT timeframe, momentum_score, strength, direction,
           volume_confirmation, breadth_indicator
    FROM market_momentum_analysis
    WHERE timeframe IN ('5m', '15m', '1h', '4h', '1d')
    ORDER BY timeframe
    """

    results = await remote.execute_query(momentum_query)
    return results

async def _calculate_kelly_position_size(performance, portfolio, risk_tolerance):
    """Calculate Kelly Criterion position size"""
    win_rate = performance['win_rate']
    avg_win = performance['avg_win_pct'] / 100
    avg_loss = abs(performance['avg_loss_pct']) / 100

    # Kelly formula: f = (bp - q) / b
    # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
    if avg_loss > 0:
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        kelly_fraction = (b * p - q) / b

        # Apply risk tolerance cap
        kelly_fraction = min(kelly_fraction, risk_tolerance)
        kelly_fraction = max(kelly_fraction, 0)  # No negative positions

        portfolio_value = portfolio['total_portfolio_value']
        position_size = portfolio_value * kelly_fraction

        return {
            "kelly_fraction": kelly_fraction,
            "position_size_usd": position_size,
            "risk_adjusted": True,
            "max_risk_pct": risk_tolerance * 100
        }

    return {"error": "Invalid performance data for Kelly calculation"}

async def _calculate_portfolio_impact(remote, symbol, position_size):
    """Calculate impact of new position on portfolio"""
    impact_query = """
    SELECT
        (SELECT beta_spy FROM stock_data WHERE symbol = %s) as position_beta,
        (SELECT correlation_spy FROM correlation_data WHERE symbol = %s) as position_correlation,
        (SELECT total_portfolio_value FROM portfolio_summary ORDER BY timestamp DESC LIMIT 1) as portfolio_value
    """

    results = await remote.execute_query(impact_query, (symbol, symbol))
    if results:
        data = results[0]
        position_weight = position_size['position_size_usd'] / data['portfolio_value']

        return {
            "position_weight_pct": position_weight * 100,
            "beta_contribution": data['position_beta'] * position_weight,
            "correlation_impact": data['position_correlation'],
            "risk_contribution": position_weight * data['position_beta']
        }

    return {"error": "Could not calculate portfolio impact"}

async def _calculate_portfolio_greeks(remote, positions):
    """Calculate portfolio-level Greeks"""
    total_delta = sum(pos.get('delta', 0) * pos.get('position_size', 0) for pos in positions)
    total_gamma = sum(pos.get('gamma', 0) * pos.get('position_size', 0) for pos in positions)
    total_theta = sum(pos.get('theta', 0) * pos.get('position_size', 0) for pos in positions)
    total_vega = sum(pos.get('vega', 0) * pos.get('position_size', 0) for pos in positions)

    return {
        "portfolio_delta": total_delta,
        "portfolio_gamma": total_gamma,
        "portfolio_theta": total_theta,
        "portfolio_vega": total_vega,
        "delta_neutral": abs(total_delta) < 50,
        "gamma_risk": abs(total_gamma) > 100,
        "theta_decay_daily": total_theta
    }

async def _generate_greeks_alerts(portfolio_greeks):
    """Generate risk alerts based on portfolio Greeks"""
    alerts = []

    if abs(portfolio_greeks['portfolio_delta']) > 100:
        alerts.append({
            "type": "DELTA_EXPOSURE",
            "severity": "HIGH",
            "message": f"High delta exposure: {portfolio_greeks['portfolio_delta']:.0f}"
        })

    if abs(portfolio_greeks['portfolio_gamma']) > 200:
        alerts.append({
            "type": "GAMMA_RISK",
            "severity": "HIGH",
            "message": f"High gamma risk: {portfolio_greeks['portfolio_gamma']:.0f}"
        })

    if portfolio_greeks['portfolio_theta'] < -500:
        alerts.append({
            "type": "THETA_DECAY",
            "severity": "MEDIUM",
            "message": f"High theta decay: ${portfolio_greeks['portfolio_theta']:.0f}/day"
        })

    return alerts

def _extract_symbols_from_query(query):
    """Extract stock symbols from natural language query"""
    import re
    # Simple regex to find potential stock symbols (2-5 uppercase letters)
    symbols = re.findall(r'\b[A-Z]{2,5}\b', query)
    return symbols

def _extract_action_from_query(query):
    """Extract trade action from natural language query"""
    query_lower = query.lower()
    if any(word in query_lower for word in ['buy', 'long', 'purchase']):
        return "buy"
    elif any(word in query_lower for word in ['sell', 'short', 'close']):
        return "sell"
    return None

def _extract_quantity_from_query(query):
    """Extract quantity from natural language query"""
    import re
    # Look for numbers in the query
    numbers = re.findall(r'\d+', query)
    return int(numbers[0]) if numbers else None

# Advanced ML and Intelligence Helper Functions
async def _get_ml_model_performance(remote, prediction_type):
    """Get ML model performance metrics"""
    performance_query = """
    SELECT prediction_type, accuracy_1h, accuracy_4h, accuracy_1d,
           precision_score, recall_score, f1_score, last_retrain_date,
           feature_importance_top5, model_version
    FROM ml_model_performance
    WHERE prediction_type = %s
    ORDER BY last_retrain_date DESC
    LIMIT 1
    """

    results = await remote.execute_query(performance_query, (prediction_type,))
    return results[0] if results else {"accuracy": "unknown", "status": "model_not_found"}

async def _detect_correlation_regime_changes(remote, assets_list):
    """Detect correlation regime changes"""
    regime_query = """
    SELECT asset_pair, correlation_regime, regime_change_detected,
           regime_change_confidence, previous_regime, change_timestamp,
           regime_stability_score, expected_duration_hours
    FROM correlation_regime_changes
    WHERE
        timestamp > NOW() - INTERVAL '4 hours' AND
        regime_change_detected = true
    ORDER BY regime_change_confidence DESC
    LIMIT 10
    """

    results = await remote.execute_query(regime_query)
    return results

async def _find_correlation_arbitrage_opportunities(remote, correlation_data):
    """Find arbitrage opportunities from correlation breakdowns"""
    opportunities = []

    for correlation in correlation_data:
        if correlation.get('correlation_breakdown_alert'):
            opportunities.append({
                "type": "correlation_arbitrage",
                "asset_pair": f"{correlation['asset1']}/{correlation['asset2']}",
                "expected_correlation": correlation['correlation_1w'],
                "current_correlation": correlation['correlation_1h'],
                "divergence_magnitude": abs(correlation['correlation_1w'] - correlation['correlation_1h']),
                "confidence": 0.8,
                "strategy": "pair_trade"
            })

    return opportunities

async def _get_comprehensive_market_regime(remote):
    """Get comprehensive market regime analysis"""
    regime_query = """
    SELECT market_regime, volatility_regime, trend_regime, momentum_regime,
           correlation_regime, liquidity_regime, sentiment_regime,
           regime_confidence, regime_duration_hours, transition_signals
    FROM comprehensive_market_regime
    ORDER BY timestamp DESC
    LIMIT 1
    """

    results = await remote.execute_query(regime_query)
    return results[0] if results else {"regime": "undefined", "confidence": 0.0}

async def _get_current_portfolio_state(remote):
    """Get current portfolio state"""
    portfolio_query = """
    SELECT total_value, cash_percentage, stock_percentage, options_percentage,
           crypto_percentage, portfolio_beta, portfolio_sharpe, max_drawdown_ytd,
           concentration_risk, correlation_risk, liquidity_risk
    FROM current_portfolio_state
    ORDER BY timestamp DESC
    LIMIT 1
    """

    results = await remote.execute_query(portfolio_query)
    return results[0] if results else {"total_value": 0, "status": "unknown"}

async def _calculate_optimal_strategy_allocation(remote, strategies, portfolio_state, market_conditions):
    """Calculate optimal strategy allocation using modern portfolio theory"""
    # Simplified MPT allocation based on Sharpe ratios and correlations
    total_sharpe = sum(s.get('sharpe_ratio', 0) for s in strategies)

    if total_sharpe > 0:
        allocations = []
        for strategy in strategies:
            weight = strategy.get('sharpe_ratio', 0) / total_sharpe
            # Cap individual strategy allocation at 25%
            weight = min(weight, 0.25)

            allocations.append({
                "strategy_name": strategy['strategy_name'],
                "allocation_percentage": weight * 100,
                "expected_return": strategy.get('avg_return_pct', 0),
                "risk_score": strategy.get('max_drawdown', 0),
                "confidence": strategy.get('regime_match_score', 0.5)
            })

        return allocations
    else:
        return [{"error": "No viable strategies for current conditions"}]

async def _generate_strategy_execution_plan(remote, allocation):
    """Generate step-by-step execution plan"""
    execution_steps = []

    for strategy in allocation:
        if not strategy.get('error'):
            execution_steps.append({
                "step": len(execution_steps) + 1,
                "action": f"Allocate {strategy['allocation_percentage']:.1f}% to {strategy['strategy_name']}",
                "expected_return": strategy['expected_return'],
                "risk_level": "LOW" if strategy['risk_score'] < 5 else "MEDIUM" if strategy['risk_score'] < 15 else "HIGH",
                "execution_priority": "HIGH" if strategy['confidence'] > 0.8 else "MEDIUM"
            })

    return execution_steps

async def _generate_execution_recommendations(remote, symbol, microstructure_data):
    """Generate optimal execution recommendations"""
    if not microstructure_data:
        return {"error": "No microstructure data available"}

    latest_data = microstructure_data[0]

    recommendations = {
        "optimal_order_size": await _calculate_optimal_order_size(remote, symbol, latest_data),
        "execution_strategy": await _select_execution_strategy(latest_data),
        "timing_recommendation": await _get_timing_recommendation(remote, symbol),
        "expected_slippage": latest_data.get('market_impact_cost', 0),
        "liquidity_assessment": latest_data.get('liquidity_score', 0)
    }

    return recommendations

async def _detect_institutional_patterns(remote, symbol):
    """Detect institutional trading patterns"""
    patterns_query = """
    SELECT pattern_type, confidence_score, volume_signature, time_pattern,
           size_distribution, execution_style, estimated_completion_time
    FROM institutional_pattern_detection
    WHERE symbol = %s AND timestamp > NOW() - INTERVAL '2 hours'
    ORDER BY confidence_score DESC
    LIMIT 5
    """

    results = await remote.execute_query(patterns_query, (symbol,))
    return results

async def _identify_optimal_entry_zones(remote, symbol):
    """Identify optimal entry zones based on support/resistance and liquidity"""
    zones_query = """
    SELECT price_level, zone_type, strength_score, volume_at_level,
           historical_bounce_rate, liquidity_at_level, risk_reward_ratio
    FROM optimal_entry_zones
    WHERE symbol = %s AND timestamp > NOW() - INTERVAL '1 hour'
    ORDER BY strength_score DESC
    LIMIT 8
    """

    results = await remote.execute_query(zones_query, (symbol,))
    return results

async def _calculate_optimal_order_size(remote, symbol, microstructure_data):
    """Calculate optimal order size to minimize market impact"""
    liquidity_score = microstructure_data.get('liquidity_score', 0.5)
    order_book_depth = microstructure_data.get('order_book_depth', 1000)

    # Conservative approach: 10% of average book depth
    optimal_size = int(order_book_depth * 0.1 * liquidity_score)
    return max(optimal_size, 100)  # Minimum 100 shares

async def _select_execution_strategy(microstructure_data):
    """Select optimal execution strategy based on market conditions"""
    liquidity = microstructure_data.get('liquidity_score', 0.5)
    algo_activity = microstructure_data.get('algo_activity_score', 0.5)

    if liquidity > 0.8 and algo_activity < 0.3:
        return "aggressive_market_order"
    elif liquidity > 0.6:
        return "limit_order_midpoint"
    elif algo_activity > 0.7:
        return "iceberg_order"
    else:
        return "twap_execution"

async def _get_timing_recommendation(remote, symbol):
    """Get optimal timing recommendation"""
    timing_query = """
    SELECT optimal_time_window, expected_volatility, volume_pattern,
           institutional_activity_level, recommendation_confidence
    FROM execution_timing_analysis
    WHERE symbol = %s AND timestamp > NOW() - INTERVAL '30 minutes'
    ORDER BY recommendation_confidence DESC
    LIMIT 1
    """

    results = await remote.execute_query(timing_query, (symbol,))
    if results:
        return results[0]['optimal_time_window']
    else:
        return "immediate"

# ==================== AUTONOMOUS MULTI-AGENT SYSTEM ====================

class AutonomousAgentCoordinator:
    """Central coordinator for multi-agent autonomous trading system"""

    def __init__(self, remote_control):
        self.remote = remote_control
        self.agents = {
            "fundamental": FundamentalAnalysisAgent(remote_control),
            "technical": TechnicalAnalysisAgent(remote_control),
            "sentiment": SentimentAnalysisAgent(remote_control),
            "options_flow": OptionsFlowAgent(remote_control),
            "research": ResearchCoordinatorAgent(remote_control),
            "execution": StrategyExecutionAgent(remote_control),
            "risk": RiskManagementAgent(remote_control)
        }

    async def process_command(self, command_type, query, risk_tolerance, execution_mode):
        """Process autonomous trading command through multi-agent system"""

        if command_type == "market_analysis":
            return await self._deep_market_analysis(query)
        elif command_type == "strategy_discovery":
            return await self._discover_optimal_strategies(query, risk_tolerance)
        elif command_type == "autonomous_execution":
            return await self._autonomous_execution(query, risk_tolerance, execution_mode)
        elif command_type == "risk_scenario":
            return await self._risk_scenario_analysis(query)
        elif command_type == "regime_adaptation":
            return await self._regime_adaptation(query, risk_tolerance)
        elif command_type == "learning_optimization":
            return await self._learning_optimization(query)
        else:
            return {"error": f"Unknown command type: {command_type}"}

    async def run_multi_agent_analysis(self, analysis_type, symbols):
        """Run comprehensive multi-agent analysis"""

        if analysis_type == "comprehensive":
            # Run all agents in parallel
            results = await asyncio.gather(
                self.agents["fundamental"].analyze(symbols),
                self.agents["technical"].analyze(symbols),
                self.agents["sentiment"].analyze(symbols),
                self.agents["options_flow"].analyze(symbols)
            )
            return {
                "fundamental": results[0],
                "technical": results[1],
                "sentiment": results[2],
                "options_flow": results[3]
            }
        else:
            # Run specific agent
            return await self.agents[analysis_type].analyze(symbols)

    async def synthesize_agent_insights(self, agent_results):
        """Multi-agent debate and consensus building"""
        return await self.agents["research"].synthesize_insights(agent_results)

    async def _deep_market_analysis(self, query):
        """Deep multi-agent market analysis"""
        # Parse symbols from query
        symbols = self._extract_symbols_from_query(query)
        if not symbols:
            symbols = ["SPY", "QQQ", "IWM"]  # Default market symbols

        # Run comprehensive analysis
        agent_results = await self.run_multi_agent_analysis("comprehensive", symbols)

        # Synthesize insights
        synthesis = await self.synthesize_agent_insights(agent_results)

        # Detect current market regime
        regime = await self._detect_current_regime()

        return {
            "query": query,
            "symbols_analyzed": symbols,
            "agent_analysis": agent_results,
            "synthesis": synthesis,
            "market_regime": regime,
            "recommendations": await self._generate_recommendations(synthesis, regime),
            "timestamp": datetime.now().isoformat()
        }

    async def _discover_optimal_strategies(self, query, risk_tolerance):
        """Discover optimal strategies for current conditions"""
        # Get current market regime
        regime = await self._detect_current_regime()

        # Get agent analysis
        symbols = self._extract_symbols_from_query(query)
        agent_results = await self.run_multi_agent_analysis("comprehensive", symbols)

        # Strategy discovery
        strategies = await self.agents["execution"].discover_strategies(
            regime, agent_results, risk_tolerance
        )

        return {
            "query": query,
            "market_regime": regime,
            "discovered_strategies": strategies,
            "risk_tolerance": risk_tolerance,
            "timestamp": datetime.now().isoformat()
        }

    async def _autonomous_execution(self, query, risk_tolerance, execution_mode):
        """Full autonomous trading execution"""
        # 1. Market Analysis
        analysis = await self._deep_market_analysis(query)

        # 2. Strategy Selection
        strategies = await self._discover_optimal_strategies(query, risk_tolerance)

        # 3. Risk Assessment
        risk_approval = await self.agents["risk"].assess_strategies(strategies)

        # 4. Execution (if approved)
        if risk_approval["approved"] and execution_mode == "autonomous":
            execution_result = await self.agents["execution"].execute_strategies(
                strategies["discovered_strategies"]
            )
        else:
            execution_result = {"status": "pending_approval", "reason": risk_approval["reason"]}

        return {
            "query": query,
            "analysis": analysis,
            "strategies": strategies,
            "risk_assessment": risk_approval,
            "execution": execution_result,
            "timestamp": datetime.now().isoformat()
        }

    async def _detect_current_regime(self):
        """Detect current market regime"""
        regime_query = """
        SELECT market_regime, volatility_regime, trend_regime, momentum_regime,
               correlation_regime, confidence_score, regime_probability
        FROM market_regime_detection
        ORDER BY timestamp DESC
        LIMIT 1
        """

        results = await self.remote.execute_query(regime_query)
        return results[0] if results else {"market_regime": "unknown", "confidence_score": 0.0}

class FundamentalAnalysisAgent:
    """Autonomous fundamental analysis agent"""

    def __init__(self, remote_control):
        self.remote = remote_control

    async def analyze(self, symbols):
        """Comprehensive fundamental analysis"""
        analysis_results = {}

        for symbol in symbols:
            fundamental_query = """
            SELECT symbol, pe_ratio, earnings_growth, revenue_growth,
                   debt_to_equity, roa, roe, analyst_ratings, price_target,
                   earnings_surprise_history, insider_trading_activity
            FROM fundamental_data
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """

            result = await self.remote.execute_query(fundamental_query, (symbol,))
            if result:
                analysis_results[symbol] = {
                    "fundamental_data": result[0],
                    "valuation_assessment": await self._assess_valuation(result[0]),
                    "growth_prospects": await self._assess_growth(result[0]),
                    "financial_health": await self._assess_health(result[0])
                }

        return {
            "agent": "fundamental",
            "analysis": analysis_results,
            "summary": await self._generate_fundamental_summary(analysis_results),
            "timestamp": datetime.now().isoformat()
        }

    async def _assess_valuation(self, data):
        """Assess if stock is overvalued, undervalued, or fairly valued"""
        pe_ratio = data.get('pe_ratio', 0)
        if pe_ratio < 15:
            return "undervalued"
        elif pe_ratio > 25:
            return "overvalued"
        else:
            return "fairly_valued"

    async def _assess_growth(self, data):
        """Assess growth prospects"""
        earnings_growth = data.get('earnings_growth', 0)
        revenue_growth = data.get('revenue_growth', 0)

        if earnings_growth > 15 and revenue_growth > 10:
            return "strong_growth"
        elif earnings_growth < 5 or revenue_growth < 5:
            return "weak_growth"
        else:
            return "moderate_growth"

    async def _assess_health(self, data):
        """Assess financial health"""
        debt_to_equity = data.get('debt_to_equity', 1.0)
        roe = data.get('roe', 0)

        if debt_to_equity < 0.5 and roe > 15:
            return "excellent"
        elif debt_to_equity > 2.0 or roe < 5:
            return "poor"
        else:
            return "good"

    async def _generate_fundamental_summary(self, analysis_results):
        """Generate summary of fundamental analysis"""
        summaries = []
        for symbol, analysis in analysis_results.items():
            summaries.append(
                f"{symbol}: {analysis['valuation_assessment']}, "
                f"{analysis['growth_prospects']}, {analysis['financial_health']}"
            )
        return summaries

class TechnicalAnalysisAgent:
    """Autonomous technical analysis agent"""

    def __init__(self, remote_control):
        self.remote = remote_control

    async def analyze(self, symbols):
        """Comprehensive technical analysis"""
        analysis_results = {}

        for symbol in symbols:
            technical_query = """
            SELECT symbol, rsi_14, macd_line, macd_signal, bb_upper, bb_lower,
                   support_1, support_2, resistance_1, resistance_2,
                   volume_sma_20, price_sma_20, price_sma_50, price_sma_200,
                   momentum_1d, momentum_1w, trend_strength
            FROM technical_indicators
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """

            result = await self.remote.execute_query(technical_query, (symbol,))
            if result:
                analysis_results[symbol] = {
                    "technical_data": result[0],
                    "trend_analysis": await self._analyze_trend(result[0]),
                    "momentum_analysis": await self._analyze_momentum(result[0]),
                    "support_resistance": await self._analyze_levels(result[0]),
                    "signals": await self._generate_signals(result[0])
                }

        return {
            "agent": "technical",
            "analysis": analysis_results,
            "summary": await self._generate_technical_summary(analysis_results),
            "timestamp": datetime.now().isoformat()
        }

    async def _analyze_trend(self, data):
        """Analyze price trend"""
        sma_20 = data.get('price_sma_20', 0)
        sma_50 = data.get('price_sma_50', 0)
        sma_200 = data.get('price_sma_200', 0)

        if sma_20 > sma_50 > sma_200:
            return "strong_uptrend"
        elif sma_20 < sma_50 < sma_200:
            return "strong_downtrend"
        elif sma_20 > sma_50:
            return "short_term_uptrend"
        else:
            return "mixed_trend"

    async def _analyze_momentum(self, data):
        """Analyze momentum indicators"""
        rsi = data.get('rsi_14', 50)
        momentum_1d = data.get('momentum_1d', 0)

        if rsi > 70 and momentum_1d > 2:
            return "overbought_strong"
        elif rsi < 30 and momentum_1d < -2:
            return "oversold_strong"
        elif rsi > 60:
            return "bullish_momentum"
        elif rsi < 40:
            return "bearish_momentum"
        else:
            return "neutral_momentum"

    async def _analyze_levels(self, data):
        """Analyze support and resistance levels"""
        return {
            "support_levels": [data.get('support_1'), data.get('support_2')],
            "resistance_levels": [data.get('resistance_1'), data.get('resistance_2')],
            "bollinger_bands": {
                "upper": data.get('bb_upper'),
                "lower": data.get('bb_lower')
            }
        }

    async def _generate_signals(self, data):
        """Generate trading signals"""
        signals = []

        rsi = data.get('rsi_14', 50)
        macd_line = data.get('macd_line', 0)
        macd_signal = data.get('macd_signal', 0)

        if rsi < 30 and macd_line > macd_signal:
            signals.append("BUY_SIGNAL")
        elif rsi > 70 and macd_line < macd_signal:
            signals.append("SELL_SIGNAL")

        return signals

    async def _generate_technical_summary(self, analysis_results):
        """Generate summary of technical analysis"""
        summaries = []
        for symbol, analysis in analysis_results.items():
            signals = ", ".join(analysis['signals']) if analysis['signals'] else "No signals"
            summaries.append(
                f"{symbol}: {analysis['trend_analysis']}, "
                f"{analysis['momentum_analysis']}, Signals: {signals}"
            )
        return summaries

class SentimentAnalysisAgent:
    """Autonomous sentiment analysis agent"""

    def __init__(self, remote_control):
        self.remote = remote_control

    async def analyze(self, symbols):
        """Comprehensive sentiment analysis"""
        analysis_results = {}

        for symbol in symbols:
            sentiment_query = """
            SELECT symbol, news_sentiment_24h, social_sentiment_24h,
                   analyst_sentiment, insider_sentiment, options_sentiment,
                   news_volume_24h, social_mentions_24h, sentiment_trend
            FROM sentiment_analysis
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """

            result = await self.remote.execute_query(sentiment_query, (symbol,))
            if result:
                analysis_results[symbol] = {
                    "sentiment_data": result[0],
                    "overall_sentiment": await self._calculate_overall_sentiment(result[0]),
                    "sentiment_strength": await self._assess_sentiment_strength(result[0]),
                    "sentiment_momentum": await self._analyze_sentiment_momentum(result[0])
                }

        return {
            "agent": "sentiment",
            "analysis": analysis_results,
            "summary": await self._generate_sentiment_summary(analysis_results),
            "timestamp": datetime.now().isoformat()
        }

    async def _calculate_overall_sentiment(self, data):
        """Calculate weighted overall sentiment"""
        news_sentiment = data.get('news_sentiment_24h', 0) * 0.4
        social_sentiment = data.get('social_sentiment_24h', 0) * 0.3
        analyst_sentiment = data.get('analyst_sentiment', 0) * 0.3

        overall = news_sentiment + social_sentiment + analyst_sentiment

        if overall > 0.3:
            return "bullish"
        elif overall < -0.3:
            return "bearish"
        else:
            return "neutral"

    async def _assess_sentiment_strength(self, data):
        """Assess strength of sentiment"""
        news_volume = data.get('news_volume_24h', 0)
        social_mentions = data.get('social_mentions_24h', 0)

        if news_volume > 50 and social_mentions > 1000:
            return "very_strong"
        elif news_volume > 20 and social_mentions > 500:
            return "strong"
        elif news_volume > 10 and social_mentions > 200:
            return "moderate"
        else:
            return "weak"

    async def _analyze_sentiment_momentum(self, data):
        """Analyze sentiment momentum"""
        sentiment_trend = data.get('sentiment_trend', 0)

        if sentiment_trend > 0.2:
            return "improving"
        elif sentiment_trend < -0.2:
            return "deteriorating"
        else:
            return "stable"

    async def _generate_sentiment_summary(self, analysis_results):
        """Generate summary of sentiment analysis"""
        summaries = []
        for symbol, analysis in analysis_results.items():
            summaries.append(
                f"{symbol}: {analysis['overall_sentiment']} "
                f"({analysis['sentiment_strength']} strength, "
                f"{analysis['sentiment_momentum']} momentum)"
            )
        return summaries

class OptionsFlowAgent:
    """Autonomous options flow analysis agent"""

    def __init__(self, remote_control):
        self.remote = remote_control

    async def analyze(self, symbols):
        """Comprehensive options flow analysis"""
        analysis_results = {}

        for symbol in symbols:
            flow_query = """
            SELECT symbol, call_volume, put_volume, call_oi, put_oi,
                   unusual_call_activity, unusual_put_activity,
                   gamma_exposure, delta_exposure, iv_rank, iv_percentile,
                   dark_pool_sentiment, institutional_flow
            FROM options_flow_analysis
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """

            result = await self.remote.execute_query(flow_query, (symbol,))
            if result:
                analysis_results[symbol] = {
                    "flow_data": result[0],
                    "flow_sentiment": await self._analyze_flow_sentiment(result[0]),
                    "unusual_activity": await self._detect_unusual_activity(result[0]),
                    "gamma_implications": await self._analyze_gamma_impact(result[0])
                }

        return {
            "agent": "options_flow",
            "analysis": analysis_results,
            "summary": await self._generate_flow_summary(analysis_results),
            "timestamp": datetime.now().isoformat()
        }

    async def _analyze_flow_sentiment(self, data):
        """Analyze options flow sentiment"""
        call_volume = data.get('call_volume', 0)
        put_volume = data.get('put_volume', 0)

        if call_volume > put_volume * 2:
            return "very_bullish"
        elif call_volume > put_volume * 1.5:
            return "bullish"
        elif put_volume > call_volume * 2:
            return "very_bearish"
        elif put_volume > call_volume * 1.5:
            return "bearish"
        else:
            return "neutral"

    async def _detect_unusual_activity(self, data):
        """Detect unusual options activity"""
        unusual_calls = data.get('unusual_call_activity', False)
        unusual_puts = data.get('unusual_put_activity', False)

        if unusual_calls and unusual_puts:
            return "unusual_straddle_activity"
        elif unusual_calls:
            return "unusual_call_buying"
        elif unusual_puts:
            return "unusual_put_buying"
        else:
            return "normal_activity"

    async def _analyze_gamma_impact(self, data):
        """Analyze gamma exposure impact"""
        gamma_exposure = data.get('gamma_exposure', 0)

        if gamma_exposure > 1000000:
            return "high_positive_gamma"
        elif gamma_exposure < -1000000:
            return "high_negative_gamma"
        elif abs(gamma_exposure) > 500000:
            return "moderate_gamma_exposure"
        else:
            return "low_gamma_exposure"

    async def _generate_flow_summary(self, analysis_results):
        """Generate summary of options flow analysis"""
        summaries = []
        for symbol, analysis in analysis_results.items():
            summaries.append(
                f"{symbol}: {analysis['flow_sentiment']} flow, "
                f"{analysis['unusual_activity']}, {analysis['gamma_implications']}"
            )
        return summaries

class ResearchCoordinatorAgent:
    """Coordinates multi-agent research and synthesis"""

    def __init__(self, remote_control):
        self.remote = remote_control

    async def synthesize_insights(self, agent_results):
        """Multi-agent debate and consensus building"""
        synthesis = {
            "consensus_view": await self._build_consensus(agent_results),
            "conflicting_signals": await self._identify_conflicts(agent_results),
            "high_confidence_signals": await self._identify_high_confidence(agent_results),
            "recommended_actions": await self._generate_recommendations(agent_results)
        }

        return synthesis

    async def _build_consensus(self, agent_results):
        """Build consensus from all agent views"""
        consensus = {}

        # Aggregate all agent summaries
        all_summaries = []
        for agent_name, result in agent_results.items():
            if isinstance(result, dict) and 'summary' in result:
                all_summaries.extend(result['summary'])

        # Simple consensus logic (can be enhanced with ML)
        bullish_signals = sum(1 for summary in all_summaries if any(
            word in summary.lower() for word in ['bullish', 'buy', 'strong_uptrend', 'undervalued']
        ))

        bearish_signals = sum(1 for summary in all_summaries if any(
            word in summary.lower() for word in ['bearish', 'sell', 'downtrend', 'overvalued']
        ))

        if bullish_signals > bearish_signals * 1.5:
            consensus['market_view'] = "bullish"
        elif bearish_signals > bullish_signals * 1.5:
            consensus['market_view'] = "bearish"
        else:
            consensus['market_view'] = "neutral"

        consensus['signal_strength'] = abs(bullish_signals - bearish_signals)

        return consensus

    async def _identify_conflicts(self, agent_results):
        """Identify conflicting signals between agents"""
        conflicts = []

        # Check for fundamental vs technical conflicts
        if ('fundamental' in agent_results and 'technical' in agent_results):
            fund_summaries = " ".join(agent_results['fundamental'].get('summary', []))
            tech_summaries = " ".join(agent_results['technical'].get('summary', []))

            if ('bullish' in fund_summaries and 'bearish' in tech_summaries) or \
               ('bearish' in fund_summaries and 'bullish' in tech_summaries):
                conflicts.append("fundamental_technical_divergence")

        return conflicts

    async def _identify_high_confidence(self, agent_results):
        """Identify high confidence signals"""
        high_confidence = []

        for agent_name, result in agent_results.items():
            if isinstance(result, dict) and 'summary' in result:
                summaries = result['summary']
                for summary in summaries:
                    if any(word in summary.lower() for word in [
                        'very_strong', 'excellent', 'unusual', 'strong_uptrend', 'strong_downtrend'
                    ]):
                        high_confidence.append(f"{agent_name}: {summary}")

        return high_confidence

    async def _generate_recommendations(self, agent_results):
        """Generate actionable recommendations"""
        recommendations = []

        consensus = await self._build_consensus(agent_results)

        if consensus['market_view'] == 'bullish' and consensus['signal_strength'] > 2:
            recommendations.append("Consider long positions in strong momentum stocks")
        elif consensus['market_view'] == 'bearish' and consensus['signal_strength'] > 2:
            recommendations.append("Consider defensive positioning or short opportunities")

        # Add options flow recommendations
        if 'options_flow' in agent_results:
            flow_summaries = agent_results['options_flow'].get('summary', [])
            for summary in flow_summaries:
                if 'unusual_call_buying' in summary:
                    recommendations.append(f"Monitor for gamma squeeze potential: {summary}")
                elif 'high_positive_gamma' in summary:
                    recommendations.append(f"Expect amplified moves: {summary}")

        return recommendations

class StrategyExecutionAgent:
    """Autonomous strategy execution agent"""

    def __init__(self, remote_control):
        self.remote = remote_control

    async def discover_strategies(self, regime, agent_results, risk_tolerance):
        """Discover optimal strategies based on analysis"""
        strategies = []

        # Strategy selection based on market regime
        if regime['market_regime'] == 'bull_momentum':
            strategies.extend(['momentum_following', 'call_buying', 'breakout_trading'])
        elif regime['market_regime'] == 'bear_momentum':
            strategies.extend(['short_selling', 'put_buying', 'defensive_hedging'])
        elif regime['market_regime'] == 'high_volatility':
            strategies.extend(['volatility_selling', 'iron_condors', 'straddle_selling'])
        elif regime['market_regime'] == 'range_bound':
            strategies.extend(['mean_reversion', 'theta_strategies', 'range_trading'])

        # Enhance strategies based on agent insights
        consensus = agent_results.get('synthesis', {}).get('consensus_view', {})
        if consensus.get('market_view') == 'bullish':
            strategies = [s for s in strategies if 'bear' not in s and 'short' not in s]
        elif consensus.get('market_view') == 'bearish':
            strategies = [s for s in strategies if 'bull' not in s and 'call' not in s]

        # Apply risk tolerance
        if risk_tolerance < 0.015:  # Conservative
            strategies = [s for s in strategies if any(
                conservative in s for conservative in ['iron_condor', 'covered', 'defensive']
            )]

        return {
            "recommended_strategies": strategies,
            "strategy_rationale": await self._explain_strategy_selection(regime, consensus),
            "risk_assessment": await self._assess_strategy_risk(strategies, risk_tolerance)
        }

    async def _explain_strategy_selection(self, regime, consensus):
        """Explain why strategies were selected"""
        rationale = []

        rationale.append(f"Market regime: {regime['market_regime']}")
        rationale.append(f"Agent consensus: {consensus.get('market_view', 'neutral')}")

        return rationale

    async def _assess_strategy_risk(self, strategies, risk_tolerance):
        """Assess risk of selected strategies"""
        risk_scores = {
            'momentum_following': 0.8,
            'call_buying': 0.9,
            'short_selling': 0.9,
            'iron_condors': 0.4,
            'mean_reversion': 0.6
        }

        strategy_risks = []
        for strategy in strategies:
            risk_score = risk_scores.get(strategy, 0.5)
            strategy_risks.append({
                "strategy": strategy,
                "risk_score": risk_score,
                "suitable_for_tolerance": risk_score <= risk_tolerance * 5  # Scale factor
            })

        return strategy_risks

class RiskManagementAgent:
    """Autonomous risk management agent"""

    def __init__(self, remote_control):
        self.remote = remote_control

    async def assess_strategies(self, strategies):
        """Assess risk of proposed strategies"""
        risk_assessment = {
            "approved": True,
            "reason": "All strategies within risk parameters",
            "risk_score": 0.0,
            "recommendations": []
        }

        # Assess each strategy
        total_risk = 0
        for strategy_data in strategies.get('recommended_strategies', []):
            strategy_risk = await self._calculate_strategy_risk(strategy_data)
            total_risk += strategy_risk

        risk_assessment['risk_score'] = total_risk

        # Risk approval logic
        if total_risk > 0.8:
            risk_assessment['approved'] = False
            risk_assessment['reason'] = "Total portfolio risk exceeds maximum threshold"
        elif total_risk > 0.6:
            risk_assessment['recommendations'].append("Consider reducing position sizes")

        return risk_assessment

    async def _calculate_strategy_risk(self, strategy):
        """Calculate risk score for individual strategy"""
        risk_scores = {
            'momentum_following': 0.7,
            'call_buying': 0.8,
            'short_selling': 0.9,
            'put_buying': 0.8,
            'iron_condors': 0.3,
            'straddle_selling': 0.6,
            'mean_reversion': 0.5
        }

        return risk_scores.get(strategy, 0.5)

if __name__ == "__main__":
    mcp.run()