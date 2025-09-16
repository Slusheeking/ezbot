#!/bin/bash

# QuestDB Installation Script for EzBot Trading System
# Based on QuestDB documentation: https://questdb.io/docs/deployment/

set -euo pipefail

QUESTDB_VERSION="8.1.1"
QUESTDB_DIR="/home/ezb0t/ezbot/questdb"
QUESTDB_JAR_URL="https://github.com/questdb/questdb/releases/download/${QUESTDB_VERSION}/questdb-${QUESTDB_VERSION}-no-jre-bin.tar.gz"

echo "🚀 Installing QuestDB ${QUESTDB_VERSION} for EzBot Trading System"

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "❌ Java is not installed. Installing OpenJDK 11..."
    sudo apt update
    sudo apt install -y openjdk-11-jdk
fi

# Verify Java version
java_version=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$java_version" -lt 11 ]; then
    echo "❌ Java 11 or higher is required. Current version: $java_version"
    exit 1
fi

echo "✅ Java version check passed"

# Create QuestDB directories
echo "📁 Creating QuestDB directories..."
mkdir -p "${QUESTDB_DIR}"/{data,logs,temp}

# Download QuestDB if not already present
if [ ! -f "${QUESTDB_DIR}/questdb.jar" ]; then
    echo "📥 Downloading QuestDB ${QUESTDB_VERSION}..."
    cd "${QUESTDB_DIR}"
    curl -L "${QUESTDB_JAR_URL}" -o questdb.tar.gz
    tar -xzf questdb.tar.gz --strip-components=1
    rm questdb.tar.gz
    echo "✅ QuestDB downloaded and extracted"
else
    echo "✅ QuestDB jar already exists"
fi

# Set proper permissions
echo "🔐 Setting file permissions..."
chmod +x "${QUESTDB_DIR}/bin/questdb.sh" 2>/dev/null || true
chown -R ezb0t:ezb0t "${QUESTDB_DIR}"

# Install systemd service
echo "⚙️ Installing systemd service..."
if [ -f "/home/ezb0t/ezbot/systemd/questdb.service" ]; then
    sudo cp "/home/ezb0t/ezbot/systemd/questdb.service" "/etc/systemd/system/"
    sudo systemctl daemon-reload
    sudo systemctl enable questdb.service
    echo "✅ QuestDB systemd service installed and enabled"
else
    echo "❌ QuestDB service file not found at /home/ezb0t/ezbot/systemd/questdb.service"
    exit 1
fi

# Create initial database schema for trading data
echo "💾 Creating initial database schema..."
cat > "${QUESTDB_DIR}/init_schema.sql" << 'EOF'
-- Trading data tables for EzBot system

-- Price data table
CREATE TABLE IF NOT EXISTS price_data (
    symbol STRING,
    timestamp TIMESTAMP,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    volume LONG,
    vwap DOUBLE
) timestamp(timestamp) PARTITION BY DAY;

-- Options flow data
CREATE TABLE IF NOT EXISTS options_flow (
    symbol STRING,
    timestamp TIMESTAMP,
    strike DOUBLE,
    expiry DATE,
    call_put STRING,
    premium DOUBLE,
    volume LONG,
    open_interest LONG,
    implied_volatility DOUBLE
) timestamp(timestamp) PARTITION BY DAY;

-- Market sentiment data
CREATE TABLE IF NOT EXISTS market_sentiment (
    timestamp TIMESTAMP,
    vix DOUBLE,
    fear_greed_index INT,
    put_call_ratio DOUBLE,
    market_cap DOUBLE
) timestamp(timestamp) PARTITION BY DAY;

-- News sentiment
CREATE TABLE IF NOT EXISTS news_sentiment (
    timestamp TIMESTAMP,
    symbol STRING,
    headline STRING,
    sentiment_score DOUBLE,
    source STRING,
    url STRING
) timestamp(timestamp) PARTITION BY DAY;

-- Insider trading
CREATE TABLE IF NOT EXISTS insider_trading (
    timestamp TIMESTAMP,
    symbol STRING,
    insider_name STRING,
    transaction_type STRING,
    shares LONG,
    price DOUBLE,
    value DOUBLE
) timestamp(timestamp) PARTITION BY DAY;

-- Dark pool data
CREATE TABLE IF NOT EXISTS darkpool_data (
    timestamp TIMESTAMP,
    symbol STRING,
    volume LONG,
    percentage DOUBLE,
    avg_price DOUBLE
) timestamp(timestamp) PARTITION BY DAY;
EOF

echo "✅ Database schema file created at ${QUESTDB_DIR}/init_schema.sql"

echo ""
echo "🎉 QuestDB installation completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Start QuestDB: sudo systemctl start questdb"
echo "   2. Check status: sudo systemctl status questdb"
echo "   3. View logs: sudo journalctl -u questdb -f"
echo "   4. Access Web Console: http://localhost:9000"
echo "   5. Connect via PostgreSQL: psql -h localhost -p 8812 -U admin -d qdb"
echo ""
echo "🔧 Configuration:"
echo "   - Config file: ${QUESTDB_DIR}/server.conf"
echo "   - Data directory: ${QUESTDB_DIR}/data"
echo "   - Logs directory: ${QUESTDB_DIR}/logs"
echo ""
echo "📊 To initialize the trading schema:"
echo "   cat ${QUESTDB_DIR}/init_schema.sql | psql -h localhost -p 8812 -U admin -d qdb"