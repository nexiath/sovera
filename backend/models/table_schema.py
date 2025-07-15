"""
Dynamic table schema models for Sovera.
Allows users to create custom tables in their project databases.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from enum import Enum
import re

class ColumnType(str, Enum):
    """Supported PostgreSQL column types"""
    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    SMALLINT = "SMALLINT"
    DECIMAL = "DECIMAL"
    NUMERIC = "NUMERIC"
    REAL = "REAL"
    DOUBLE_PRECISION = "DOUBLE PRECISION"
    
    # Text types
    TEXT = "TEXT"
    VARCHAR = "VARCHAR"
    CHAR = "CHAR"
    
    # Date/Time types
    TIMESTAMP = "TIMESTAMP"
    TIMESTAMPTZ = "TIMESTAMPTZ"
    DATE = "DATE"
    TIME = "TIME"
    
    # Boolean
    BOOLEAN = "BOOLEAN"
    
    # JSON
    JSON = "JSON"
    JSONB = "JSONB"
    
    # UUID
    UUID = "UUID"

class ColumnSchema(BaseModel):
    """Schema definition for a single column"""
    name: str = Field(..., min_length=1, max_length=63, description="Column name")
    type: ColumnType = Field(..., description="PostgreSQL column type")
    nullable: bool = Field(default=True, description="Whether column can be NULL")
    primary_key: bool = Field(default=False, description="Whether column is primary key")
    unique: bool = Field(default=False, description="Whether column has unique constraint")
    default: Optional[str] = Field(default=None, description="Default value expression")
    length: Optional[int] = Field(default=None, description="Length for VARCHAR/CHAR types")
    
    @validator('name')
    def validate_column_name(cls, v):
        """Validate column name follows PostgreSQL naming rules"""
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Column name must start with letter or underscore, contain only letters, numbers, and underscores')
        
        # Reserved keywords check
        reserved_keywords = {
            'select', 'from', 'where', 'insert', 'update', 'delete', 'create', 
            'drop', 'alter', 'table', 'index', 'primary', 'key', 'foreign',
            'references', 'constraint', 'user', 'order', 'group', 'having',
            'union', 'join', 'inner', 'outer', 'left', 'right', 'on', 'as'
        }
        if v.lower() in reserved_keywords:
            raise ValueError(f'Column name "{v}" is a reserved PostgreSQL keyword')
        
        return v.lower()  # Normalize to lowercase
    
    @validator('length')
    def validate_length(cls, v, values):
        """Validate length parameter for applicable types"""
        if v is not None:
            column_type = values.get('type')
            if column_type not in [ColumnType.VARCHAR, ColumnType.CHAR]:
                raise ValueError(f'Length parameter not applicable for type {column_type}')
            if v <= 0 or v > 10485760:  # 10MB limit
                raise ValueError('Length must be between 1 and 10485760')
        return v

class TableSchemaCreate(BaseModel):
    """Schema for creating a new table"""
    table_name: str = Field(..., min_length=1, max_length=63, description="Table name")
    columns: List[ColumnSchema] = Field(..., min_items=1, max_items=1000, description="Column definitions")
    
    @validator('table_name')
    def validate_table_name(cls, v):
        """Validate table name follows PostgreSQL naming rules"""
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Table name must start with letter or underscore, contain only letters, numbers, and underscores')
        
        # Reserved table names
        reserved_names = {
            'user', 'users', 'project', 'projects', 'schema', 'information_schema',
            'pg_catalog', 'pg_tables', 'pg_indexes', 'pg_views', 'pg_sequences'
        }
        if v.lower() in reserved_names:
            raise ValueError(f'Table name "{v}" is reserved')
        
        return v.lower()  # Normalize to lowercase
    
    @validator('columns')
    def validate_columns(cls, v):
        """Validate column definitions"""
        if not v:
            raise ValueError('At least one column is required')
        
        # Check for duplicate column names
        names = [col.name.lower() for col in v]
        if len(names) != len(set(names)):
            raise ValueError('Duplicate column names are not allowed')
        
        # Check primary key constraints
        primary_keys = [col for col in v if col.primary_key]
        if len(primary_keys) > 1:
            raise ValueError('Only one primary key column is allowed')
        
        # If no primary key specified, we'll add an auto-increment ID
        if not primary_keys:
            # Add default ID column
            id_column = ColumnSchema(
                name="id",
                type=ColumnType.INTEGER,
                nullable=False,
                primary_key=True
            )
            v.insert(0, id_column)
        
        return v

class TableSchemaResponse(BaseModel):
    """Response model for table creation"""
    table_name: str
    columns: List[ColumnSchema]
    created_at: str
    project_id: int
    
class TableInfo(BaseModel):
    """Information about an existing table"""
    table_name: str
    column_count: int
    row_count: Optional[int] = None
    created_at: Optional[str] = None
    size_mb: Optional[float] = None