# QuestDB Setup for EzBot Trading System

This directory contains the QuestDB time-series database setup for the EzBot trading system.

## Overview

QuestDB is configured to store and analyze trading data including:
- Real-time price data
- Options flow
- Market sentiment indicators
- News sentiment analysis
- Insider trading data
- Dark pool activity

## Installation

Run the installation script:
```bash
./install.sh
```

## Configuration

- **Config file**: `server.conf` - Main QuestDB configuration
- **Service file**: `../systemd/questdb.service` - Systemd service definition
- **Schema**: `init_schema.sql` - Initial database tables for trading data

## Usage

### Start/Stop Service
```bash
# Start QuestDB
sudo systemctl start questdb

# Stop QuestDB
sudo systemctl stop questdb

# Check status
sudo systemctl status questdb

# View logs
sudo journalctl -u questdb -f
```

### Access Methods

1. **Web Console**: http://localhost:9000
2. **PostgreSQL Wire**: `psql -h localhost -p 8812 -U admin -d qdb`
3. **InfluxDB Line Protocol**:
   - HTTP: `localhost:9000/write`
   - TCP: `localhost:9009`

### Initialize Schema

After starting QuestDB, run:
```bash
cat init_schema.sql | psql -h localhost -p 8812 -U admin -d qdb
```

## Integration with Trading Feeds

The existing systemd services can connect to QuestDB using:

### Python Example (for feed services)
```python
import psycopg2

# Connect to QuestDB
conn = psycopg2.connect(
    host="localhost",
    port="8812",
    user="admin",
    password="quest",
    database="qdb"
)

# Insert price data
cursor = conn.cursor()
cursor.execute("""
    INSERT INTO price_data (symbol, timestamp, open, high, low, close, volume)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", ('AAPL', '2024-01-01T10:00:00.000Z', 150.0, 152.0, 149.0, 151.0, 1000000))
conn.commit()
```

### InfluxDB Line Protocol Example
```python
import requests

# Send data via HTTP
data = "price_data,symbol=AAPL open=150.0,high=152.0,low=149.0,close=151.0,volume=1000000i"
response = requests.post('http://localhost:9000/write', data=data)
```

## Performance Tuning

The configuration is optimized for trading data with:
- Daily partitioning for efficient time-based queries
- Increased buffer sizes for high-frequency data
- Automatic table/column creation for dynamic feeds

## Security Notes

- Default credentials: `admin/quest` (change in production)
- Database bound to localhost only
- Telemetry disabled
- No external access by default

## Monitoring

View QuestDB metrics at: http://localhost:9000/status

## Troubleshooting

- **Service won't start**: Check Java installation and logs
- **Permission errors**: Ensure proper ownership of questdb directory
- **Memory issues**: Adjust JVM heap size in systemd service file
- **Connection refused**: Verify ports 9000, 8812, 9009 are available