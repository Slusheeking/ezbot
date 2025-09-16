#!/usr/bin/env python3
"""
Comprehensive Polygon Data Feed with API SDK and TA-Lib Integration
Consolidates all Polygon streams: Stocks, Options, Crypto + Technical Indicators
Designed for Agentic AI Trading System with QuestDB integration
"""

import asyncio
import logging
import os
import json
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path

# Polygon API SDK
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import WebSocketMessage
from polygon.websocket.models.common import Feed

# TA-Lib for technical analysis
import talib

# Environment setup - Load from project root .env
from dotenv import load_dotenv

# Get absolute path to this feed directory
FEED_DIR = Path(__file__).parent.absolute()

# Load environment variables from project root .env file
PROJECT_ROOT = FEED_DIR.parent.parent
env_file = PROJECT_ROOT / ".env"
load_dotenv(env_file)

# Load configuration
def load_config():
    """Load settings from YAML configuration file"""
    config_path = FEED_DIR / "settings.yaml"
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Replace environment variables
        def replace_env_vars(obj):
            if isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                # Handle ${VAR:default} format
                env_var = obj[2:-1]
                if ":" in env_var:
                    var_name, default = env_var.split(":", 1)
                    return os.getenv(var_name, default)
                else:
                    return os.getenv(env_var, obj)
            return obj

        return replace_env_vars(config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return {}

def load_schema():
    """Load QuestDB schema from SQL file"""
    schema_path = FEED_DIR / "schema.sql"
    try:
        with open(schema_path, 'r') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return ""

# Load configuration and schema
CONFIG = load_config()
SCHEMA_SQL = load_schema()

# Setup logging from config
log_level = CONFIG.get('logging', {}).get('level', 'INFO')
log_format = CONFIG.get('logging', {}).get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=getattr(logging, log_level), format=log_format)
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Unified market data structure"""
    symbol: str
    timestamp: datetime
    price: float
    volume: int
    data_type: str  # 'stock', 'option', 'crypto', 'aggregate'
    raw_data: dict

class PolygonDataFeed:
    """
    Comprehensive Polygon data feed with real-time streams and technical analysis

    Features:
    - Real-time WebSocket streams for stocks, options, crypto
    - REST API for snapshots and historical data
    - TA-Lib technical indicator calculations
    - QuestDB integration for agentic AI system
    - High-performance data processing
    """

    def __init__(self):
        # Load configuration
        self.config = CONFIG

        # Polygon API configuration
        polygon_config = self.config.get('polygon', {})
        self.api_key = polygon_config.get('api_key')
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in configuration")

        # Initialize Polygon clients
        self.rest_client = RESTClient(self.api_key)
        self.websocket_client = None

        # QuestDB connection from config
        questdb_config = self.config.get('questdb', {})
        self.questdb_host = questdb_config.get('host', 'localhost')
        self.questdb_port = int(questdb_config.get('port', 9000))
        self.questdb_user = questdb_config.get('username', 'admin')
        self.questdb_password = questdb_config.get('password', 'quest')
        self.questdb_database = questdb_config.get('database', 'qdb')

        # Table names from config
        self.tables = questdb_config.get('tables', {})

        # WebSocket configuration
        websocket_config = self.config.get('websocket', {})
        self.websocket_config = websocket_config

        # TA-Lib configuration
        self.talib_config = self.config.get('talib', {})

        # Processing configuration
        self.processing_config = self.config.get('processing', {})

        # Data buffers for technical analysis
        self.price_buffers = {}  # symbol -> price history
        self.volume_buffers = {}  # symbol -> volume history
        self.technical_indicators = {}  # symbol -> calculated indicators

        # Buffer sizes from config
        self.lookback_periods = self.talib_config.get('lookback_periods', 200)
        self.min_data_points = self.talib_config.get('min_data_points', 50)

        # Subscribed symbols (can be made configurable later)
        self.stock_symbols = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"]
        self.crypto_symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD"]
        self.option_symbols = []  # Will be populated dynamically

        # Callbacks for real-time processing
        self.data_callbacks = []

        logger.info(f"Polygon Data Feed initialized with configuration from settings.yaml")
        logger.info(f"QuestDB: {self.questdb_host}:{self.questdb_port}")
        logger.info(f"TA-Lib lookback periods: {self.lookback_periods}")

    async def start(self):
        """Start all data feeds"""
        logger.info("Starting comprehensive Polygon data feed...")

        # Initialize database schema first
        await self.initialize_database_schema()

        # Initialize WebSocket client
        self.websocket_client = WebSocketClient(
            api_key=self.api_key,
            feed=Feed.RealTime,
            market=None,  # All markets
            subscriptions=self._get_subscriptions(),
            on_message=self._handle_websocket_message
        )

        # Start WebSocket connection
        await self._start_websocket()

        # Start REST API polling for additional data
        asyncio.create_task(self._poll_market_data())
        asyncio.create_task(self._poll_technical_indicators())

        logger.info("All Polygon data feeds started successfully")

    def _get_subscriptions(self) -> List[str]:
        """Get WebSocket subscriptions for all asset classes"""
        subscriptions = []

        # Stock subscriptions
        for symbol in self.stock_symbols:
            subscriptions.extend([
                f"T.{symbol}",      # Trades
                f"Q.{symbol}",      # Quotes
                f"A.{symbol}",      # Minute aggregates
                f"AM.{symbol}",     # Minute aggregates
            ])

        # Crypto subscriptions
        for symbol in self.crypto_symbols:
            subscriptions.extend([
                f"XT.{symbol}",     # Crypto trades
                f"XQ.{symbol}",     # Crypto quotes
                f"XA.{symbol}",     # Crypto aggregates
            ])

        # Add LULD (Limit Up Limit Down) and market status
        subscriptions.extend([
            "LULD.*",           # All LULD events
            "STATUS",           # Market status
        ])

        logger.info(f"Created {len(subscriptions)} WebSocket subscriptions")
        return subscriptions

    async def _start_websocket(self):
        """Start WebSocket connection with error handling"""
        try:
            await self.websocket_client.connect()
            logger.info("WebSocket connection established")
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            # Retry logic
            await asyncio.sleep(5)
            await self._start_websocket()

    async def _handle_websocket_message(self, message: WebSocketMessage):
        """Handle incoming WebSocket messages"""
        try:
            data = message.data
            message_type = message.message_type

            if message_type == "T":  # Trade
                await self._process_trade(data)
            elif message_type == "Q":  # Quote
                await self._process_quote(data)
            elif message_type == "A" or message_type == "AM":  # Aggregate
                await self._process_aggregate(data)
            elif message_type == "XT":  # Crypto trade
                await self._process_crypto_trade(data)
            elif message_type == "XQ":  # Crypto quote
                await self._process_crypto_quote(data)
            elif message_type == "XA":  # Crypto aggregate
                await self._process_crypto_aggregate(data)
            elif message_type == "LULD":  # LULD event
                await self._process_luld(data)
            elif message_type == "STATUS":  # Market status
                await self._process_market_status(data)

        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    async def _process_trade(self, data: dict):
        """Process stock trade data"""
        symbol = data.get("sym", "")
        price = data.get("p", 0.0)
        volume = data.get("s", 0)
        timestamp = datetime.fromtimestamp(data.get("t", 0) / 1000)

        # Update price buffer for technical analysis
        self._update_price_buffer(symbol, price, volume, timestamp)

        # Calculate technical indicators
        await self._calculate_technical_indicators(symbol)

        # Create market data object
        market_data = MarketData(
            symbol=symbol,
            timestamp=timestamp,
            price=price,
            volume=volume,
            data_type="stock_trade",
            raw_data=data
        )

        # Store in QuestDB
        await self._store_trade_data(market_data)

        # Notify callbacks
        await self._notify_callbacks(market_data)

    async def _process_quote(self, data: dict):
        """Process stock quote data"""
        symbol = data.get("sym", "")
        bid = data.get("bp", 0.0)
        ask = data.get("ap", 0.0)
        bid_size = data.get("bs", 0)
        ask_size = data.get("as", 0)
        timestamp = datetime.fromtimestamp(data.get("t", 0) / 1000)

        # Store quote data
        await self._store_quote_data(symbol, bid, ask, bid_size, ask_size, timestamp, "stock")

    async def _process_aggregate(self, data: dict):
        """Process minute aggregate data"""
        symbol = data.get("sym", "")
        open_price = data.get("o", 0.0)
        high_price = data.get("h", 0.0)
        low_price = data.get("l", 0.0)
        close_price = data.get("c", 0.0)
        volume = data.get("v", 0)
        timestamp = datetime.fromtimestamp(data.get("s", 0) / 1000)  # Start time

        # Update OHLCV buffer for technical analysis
        self._update_ohlcv_buffer(symbol, open_price, high_price, low_price, close_price, volume, timestamp)

        # Calculate technical indicators on OHLCV data
        await self._calculate_ohlcv_indicators(symbol)

        # Store aggregate data
        await self._store_aggregate_data(symbol, open_price, high_price, low_price, close_price, volume, timestamp, "stock")

    async def _process_crypto_trade(self, data: dict):
        """Process crypto trade data"""
        symbol = data.get("pair", "")
        price = data.get("p", 0.0)
        volume = data.get("s", 0.0)
        timestamp = datetime.fromtimestamp(data.get("t", 0) / 1000)

        # Update crypto price buffer
        self._update_price_buffer(f"crypto_{symbol}", price, volume, timestamp)

        # Calculate crypto technical indicators
        await self._calculate_technical_indicators(f"crypto_{symbol}")

        market_data = MarketData(
            symbol=symbol,
            timestamp=timestamp,
            price=price,
            volume=volume,
            data_type="crypto_trade",
            raw_data=data
        )

        await self._store_trade_data(market_data)
        await self._notify_callbacks(market_data)

    async def _process_crypto_quote(self, data: dict):
        """Process crypto quote data"""
        symbol = data.get("pair", "")
        bid = data.get("bp", 0.0)
        ask = data.get("ap", 0.0)
        timestamp = datetime.fromtimestamp(data.get("t", 0) / 1000)

        await self._store_quote_data(symbol, bid, ask, 0, 0, timestamp, "crypto")

    async def _process_crypto_aggregate(self, data: dict):
        """Process crypto aggregate data"""
        symbol = data.get("pair", "")
        open_price = data.get("o", 0.0)
        high_price = data.get("h", 0.0)
        low_price = data.get("l", 0.0)
        close_price = data.get("c", 0.0)
        volume = data.get("v", 0.0)
        timestamp = datetime.fromtimestamp(data.get("s", 0) / 1000)

        self._update_ohlcv_buffer(f"crypto_{symbol}", open_price, high_price, low_price, close_price, volume, timestamp)
        await self._calculate_ohlcv_indicators(f"crypto_{symbol}")
        await self._store_aggregate_data(symbol, open_price, high_price, low_price, close_price, volume, timestamp, "crypto")

    async def _process_luld(self, data: dict):
        """Process LULD (Limit Up Limit Down) events"""
        symbol = data.get("sym", "")
        limit_up_price = data.get("lu", 0.0)
        limit_down_price = data.get("ld", 0.0)
        timestamp = datetime.fromtimestamp(data.get("t", 0) / 1000)

        await self._store_luld_data(symbol, limit_up_price, limit_down_price, timestamp)

    async def _process_market_status(self, data: dict):
        """Process market status updates"""
        market = data.get("market", "")
        status = data.get("status", "")
        timestamp = datetime.fromtimestamp(data.get("t", 0) / 1000)

        await self._store_market_status(market, status, timestamp)

    def _update_price_buffer(self, symbol: str, price: float, volume: int, timestamp: datetime):
        """Update price buffer for technical analysis"""
        if symbol not in self.price_buffers:
            self.price_buffers[symbol] = []
            self.volume_buffers[symbol] = []

        # Keep last 200 data points for technical analysis
        self.price_buffers[symbol].append(price)
        self.volume_buffers[symbol].append(volume)

        if len(self.price_buffers[symbol]) > 200:
            self.price_buffers[symbol] = self.price_buffers[symbol][-200:]
            self.volume_buffers[symbol] = self.volume_buffers[symbol][-200:]

    def _update_ohlcv_buffer(self, symbol: str, open_p: float, high: float, low: float, close: float, volume: float, timestamp: datetime):
        """Update OHLCV buffer for technical analysis"""
        if symbol not in self.technical_indicators:
            self.technical_indicators[symbol] = {
                'ohlcv': [],
                'timestamps': []
            }

        # Store OHLCV data
        ohlcv_data = {
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }

        self.technical_indicators[symbol]['ohlcv'].append(ohlcv_data)
        self.technical_indicators[symbol]['timestamps'].append(timestamp)

        # Keep last 200 periods
        if len(self.technical_indicators[symbol]['ohlcv']) > 200:
            self.technical_indicators[symbol]['ohlcv'] = self.technical_indicators[symbol]['ohlcv'][-200:]
            self.technical_indicators[symbol]['timestamps'] = self.technical_indicators[symbol]['timestamps'][-200:]

    async def _calculate_technical_indicators(self, symbol: str):
        """Calculate TA-Lib technical indicators from price data using configuration"""
        min_data_points = self.talib_config.get('min_data_points', 50)

        if symbol not in self.price_buffers or len(self.price_buffers[symbol]) < min_data_points:
            return

        prices = np.array(self.price_buffers[symbol], dtype=np.float64)
        volumes = np.array(self.volume_buffers[symbol], dtype=np.float64)

        try:
            indicators = {}

            # RSI with configurable periods
            rsi_periods = self.talib_config.get('rsi_periods', [14, 30])
            for period in rsi_periods:
                rsi = talib.RSI(prices, timeperiod=period)
                indicators[f'rsi_{period}'] = rsi[-1] if len(rsi) > 0 and not np.isnan(rsi[-1]) else None

            # MACD with configurable periods
            macd_config = self.talib_config.get('macd', {})
            fast_period = macd_config.get('fast_period', 12)
            slow_period = macd_config.get('slow_period', 26)
            signal_period = macd_config.get('signal_period', 9)

            macd_line, macd_signal, macd_histogram = talib.MACD(
                prices, fastperiod=fast_period, slowperiod=slow_period, signalperiod=signal_period
            )
            indicators['macd'] = macd_line[-1] if len(macd_line) > 0 and not np.isnan(macd_line[-1]) else None
            indicators['macd_signal'] = macd_signal[-1] if len(macd_signal) > 0 and not np.isnan(macd_signal[-1]) else None
            indicators['macd_histogram'] = macd_histogram[-1] if len(macd_histogram) > 0 and not np.isnan(macd_histogram[-1]) else None

            # Moving averages with configurable periods
            sma_periods = self.talib_config.get('sma_periods', [20, 50, 200])
            for period in sma_periods:
                if len(prices) >= period:
                    sma = talib.SMA(prices, timeperiod=period)
                    indicators[f'sma_{period}'] = sma[-1] if len(sma) > 0 and not np.isnan(sma[-1]) else None

            ema_periods = self.talib_config.get('ema_periods', [12, 26, 50])
            for period in ema_periods:
                if len(prices) >= period:
                    ema = talib.EMA(prices, timeperiod=period)
                    indicators[f'ema_{period}'] = ema[-1] if len(ema) > 0 and not np.isnan(ema[-1]) else None

            # Bollinger Bands with configurable settings
            bb_period = self.talib_config.get('bb_period', 20)
            bb_std_dev = self.talib_config.get('bb_std_dev', 2)
            if len(prices) >= bb_period:
                bb_upper, bb_middle, bb_lower = talib.BBANDS(prices, timeperiod=bb_period, nbdevup=bb_std_dev, nbdevdn=bb_std_dev)
                indicators['bb_upper'] = bb_upper[-1] if len(bb_upper) > 0 and not np.isnan(bb_upper[-1]) else None
                indicators['bb_middle'] = bb_middle[-1] if len(bb_middle) > 0 and not np.isnan(bb_middle[-1]) else None
                indicators['bb_lower'] = bb_lower[-1] if len(bb_lower) > 0 and not np.isnan(bb_lower[-1]) else None

            # Volume indicators (if enabled)
            if self.talib_config.get('obv_enabled', True) and len(volumes) > 0:
                obv = talib.OBV(prices, volumes)
                indicators['obv'] = obv[-1] if len(obv) > 0 and not np.isnan(obv[-1]) else None

            # Additional oscillators with configurable periods
            williams_r_period = self.talib_config.get('williams_r_period', 14)
            if len(prices) >= williams_r_period:
                willr = talib.WILLR(prices, prices, prices, timeperiod=williams_r_period)
                indicators['williams_r'] = willr[-1] if len(willr) > 0 and not np.isnan(willr[-1]) else None

            cci_period = self.talib_config.get('cci_period', 14)
            if len(prices) >= cci_period:
                cci = talib.CCI(prices, prices, prices, timeperiod=cci_period)
                indicators['cci'] = cci[-1] if len(cci) > 0 and not np.isnan(cci[-1]) else None

            # Volatility indicators
            atr_period = self.talib_config.get('atr_period', 14)
            if len(prices) >= atr_period:
                atr = talib.ATR(prices, prices, prices, timeperiod=atr_period)
                indicators['atr'] = atr[-1] if len(atr) > 0 and not np.isnan(atr[-1]) else None

            # Add current price and volume
            indicators['current_price'] = prices[-1]
            indicators['current_volume'] = volumes[-1] if len(volumes) > 0 else 0

            # Store indicators in instance for later retrieval
            self.technical_indicators[symbol] = indicators

            # Store in QuestDB
            await self._store_technical_indicators(symbol, indicators, datetime.now())

        except Exception as e:
            logger.error(f"Error calculating technical indicators for {symbol}: {e}")

    async def _calculate_ohlcv_indicators(self, symbol: str):
        """Calculate TA-Lib indicators from OHLCV data"""
        if symbol not in self.technical_indicators or len(self.technical_indicators[symbol]['ohlcv']) < 20:
            return

        ohlcv_data = self.technical_indicators[symbol]['ohlcv']

        # Convert to numpy arrays
        opens = np.array([d['open'] for d in ohlcv_data], dtype=np.float64)
        highs = np.array([d['high'] for d in ohlcv_data], dtype=np.float64)
        lows = np.array([d['low'] for d in ohlcv_data], dtype=np.float64)
        closes = np.array([d['close'] for d in ohlcv_data], dtype=np.float64)
        volumes = np.array([d['volume'] for d in ohlcv_data], dtype=np.float64)

        try:
            # More accurate indicators with OHLC data
            rsi = talib.RSI(closes, timeperiod=14)
            macd_line, macd_signal, macd_histogram = talib.MACD(closes)

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(closes)

            # Stochastic
            stoch_k, stoch_d = talib.STOCH(highs, lows, closes)

            # Average True Range
            atr = talib.ATR(highs, lows, closes, timeperiod=14)

            # Williams %R
            willr = talib.WILLR(highs, lows, closes, timeperiod=14)

            # CCI
            cci = talib.CCI(highs, lows, closes, timeperiod=14)

            # Volume indicators
            ad_line = talib.AD(highs, lows, closes, volumes)
            obv = talib.OBV(closes, volumes)

            # Momentum indicators
            mom = talib.MOM(closes, timeperiod=10)
            roc = talib.ROC(closes, timeperiod=10)

            # Overlap studies
            sma_20 = talib.SMA(closes, timeperiod=20)
            sma_50 = talib.SMA(closes, timeperiod=50)
            sma_200 = talib.SMA(closes, timeperiod=200)
            ema_12 = talib.EMA(closes, timeperiod=12)
            ema_26 = talib.EMA(closes, timeperiod=26)

            # Pattern recognition (select few important ones)
            hammer = talib.CDLHAMMER(opens, highs, lows, closes)
            doji = talib.CDLDOJI(opens, highs, lows, closes)
            engulfing = talib.CDLENGULFING(opens, highs, lows, closes)

            # Store comprehensive indicators
            indicators = {
                'rsi_14': rsi[-1] if len(rsi) > 0 and not np.isnan(rsi[-1]) else None,
                'macd_line': macd_line[-1] if len(macd_line) > 0 and not np.isnan(macd_line[-1]) else None,
                'macd_signal': macd_signal[-1] if len(macd_signal) > 0 and not np.isnan(macd_signal[-1]) else None,
                'macd_histogram': macd_histogram[-1] if len(macd_histogram) > 0 and not np.isnan(macd_histogram[-1]) else None,
                'bb_upper': bb_upper[-1] if len(bb_upper) > 0 and not np.isnan(bb_upper[-1]) else None,
                'bb_middle': bb_middle[-1] if len(bb_middle) > 0 and not np.isnan(bb_middle[-1]) else None,
                'bb_lower': bb_lower[-1] if len(bb_lower) > 0 and not np.isnan(bb_lower[-1]) else None,
                'stoch_k': stoch_k[-1] if len(stoch_k) > 0 and not np.isnan(stoch_k[-1]) else None,
                'stoch_d': stoch_d[-1] if len(stoch_d) > 0 and not np.isnan(stoch_d[-1]) else None,
                'atr': atr[-1] if len(atr) > 0 and not np.isnan(atr[-1]) else None,
                'willr': willr[-1] if len(willr) > 0 and not np.isnan(willr[-1]) else None,
                'cci': cci[-1] if len(cci) > 0 and not np.isnan(cci[-1]) else None,
                'ad_line': ad_line[-1] if len(ad_line) > 0 and not np.isnan(ad_line[-1]) else None,
                'obv': obv[-1] if len(obv) > 0 and not np.isnan(obv[-1]) else None,
                'momentum': mom[-1] if len(mom) > 0 and not np.isnan(mom[-1]) else None,
                'roc': roc[-1] if len(roc) > 0 and not np.isnan(roc[-1]) else None,
                'sma_20': sma_20[-1] if len(sma_20) > 0 and not np.isnan(sma_20[-1]) else None,
                'sma_50': sma_50[-1] if len(sma_50) > 0 and not np.isnan(sma_50[-1]) else None,
                'sma_200': sma_200[-1] if len(sma_200) > 0 and not np.isnan(sma_200[-1]) else None,
                'ema_12': ema_12[-1] if len(ema_12) > 0 and not np.isnan(ema_12[-1]) else None,
                'ema_26': ema_26[-1] if len(ema_26) > 0 and not np.isnan(ema_26[-1]) else None,
                'hammer_pattern': hammer[-1] if len(hammer) > 0 else 0,
                'doji_pattern': doji[-1] if len(doji) > 0 else 0,
                'engulfing_pattern': engulfing[-1] if len(engulfing) > 0 else 0,
                'open': opens[-1],
                'high': highs[-1],
                'low': lows[-1],
                'close': closes[-1],
                'volume': volumes[-1]
            }

            # Store in QuestDB
            await self._store_technical_indicators(symbol, indicators, datetime.now())

        except Exception as e:
            logger.error(f"Error calculating OHLCV indicators for {symbol}: {e}")

    async def _poll_market_data(self):
        """Poll additional market data via REST API"""
        while True:
            try:
                # Get market snapshots
                await self._get_market_snapshots()

                # Get options data
                await self._get_options_data()

                # Get market status
                await self._get_market_status()

                # Wait before next poll
                await asyncio.sleep(60)  # Poll every minute

            except Exception as e:
                logger.error(f"Error in market data polling: {e}")
                await asyncio.sleep(30)

    async def _get_market_snapshots(self):
        """Get market snapshots via REST API"""
        try:
            # Get stock snapshots
            for symbol in self.stock_symbols:
                snapshot = self.rest_client.get_snapshot_ticker("stocks", symbol)
                if snapshot:
                    await self._process_snapshot(snapshot, "stock")

            # Get crypto snapshots
            for symbol in self.crypto_symbols:
                snapshot = self.rest_client.get_snapshot_ticker("crypto", symbol)
                if snapshot:
                    await self._process_snapshot(snapshot, "crypto")

        except Exception as e:
            logger.error(f"Error getting market snapshots: {e}")

    async def _process_snapshot(self, snapshot: dict, asset_type: str):
        """Process snapshot data"""
        ticker = snapshot.get("ticker", "")
        last_trade = snapshot.get("lastTrade", {})
        last_quote = snapshot.get("lastQuote", {})

        if last_trade:
            price = last_trade.get("p", 0.0)
            volume = last_trade.get("s", 0)
            timestamp = datetime.fromtimestamp(last_trade.get("t", 0) / 1000)

            market_data = MarketData(
                symbol=ticker,
                timestamp=timestamp,
                price=price,
                volume=volume,
                data_type=f"{asset_type}_snapshot",
                raw_data=snapshot
            )

            await self._store_trade_data(market_data)

    async def _get_options_data(self):
        """Get options data via REST API"""
        try:
            # Get options contracts for major stocks
            for symbol in ["SPY", "QQQ", "AAPL", "TSLA", "NVDA"]:
                # Get options contracts expiring within 30 days
                contracts = self.rest_client.list_options_contracts(
                    underlying_ticker=symbol,
                    expiration_date_lte=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                )

                if contracts:
                    for contract in contracts.results[:10]:  # Limit to 10 most active
                        await self._process_options_contract(contract)

        except Exception as e:
            logger.error(f"Error getting options data: {e}")

    async def _process_options_contract(self, contract: dict):
        """Process options contract data"""
        ticker = contract.get("ticker", "")
        underlying_ticker = contract.get("underlying_ticker", "")
        contract_type = contract.get("contract_type", "")
        strike_price = contract.get("strike_price", 0.0)
        expiration_date = contract.get("expiration_date", "")

        await self._store_options_contract(ticker, underlying_ticker, contract_type, strike_price, expiration_date)

    async def _get_market_status(self):
        """Get market status via REST API"""
        try:
            status = self.rest_client.get_market_status()
            if status:
                await self._store_market_status("stocks", status.get("market", ""), datetime.now())
        except Exception as e:
            logger.error(f"Error getting market status: {e}")

    async def _poll_technical_indicators(self):
        """Periodically calculate and store technical indicators"""
        while True:
            try:
                # Calculate indicators for all symbols with sufficient data
                for symbol in list(self.price_buffers.keys()):
                    if len(self.price_buffers[symbol]) >= 20:
                        await self._calculate_technical_indicators(symbol)

                for symbol in list(self.technical_indicators.keys()):
                    if len(self.technical_indicators[symbol]['ohlcv']) >= 20:
                        await self._calculate_ohlcv_indicators(symbol)

                # Wait before next calculation
                await asyncio.sleep(30)  # Calculate every 30 seconds

            except Exception as e:
                logger.error(f"Error in technical indicators polling: {e}")
                await asyncio.sleep(30)

    # QuestDB storage methods
    async def get_questdb_connection(self):
        """Get QuestDB connection"""
        try:
            conn = psycopg2.connect(
                host=self.questdb_host,
                port=self.questdb_port,
                user=self.questdb_user,
                password=self.questdb_password,
                database=self.questdb_database,
                cursor_factory=RealDictCursor
            )
            return conn
        except Exception as e:
            logger.error(f"QuestDB connection failed: {e}")
            raise

    async def initialize_database_schema(self):
        """Initialize QuestDB tables using the schema.sql file"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            # Split and execute each statement from schema.sql
            statements = [stmt.strip() for stmt in SCHEMA_SQL.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    try:
                        cursor.execute(statement)
                        conn.commit()
                        logger.debug(f"Executed schema statement: {statement[:50]}...")
                    except Exception as e:
                        logger.warning(f"Schema statement failed (may already exist): {e}")

            cursor.close()
            conn.close()
            logger.info("Database schema initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise

    async def _store_stock_data(self, market_data: MarketData):
        """Store stock data in QuestDB using configured table name"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            table_name = self.tables.get('polygon_stocks', 'polygon_stocks')

            query = f"""
            INSERT INTO {table_name} (symbol, timestamp, price, volume, data_type, feed_source)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                market_data.symbol,
                market_data.timestamp,
                market_data.price,
                market_data.volume,
                market_data.data_type,
                'polygon_live_feed'
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing stock data: {e}")

    async def _store_crypto_data(self, market_data: MarketData):
        """Store crypto data in QuestDB using configured table name"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            table_name = self.tables.get('polygon_crypto', 'polygon_crypto')

            query = f"""
            INSERT INTO {table_name} (symbol, timestamp, price, volume, data_type, feed_source)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (
                market_data.symbol,
                market_data.timestamp,
                market_data.price,
                market_data.volume,
                market_data.data_type,
                'polygon_live_feed'
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing crypto data: {e}")

    async def _store_options_data(self, market_data: MarketData):
        """Store options data in QuestDB using configured table name"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            table_name = self.tables.get('polygon_options', 'polygon_options')

            # Extract option details from symbol or raw_data
            raw_data = market_data.raw_data

            query = f"""
            INSERT INTO {table_name} (underlying_symbol, option_symbol, timestamp, price, volume, feed_source)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            underlying_symbol = raw_data.get('underlying_ticker', market_data.symbol)

            cursor.execute(query, (
                underlying_symbol,
                market_data.symbol,
                market_data.timestamp,
                market_data.price,
                market_data.volume,
                'polygon_live_feed'
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing options data: {e}")

    async def _store_quote_data(self, symbol: str, bid: float, ask: float, bid_size: int, ask_size: int, timestamp: datetime, asset_type: str):
        """Store quote data in QuestDB"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO quote_data (symbol, timestamp, bid, ask, bid_size, ask_size, asset_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (symbol, timestamp, bid, ask, bid_size, ask_size, asset_type))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing quote data: {e}")

    async def _store_aggregate_data(self, symbol: str, open_p: float, high: float, low: float, close: float, volume: float, timestamp: datetime, asset_type: str):
        """Store aggregate OHLCV data in QuestDB"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO aggregate_data (symbol, timestamp, open, high, low, close, volume, asset_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (symbol, timestamp, open_p, high, low, close, volume, asset_type))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing aggregate data: {e}")

    async def _store_technical_indicators(self, symbol: str, indicators: dict, timestamp: datetime):
        """Store technical indicators in QuestDB"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            # Convert None values to NULL for database storage
            indicator_values = []
            indicator_columns = []

            for key, value in indicators.items():
                indicator_columns.append(key)
                indicator_values.append(value if value is not None else None)

            columns_str = ", ".join(["symbol", "timestamp"] + indicator_columns)
            placeholders = ", ".join(["%s"] * (len(indicator_columns) + 2))

            query = f"""
            INSERT INTO technical_indicators ({columns_str})
            VALUES ({placeholders})
            """

            cursor.execute(query, [symbol, timestamp] + indicator_values)

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing technical indicators: {e}")

    async def _store_luld_data(self, symbol: str, limit_up: float, limit_down: float, timestamp: datetime):
        """Store LULD data in QuestDB"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO luld_data (symbol, timestamp, limit_up_price, limit_down_price)
            VALUES (%s, %s, %s, %s)
            """

            cursor.execute(query, (symbol, timestamp, limit_up, limit_down))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing LULD data: {e}")

    async def _store_market_status(self, market: str, status: str, timestamp: datetime):
        """Store market status in QuestDB"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO market_status (market, status, timestamp)
            VALUES (%s, %s, %s)
            """

            cursor.execute(query, (market, status, timestamp))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing market status: {e}")

    async def _store_options_contract(self, ticker: str, underlying: str, contract_type: str, strike: float, expiration: str):
        """Store options contract data in QuestDB"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            query = """
            INSERT INTO options_contracts (ticker, underlying_ticker, contract_type, strike_price, expiration_date, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            cursor.execute(query, (ticker, underlying, contract_type, strike, expiration, datetime.now()))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error storing options contract: {e}")

    # Callback system for real-time processing
    def add_callback(self, callback: Callable[[MarketData], None]):
        """Add callback for real-time data processing"""
        self.data_callbacks.append(callback)

    async def _notify_callbacks(self, market_data: MarketData):
        """Notify all registered callbacks"""
        for callback in self.data_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(market_data)
                else:
                    callback(market_data)
            except Exception as e:
                logger.error(f"Error in callback: {e}")

    async def stop(self):
        """Stop all data feeds"""
        if self.websocket_client:
            await self.websocket_client.disconnect()
        logger.info("Polygon Data Feed stopped")

    # Utility methods for agentic AI system
    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for symbol"""
        if symbol in self.price_buffers and self.price_buffers[symbol]:
            return self.price_buffers[symbol][-1]
        return None

    async def get_technical_indicator(self, symbol: str, indicator: str) -> Optional[float]:
        """Get specific technical indicator value"""
        try:
            conn = await self.get_questdb_connection()
            cursor = conn.cursor()

            query = f"""
            SELECT {indicator}
            FROM technical_indicators
            WHERE symbol = %s
            ORDER BY timestamp DESC
            LIMIT 1
            """

            cursor.execute(query, (symbol,))
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                return result[indicator]
            return None

        except Exception as e:
            logger.error(f"Error getting technical indicator: {e}")
            return None

# Main execution
async def main():
    """Main function to run the comprehensive Polygon data feed"""
    feed = PolygonDataFeed()

    # Add example callback
    async def example_callback(data: MarketData):
        logger.info(f"Received data: {data.symbol} @ ${data.price}")

    feed.add_callback(example_callback)

    try:
        await feed.start()

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await feed.stop()

if __name__ == "__main__":
    asyncio.run(main())