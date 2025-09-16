#!/usr/bin/env python3
"""
Custom QuestDB MCP Server for EZBot Trading System
Provides time-series database operations through QuestDB
"""

import asyncio
import json
import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Union
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
    name="questdb-data",
    instructions="""
    This server provides comprehensive time-series database operations through QuestDB.
    Use these tools to manage tables, ingest data, and query time-series data efficiently.
    QuestDB is optimized for high-performance time-series workloads and financial data analysis.
    """
)

class QuestDBClient:
    """QuestDB client with connection pooling and error handling"""

    def __init__(self):
        logger.info("Initializing QuestDBClient")
        # QuestDB connection parameters
        self.host = os.getenv("QUESTDB_HOST", "localhost")
        self.port = int(os.getenv("QUESTDB_PG_PORT", "8812"))  # PostgreSQL wire protocol port
        self.user = os.getenv("QUESTDB_USER", "admin")
        self.password = os.getenv("QUESTDB_PASSWORD", "quest")
        self.database = os.getenv("QUESTDB_DATABASE", "qdb")

        # HTTP connection for REST API
        self.http_host = os.getenv("QUESTDB_HTTP_HOST", "localhost")
        self.http_port = int(os.getenv("QUESTDB_HTTP_PORT", "9000"))
        self.http_base_url = f"http://{self.http_host}:{self.http_port}"

        self.session = None
        logger.info("QuestDBClient initialized successfully")

    async def _get_session(self):
        """Get or create HTTP session"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
        return self.session

    def _get_pg_connection(self):
        """Get PostgreSQL wire protocol connection"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to QuestDB via PostgreSQL wire protocol: {e}")
            raise

    async def _execute_sql_http(self, sql: str, params: Dict = None) -> Dict:
        """Execute SQL via HTTP REST API"""
        session = await self._get_session()
        url = f"{self.http_base_url}/exec"

        try:
            response = await session.get(url, params={"query": sql})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error executing SQL: {e}")
            return {"error": f"HTTP error: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            return {"error": f"Execution error: {str(e)}"}

    def _execute_sql_pg(self, sql: str, params: List = None, fetch: bool = True) -> Dict:
        """Execute SQL via PostgreSQL wire protocol"""
        try:
            with self._get_pg_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql, params)
                    if fetch and cursor.description:
                        results = cursor.fetchall()
                        return {
                            "data": [dict(row) for row in results],
                            "count": len(results)
                        }
                    else:
                        conn.commit()
                        return {"success": True, "rowcount": cursor.rowcount}
        except Exception as e:
            logger.error(f"PostgreSQL error: {e}")
            return {"error": f"PostgreSQL error: {str(e)}"}

    async def _import_csv_http(self, table_name: str, csv_data: str) -> Dict:
        """Import CSV data via HTTP"""
        session = await self._get_session()
        url = f"{self.http_base_url}/imp"

        try:
            response = await session.put(
                url,
                params={"name": table_name},
                content=csv_data,
                headers={"Content-Type": "application/octet-stream"}
            )
            response.raise_for_status()
            return {"success": True, "message": "CSV data imported successfully"}
        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            return {"error": f"CSV import error: {str(e)}"}

# Initialize QuestDB client
logger.info("Creating QuestDBClient instance")
try:
    questdb_client = QuestDBClient()
    logger.info("QuestDBClient instance created successfully")
except Exception as e:
    logger.error(f"Failed to create QuestDBClient: {e}")
    raise

@mcp.tool
async def execute_query(
    sql: str,
    method: str = "http"
) -> Dict[str, Any]:
    """
    Execute a SQL query against QuestDB.

    Args:
        sql: SQL query to execute
        method: Connection method ('http' or 'pg')

    Returns:
        Query results or error information
    """
    logger.info(f"Executing query via {method}: {sql[:100]}...")

    if method == "http":
        result = await questdb_client._execute_sql_http(sql)
    else:
        result = questdb_client._execute_sql_pg(sql)

    return result

@mcp.tool
async def create_table(
    table_name: str,
    columns: Dict[str, str],
    timestamp_column: str = "timestamp",
    partition_by: str = "DAY"
) -> Dict[str, Any]:
    """
    Create a new table in QuestDB.

    Args:
        table_name: Name of the table to create
        columns: Dictionary of column_name: data_type pairs
        timestamp_column: Name of the timestamp column for partitioning
        partition_by: Partition strategy (HOUR, DAY, WEEK, MONTH, YEAR)

    Returns:
        Success status or error information
    """
    # Build column definitions
    column_defs = []
    for col_name, col_type in columns.items():
        column_defs.append(f"{col_name} {col_type}")

    columns_sql = ", ".join(column_defs)

    sql = f"""
    CREATE TABLE {table_name} (
        {columns_sql}
    ) timestamp({timestamp_column}) PARTITION BY {partition_by}
    """

    result = questdb_client._execute_sql_pg(sql, fetch=False)
    return result

@mcp.tool
async def drop_table(
    table_name: str
) -> Dict[str, Any]:
    """
    Drop a table from QuestDB.

    Args:
        table_name: Name of the table to drop

    Returns:
        Success status or error information
    """
    sql = f"DROP TABLE IF EXISTS {table_name}"
    result = questdb_client._execute_sql_pg(sql, fetch=False)
    return result

@mcp.tool
async def list_tables() -> Dict[str, Any]:
    """
    List all tables in QuestDB.

    Returns:
        List of tables with metadata
    """
    sql = """
    SELECT table_name, partitionBy, maxUncommittedRows, o3MaxLag
    FROM tables()
    ORDER BY table_name
    """
    result = await questdb_client._execute_sql_http(sql)
    return result

@mcp.tool
async def describe_table(
    table_name: str
) -> Dict[str, Any]:
    """
    Get detailed information about a table structure.

    Args:
        table_name: Name of the table to describe

    Returns:
        Table column information and metadata
    """
    sql = f"""
    SELECT column, type, indexed, indexBlockCapacity, symbolCached, symbolCapacity
    FROM table_columns('{table_name}')
    ORDER BY column
    """
    result = await questdb_client._execute_sql_http(sql)
    return result

@mcp.tool
async def insert_data(
    table_name: str,
    data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Insert data into a QuestDB table.

    Args:
        table_name: Target table name
        data: List of dictionaries containing row data

    Returns:
        Success status or error information
    """
    if not data:
        return {"error": "No data provided"}

    # Get column names from first row
    columns = list(data[0].keys())
    columns_sql = ", ".join(columns)

    # Build VALUES clause
    values_list = []
    for row in data:
        values = []
        for col in columns:
            value = row.get(col)
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                escaped_value = value.replace("'", "''")
                values.append(f"'{escaped_value}'")
            else:
                values.append(str(value))
        values_list.append(f"({', '.join(values)})")

    values_sql = ", ".join(values_list)
    sql = f"INSERT INTO {table_name} ({columns_sql}) VALUES {values_sql}"

    result = questdb_client._execute_sql_pg(sql, fetch=False)
    return result

@mcp.tool
async def import_csv(
    table_name: str,
    csv_data: str,
    create_table: bool = True
) -> Dict[str, Any]:
    """
    Import CSV data into QuestDB.

    Args:
        table_name: Target table name
        csv_data: CSV data as string
        create_table: Whether to auto-create table if it doesn't exist

    Returns:
        Import status or error information
    """
    result = await questdb_client._import_csv_http(table_name, csv_data)
    return result

@mcp.tool
async def get_table_stats(
    table_name: str
) -> Dict[str, Any]:
    """
    Get statistics about a table.

    Args:
        table_name: Name of the table

    Returns:
        Table statistics including row count, size, etc.
    """
    sql = f"""
    SELECT
        COUNT(*) as row_count,
        MIN(timestamp) as min_timestamp,
        MAX(timestamp) as max_timestamp
    FROM {table_name}
    """
    result = await questdb_client._execute_sql_http(sql)
    return result

@mcp.tool
async def sample_data(
    table_name: str,
    limit: int = 10,
    where_clause: str = None
) -> Dict[str, Any]:
    """
    Get a sample of data from a table.

    Args:
        table_name: Name of the table
        limit: Maximum number of rows to return
        where_clause: Optional WHERE clause (without WHERE keyword)

    Returns:
        Sample data from the table
    """
    sql = f"SELECT * FROM {table_name}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    sql += f" LIMIT {limit}"

    result = await questdb_client._execute_sql_http(sql)
    return result

@mcp.tool
async def time_series_query(
    table_name: str,
    time_column: str = "timestamp",
    start_time: str = None,
    end_time: str = None,
    interval: str = "1h",
    aggregations: List[str] = None
) -> Dict[str, Any]:
    """
    Execute a time-series aggregation query.

    Args:
        table_name: Name of the table
        time_column: Name of the timestamp column
        start_time: Start time (ISO format or relative like '1d')
        end_time: End time (ISO format or relative like 'now')
        interval: Aggregation interval (1m, 5m, 1h, 1d, etc.)
        aggregations: List of aggregation functions to apply

    Returns:
        Time-series aggregated data
    """
    # Default aggregations
    if not aggregations:
        aggregations = ["count(*) as count"]

    agg_clause = ", ".join(aggregations)

    sql = f"""
    SELECT sample_by({interval}, {time_column}) as time_bucket, {agg_clause}
    FROM {table_name}
    """

    where_conditions = []
    if start_time:
        where_conditions.append(f"{time_column} >= '{start_time}'")
    if end_time:
        where_conditions.append(f"{time_column} <= '{end_time}'")

    if where_conditions:
        sql += " WHERE " + " AND ".join(where_conditions)

    sql += f" SAMPLE BY {interval}"

    result = await questdb_client._execute_sql_http(sql)
    return result

@mcp.tool
async def latest_by_symbol(
    table_name: str,
    symbol_column: str = "symbol",
    symbols: List[str] = None,
    columns: List[str] = None
) -> Dict[str, Any]:
    """
    Get the latest records by symbol using QuestDB's LATEST BY feature.

    Args:
        table_name: Name of the table
        symbol_column: Name of the symbol/grouping column
        symbols: Optional list of specific symbols to filter
        columns: Optional list of columns to select

    Returns:
        Latest records for each symbol
    """
    if columns:
        select_clause = ", ".join(columns)
    else:
        select_clause = "*"

    sql = f"SELECT {select_clause} FROM {table_name}"

    if symbols:
        symbol_list = "', '".join(symbols)
        sql += f" WHERE {symbol_column} IN ('{symbol_list}')"

    sql += f" LATEST BY {symbol_column}"

    result = await questdb_client._execute_sql_http(sql)
    return result

@mcp.tool
async def create_index(
    table_name: str,
    column_name: str,
    index_type: str = "symbol"
) -> Dict[str, Any]:
    """
    Create an index on a table column.

    Args:
        table_name: Name of the table
        column_name: Name of the column to index
        index_type: Type of index ('symbol' for string columns)

    Returns:
        Success status or error information
    """
    sql = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} ADD INDEX"
    result = questdb_client._execute_sql_pg(sql, fetch=False)
    return result

@mcp.tool
async def query_to_dataframe(
    sql: str,
    method: str = "http"
) -> Dict[str, Any]:
    """
    Execute a query and return results as pandas DataFrame JSON.

    Args:
        sql: SQL query to execute
        method: Connection method ('http' or 'pg')

    Returns:
        Query results formatted as DataFrame JSON with shape info
    """
    logger.info(f"Executing query to DataFrame via {method}: {sql[:100]}...")

    if method == "http":
        result = await questdb_client._execute_sql_http(sql)

        if "error" in result:
            return result

        # Convert to DataFrame
        if "dataset" in result and result["dataset"]:
            columns = [col["name"] for col in result["columns"]]
            df = pd.DataFrame(result["dataset"], columns=columns)

            return {
                "data": df.to_dict('records'),
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "summary": df.describe().to_dict() if len(df) > 0 else {}
            }
        else:
            return {"data": [], "shape": (0, 0), "columns": [], "dtypes": {}, "summary": {}}
    else:
        result = questdb_client._execute_sql_pg(sql)

        if "error" in result:
            return result

        if "data" in result and result["data"]:
            df = pd.DataFrame(result["data"])

            return {
                "data": df.to_dict('records'),
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "summary": df.describe().to_dict() if len(df) > 0 else {}
            }
        else:
            return {"data": [], "shape": (0, 0), "columns": [], "dtypes": {}, "summary": {}}

async def cleanup():
    """Cleanup resources on shutdown"""
    if questdb_client.session:
        await questdb_client.session.aclose()

if __name__ == "__main__":
    logger.info("Starting QuestDB MCP server")
    try:
        logger.info("Calling mcp.run()")
        mcp.run()
        logger.info("QuestDB MCP server started successfully")
    except Exception as e:
        logger.error(f"QuestDB MCP server failed to start: {e}", exc_info=True)
        raise
    finally:
        logger.info("Running cleanup")
        asyncio.run(cleanup())
        logger.info("Cleanup completed")