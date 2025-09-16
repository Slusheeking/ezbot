# QuestDB MCP Server

A Model Context Protocol (MCP) server for interacting with QuestDB, a high-performance time-series database.

## Features

### Database Management
- **create_table**: Create new tables with timestamp partitioning
- **drop_table**: Remove tables safely
- **list_tables**: View all tables with metadata
- **describe_table**: Get detailed table structure information

### Data Operations
- **insert_data**: Insert structured data into tables
- **import_csv**: Bulk import CSV data
- **execute_query**: Run custom SQL queries

### Time-Series Analytics
- **time_series_query**: Perform time-bucketed aggregations
- **sample_data**: Get sample records with filtering
- **latest_by_symbol**: Get latest records per symbol/group
- **get_table_stats**: Analyze table statistics

### Performance
- **create_index**: Add indexes for better query performance

## Connection Methods

The server supports two connection methods to QuestDB:
- **HTTP REST API** (default): Fast for queries and data ingestion
- **PostgreSQL Wire Protocol**: Full SQL compatibility

## Environment Variables

```env
# QuestDB Connection (Optional - defaults provided)
QUESTDB_HOST=localhost
QUESTDB_PG_PORT=8812
QUESTDB_HTTP_PORT=9000
QUESTDB_USER=admin
QUESTDB_PASSWORD=quest
QUESTDB_DATABASE=qdb
```

## Installation

```bash
cd mcp/questdb_mcp
pip install -r requirements.txt
python server.py
```

## Usage Examples

### Creating a Trading Data Table
```python
# Create table for stock prices
await create_table(
    table_name="stock_prices",
    columns={
        "symbol": "SYMBOL",
        "price": "DOUBLE",
        "volume": "LONG",
        "timestamp": "TIMESTAMP"
    },
    timestamp_column="timestamp",
    partition_by="DAY"
)
```

### Time-Series Analysis
```python
# Get hourly price averages
await time_series_query(
    table_name="stock_prices",
    interval="1h",
    aggregations=[
        "avg(price) as avg_price",
        "sum(volume) as total_volume"
    ],
    start_time="2024-01-01",
    end_time="2024-01-02"
)
```

### Latest Data by Symbol
```python
# Get latest prices for specific stocks
await latest_by_symbol(
    table_name="stock_prices",
    symbol_column="symbol",
    symbols=["AAPL", "GOOGL", "MSFT"]
)
```

## Architecture

- Built on FastMCP framework
- Dual connection support (HTTP + PostgreSQL)
- Async/await for optimal performance
- Comprehensive error handling and logging
- Type-safe data operations

Perfect for financial data analysis, IoT metrics, and any time-series workload requiring high-performance analytics.