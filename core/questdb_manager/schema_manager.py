"""
QuestDB Schema Manager

Handles table schema definitions, validation, and SQL generation
for consistent data structure across all feeds.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum


class ColumnType(Enum):
    """QuestDB column types"""
    TIMESTAMP = "TIMESTAMP"
    SYMBOL = "SYMBOL"
    STRING = "STRING"
    DOUBLE = "DOUBLE"
    FLOAT = "FLOAT"
    LONG = "LONG"
    INT = "INT"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    BINARY = "BINARY"


@dataclass
class ColumnDefinition:
    """Definition of a table column"""
    name: str
    type: ColumnType
    nullable: bool = True
    symbol_capacity: Optional[int] = None
    symbol_cache: bool = False
    index: bool = False
    default_value: Optional[Any] = None
    description: str = ""

    def to_sql(self) -> str:
        """Convert column definition to SQL"""
        sql = f"{self.name} {self.type.value}"

        # Add symbol-specific options
        if self.type == ColumnType.SYMBOL:
            if self.symbol_capacity:
                sql += f" CAPACITY {self.symbol_capacity}"
            if self.symbol_cache:
                sql += " CACHE"

        # Add constraints
        if not self.nullable:
            sql += " NOT NULL"

        return sql

    def validate_value(self, value: Any) -> Any:
        """Validate and convert value to appropriate type"""
        if value is None:
            if not self.nullable:
                raise ValueError(f"Column '{self.name}' cannot be null")
            return None

        try:
            if self.type == ColumnType.TIMESTAMP:
                if isinstance(value, str):
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                elif isinstance(value, datetime):
                    return value
                else:
                    raise ValueError(f"Invalid timestamp format: {value}")

            elif self.type == ColumnType.DATE:
                if isinstance(value, str):
                    return datetime.strptime(value, '%Y-%m-%d').date()
                elif isinstance(value, date):
                    return value
                elif isinstance(value, datetime):
                    return value.date()
                else:
                    raise ValueError(f"Invalid date format: {value}")

            elif self.type in [ColumnType.DOUBLE, ColumnType.FLOAT]:
                return float(value)

            elif self.type in [ColumnType.LONG, ColumnType.INT]:
                return int(float(value))  # Handle string numbers

            elif self.type == ColumnType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                else:
                    return bool(value)

            elif self.type in [ColumnType.STRING, ColumnType.SYMBOL]:
                return str(value)

            else:
                return value

        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value for column '{self.name}' (type {self.type.value}): {value} - {e}")


@dataclass
class TableSchema:
    """Complete table schema definition"""
    table_name: str
    columns: List[ColumnDefinition] = field(default_factory=list)
    timestamp_column: str = "timestamp"
    partition_by: str = "DAY"
    wal_enabled: bool = True
    description: str = ""
    version: str = "1.0.0"

    def __post_init__(self):
        """Validate schema after initialization"""
        self._validate_schema()

    def _validate_schema(self):
        """Validate the schema definition"""
        if not self.table_name:
            raise ValueError("Table name is required")

        if not self.columns:
            raise ValueError("At least one column is required")

        # Check for timestamp column
        timestamp_col = next((col for col in self.columns if col.name == self.timestamp_column), None)
        if not timestamp_col:
            raise ValueError(f"Timestamp column '{self.timestamp_column}' not found in columns")

        if timestamp_col.type != ColumnType.TIMESTAMP:
            raise ValueError(f"Timestamp column '{self.timestamp_column}' must be of type TIMESTAMP")

        # Check for duplicate column names
        column_names = [col.name for col in self.columns]
        if len(column_names) != len(set(column_names)):
            raise ValueError("Duplicate column names found")

    def add_column(self, column: ColumnDefinition):
        """Add a column to the schema"""
        if any(col.name == column.name for col in self.columns):
            raise ValueError(f"Column '{column.name}' already exists")
        self.columns.append(column)

    def get_column(self, name: str) -> Optional[ColumnDefinition]:
        """Get column definition by name"""
        return next((col for col in self.columns if col.name == name), None)

    def to_create_sql(self) -> str:
        """Generate CREATE TABLE SQL statement"""
        column_definitions = [col.to_sql() for col in self.columns]
        columns_sql = ",\n    ".join(column_definitions)

        sql = f"""
CREATE TABLE IF NOT EXISTS {self.table_name} (
    {columns_sql}
) TIMESTAMP({self.timestamp_column}) PARTITION BY {self.partition_by}"""

        if self.wal_enabled:
            sql += " WAL"

        sql += ";"

        return sql

    def to_insert_sql(self) -> str:
        """Generate INSERT SQL statement"""
        column_names = [col.name for col in self.columns]
        placeholders = ", ".join(["%s"] * len(column_names))

        return f"""
INSERT INTO {self.table_name} (
    {', '.join(column_names)}
) VALUES %s
"""

    def validate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a record against the schema"""
        validated = {}

        for column in self.columns:
            value = record.get(column.name)

            # Use default value if provided and value is missing
            if value is None and column.default_value is not None:
                value = column.default_value

            validated[column.name] = column.validate_value(value)

        return validated

    def record_to_values(self, record: Dict[str, Any]) -> tuple:
        """Convert validated record to tuple for SQL insertion"""
        return tuple(record.get(col.name) for col in self.columns)

    def to_dict(self) -> Dict[str, Any]:
        """Convert schema to dictionary for serialization"""
        return {
            'table_name': self.table_name,
            'columns': [
                {
                    'name': col.name,
                    'type': col.type.value,
                    'nullable': col.nullable,
                    'symbol_capacity': col.symbol_capacity,
                    'symbol_cache': col.symbol_cache,
                    'index': col.index,
                    'default_value': col.default_value,
                    'description': col.description
                }
                for col in self.columns
            ],
            'timestamp_column': self.timestamp_column,
            'partition_by': self.partition_by,
            'wal_enabled': self.wal_enabled,
            'description': self.description,
            'version': self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableSchema':
        """Create schema from dictionary"""
        columns = []
        for col_data in data['columns']:
            column = ColumnDefinition(
                name=col_data['name'],
                type=ColumnType(col_data['type']),
                nullable=col_data.get('nullable', True),
                symbol_capacity=col_data.get('symbol_capacity'),
                symbol_cache=col_data.get('symbol_cache', False),
                index=col_data.get('index', False),
                default_value=col_data.get('default_value'),
                description=col_data.get('description', '')
            )
            columns.append(column)

        return cls(
            table_name=data['table_name'],
            columns=columns,
            timestamp_column=data.get('timestamp_column', 'timestamp'),
            partition_by=data.get('partition_by', 'DAY'),
            wal_enabled=data.get('wal_enabled', True),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0')
        )


class SchemaManager:
    """Manages table schemas for the entire system"""

    def __init__(self):
        self.schemas: Dict[str, TableSchema] = {}
        self.logger = logging.getLogger('schema_manager')

    def register_schema(self, schema: TableSchema):
        """Register a table schema"""
        self.schemas[schema.table_name] = schema
        self.logger.info(f"Registered schema for table '{schema.table_name}'")

    def get_schema(self, table_name: str) -> Optional[TableSchema]:
        """Get schema for a table"""
        return self.schemas.get(table_name)

    def list_schemas(self) -> List[str]:
        """List all registered schema names"""
        return list(self.schemas.keys())

    def validate_record_for_table(self, table_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a record against a table's schema"""
        schema = self.get_schema(table_name)
        if not schema:
            raise ValueError(f"No schema found for table '{table_name}'")
        return schema.validate_record(record)

    async def load_existing_schemas(self, questdb_manager):
        """Load schemas for existing tables from QuestDB"""
        try:
            self.logger.info("Loading existing table schemas from QuestDB")

            # Query to get table information
            result = await questdb_manager.execute_query("""
                SELECT table_name, column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)

            if result['success']:
                tables = {}
                for row in result['results']:
                    table_name, column_name, data_type, is_nullable = row

                    if table_name not in tables:
                        tables[table_name] = []

                    # Map QuestDB types to our ColumnType enum
                    column_type = self._map_questdb_type(data_type)

                    column = ColumnDefinition(
                        name=column_name,
                        type=column_type,
                        nullable=is_nullable == 'YES'
                    )

                    tables[table_name].append(column)

                # Create schemas for discovered tables
                for table_name, columns in tables.items():
                    # Find timestamp column (assume first TIMESTAMP column)
                    timestamp_col = next(
                        (col.name for col in columns if col.type == ColumnType.TIMESTAMP),
                        'timestamp'
                    )

                    schema = TableSchema(
                        table_name=table_name,
                        columns=columns,
                        timestamp_column=timestamp_col,
                        description=f"Auto-discovered schema for {table_name}"
                    )

                    self.register_schema(schema)

                self.logger.info(f"Loaded schemas for {len(tables)} existing tables")

        except Exception as e:
            self.logger.warning(f"Failed to load existing schemas: {e}")

    def _map_questdb_type(self, questdb_type: str) -> ColumnType:
        """Map QuestDB data type to our ColumnType enum"""
        type_mapping = {
            'timestamp': ColumnType.TIMESTAMP,
            'symbol': ColumnType.SYMBOL,
            'string': ColumnType.STRING,
            'double': ColumnType.DOUBLE,
            'float': ColumnType.FLOAT,
            'long': ColumnType.LONG,
            'int': ColumnType.INT,
            'boolean': ColumnType.BOOLEAN,
            'date': ColumnType.DATE,
            'binary': ColumnType.BINARY
        }

        return type_mapping.get(questdb_type.lower(), ColumnType.STRING)

    def create_standard_telemetry_schema(self) -> TableSchema:
        """Create standard telemetry table schema"""
        columns = [
            ColumnDefinition("timestamp", ColumnType.TIMESTAMP, nullable=False),
            ColumnDefinition("feed_name", ColumnType.SYMBOL, symbol_capacity=100, symbol_cache=True),
            ColumnDefinition("execution_time_ms", ColumnType.DOUBLE),
            ColumnDefinition("records_processed", ColumnType.INT),
            ColumnDefinition("records_failed", ColumnType.INT),
            ColumnDefinition("success_rate", ColumnType.DOUBLE),
            ColumnDefinition("cpu_usage_percent", ColumnType.DOUBLE),
            ColumnDefinition("memory_usage_mb", ColumnType.DOUBLE),
            ColumnDefinition("memory_percent", ColumnType.DOUBLE),
            ColumnDefinition("error_count", ColumnType.INT),
            ColumnDefinition("last_error", ColumnType.STRING, nullable=True),
            ColumnDefinition("host_name", ColumnType.SYMBOL, symbol_capacity=50, symbol_cache=True),
            ColumnDefinition("process_id", ColumnType.INT)
        ]

        return TableSchema(
            table_name="telemetry_metrics",
            columns=columns,
            timestamp_column="timestamp",
            description="Standard telemetry metrics for all feeds"
        )

    def create_standard_health_schema(self) -> TableSchema:
        """Create standard health monitoring table schema"""
        columns = [
            ColumnDefinition("timestamp", ColumnType.TIMESTAMP, nullable=False),
            ColumnDefinition("feed_name", ColumnType.SYMBOL, symbol_capacity=100, symbol_cache=True),
            ColumnDefinition("status", ColumnType.SYMBOL, symbol_capacity=20, symbol_cache=True),
            ColumnDefinition("health_score", ColumnType.DOUBLE),
            ColumnDefinition("consecutive_failures", ColumnType.INT),
            ColumnDefinition("uptime_percent", ColumnType.DOUBLE),
            ColumnDefinition("last_successful_run", ColumnType.TIMESTAMP, nullable=True),
            ColumnDefinition("alerts_triggered", ColumnType.INT),
            ColumnDefinition("host_name", ColumnType.SYMBOL, symbol_capacity=50, symbol_cache=True)
        ]

        return TableSchema(
            table_name="health_status",
            columns=columns,
            timestamp_column="timestamp",
            description="Health monitoring status for all feeds"
        )

    def create_standard_alerts_schema(self) -> TableSchema:
        """Create standard alerts table schema"""
        columns = [
            ColumnDefinition("timestamp", ColumnType.TIMESTAMP, nullable=False),
            ColumnDefinition("feed_name", ColumnType.SYMBOL, symbol_capacity=100, symbol_cache=True),
            ColumnDefinition("alert_type", ColumnType.SYMBOL, symbol_capacity=50, symbol_cache=True),
            ColumnDefinition("severity", ColumnType.SYMBOL, symbol_capacity=20, symbol_cache=True),
            ColumnDefinition("message", ColumnType.STRING),
            ColumnDefinition("value", ColumnType.DOUBLE, nullable=True),
            ColumnDefinition("threshold", ColumnType.DOUBLE, nullable=True),
            ColumnDefinition("resolved", ColumnType.BOOLEAN, default_value=False),
            ColumnDefinition("resolved_at", ColumnType.TIMESTAMP, nullable=True),
            ColumnDefinition("host_name", ColumnType.SYMBOL, symbol_capacity=50, symbol_cache=True)
        ]

        return TableSchema(
            table_name="telemetry_alerts",
            columns=columns,
            timestamp_column="timestamp",
            description="Alert history and management"
        )