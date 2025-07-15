"""
Dynamic table rows router for Sovera.
Allows users to insert and read data from their custom tables.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlmodel import Session
import asyncpg
import json
import logging
from datetime import datetime

from auth.dependencies import get_current_user
from database.session import get_session
from models.user import User
from models.project import Project
from utils.websocket_manager import notify_table_change

logger = logging.getLogger(__name__)
router = APIRouter()

class TableRowsError(Exception):
    """Custom exception for table rows operations"""
    pass

async def get_project_and_verify_access(
    project_id: int,
    current_user: User,
    session: Session
) -> Project:
    """Get project and verify user has access to it"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: You don't own this project")
    if project.provisioning_status != "completed":
        raise HTTPException(
            status_code=400, 
            detail="Project infrastructure not ready. Please wait for provisioning to complete."
        )
    return project

def get_project_db_url(project: Project) -> str:
    """Generate database URL for a specific project"""
    import os
    pg_host = os.getenv("POSTGRES_SERVER", "db")
    pg_user = os.getenv("POSTGRES_USER", "postgres")
    pg_password = os.getenv("POSTGRES_PASSWORD")
    return f"postgresql://{pg_user}:{pg_password}@{pg_host}/{project.db_name}"

async def check_table_exists(db_url: str, table_name: str) -> bool:
    """Check if table exists in the database"""
    try:
        conn = await asyncpg.connect(db_url)
        try:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                );
            """, table_name)
            return result
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Error checking table existence: {e}")
        raise TableRowsError(f"Failed to check table existence: {e}")

async def get_table_columns(db_url: str, table_name: str) -> List[Dict[str, Any]]:
    """
    Get column information for a table using introspection.
    
    Args:
        db_url: Database connection URL
        table_name: Name of the table
        
    Returns:
        List of column definitions with name, type, nullable, default, etc.
        
    Raises:
        TableRowsError: If table doesn't exist or introspection fails
    """
    try:
        conn = await asyncpg.connect(db_url)
        try:
            # Check if table exists first
            if not await check_table_exists(db_url, table_name):
                raise TableRowsError(f"Table '{table_name}' does not exist")
            
            # Get detailed column information
            columns = await conn.fetch("""
                SELECT 
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale,
                    c.ordinal_position,
                    CASE WHEN kcu.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
                    CASE WHEN tc.constraint_type = 'UNIQUE' THEN true ELSE false END as is_unique
                FROM information_schema.columns c
                LEFT JOIN information_schema.key_column_usage kcu 
                    ON c.table_name = kcu.table_name 
                    AND c.column_name = kcu.column_name
                    AND c.table_schema = kcu.table_schema
                LEFT JOIN information_schema.table_constraints tc 
                    ON kcu.constraint_name = tc.constraint_name
                    AND kcu.table_schema = tc.table_schema
                    AND tc.constraint_type IN ('PRIMARY KEY', 'UNIQUE')
                WHERE c.table_schema = 'public' 
                    AND c.table_name = $1
                ORDER BY c.ordinal_position;
            """, table_name)
            
            if not columns:
                raise TableRowsError(f"No columns found for table '{table_name}'")
            
            # Convert to dict format
            result = []
            for col in columns:
                result.append({
                    "name": col["column_name"],
                    "type": col["data_type"],
                    "nullable": col["is_nullable"] == "YES",
                    "default": col["column_default"],
                    "max_length": col["character_maximum_length"],
                    "precision": col["numeric_precision"],
                    "scale": col["numeric_scale"],
                    "position": col["ordinal_position"],
                    "is_primary_key": col["is_primary_key"],
                    "is_unique": col["is_unique"]
                })
            
            return result
            
        finally:
            await conn.close()
            
    except TableRowsError:
        raise
    except Exception as e:
        logger.error(f"Failed to get columns for table '{table_name}': {e}")
        raise TableRowsError(f"Failed to introspect table: {e}")

def convert_python_to_postgres_value(value: Any, pg_type: str) -> Any:
    """Convert Python value to PostgreSQL-compatible value"""
    if value is None:
        return None
    
    # Handle different PostgreSQL types
    if pg_type in ["integer", "bigint", "smallint"]:
        return int(value)
    elif pg_type in ["real", "double precision", "numeric", "decimal"]:
        return float(value)
    elif pg_type == "boolean":
        if isinstance(value, bool):
            return value
        return str(value).lower() in ["true", "1", "yes", "on"]
    elif pg_type in ["json", "jsonb"]:
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)
    elif pg_type in ["timestamp", "timestamptz", "date", "time"]:
        if isinstance(value, str):
            return value  # Let PostgreSQL handle the parsing
        return str(value)
    else:
        # Default to string for text types
        return str(value)

async def insert_dynamic_row(db_url: str, table_name: str, payload_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Insert a row into a table using dynamic column introspection.
    
    Args:
        db_url: Database connection URL
        table_name: Name of the table
        payload_dict: Dictionary of column->value mappings
        
    Returns:
        Dictionary with inserted row data including generated ID
        
    Raises:
        TableRowsError: If insertion fails
    """
    try:
        # Get table columns for validation
        columns = await get_table_columns(db_url, table_name)
        column_map = {col["name"]: col for col in columns}
        
        # Validate payload columns exist in table
        for col_name in payload_dict.keys():
            if col_name not in column_map:
                raise TableRowsError(f"Column '{col_name}' does not exist in table '{table_name}'")
        
        # Check required columns (non-nullable without default)
        required_columns = [
            col["name"] for col in columns 
            if not col["nullable"] and col["default"] is None and not col["is_primary_key"]
        ]
        
        missing_columns = set(required_columns) - set(payload_dict.keys())
        if missing_columns:
            raise TableRowsError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Prepare data for insertion
        insert_columns = []
        insert_values = []
        placeholders = []
        
        for i, (col_name, value) in enumerate(payload_dict.items(), 1):
            column_info = column_map[col_name]
            
            # Skip auto-increment primary keys
            if column_info["is_primary_key"] and "nextval" in str(column_info["default"]):
                continue
            
            insert_columns.append(f'"{col_name}"')
            converted_value = convert_python_to_postgres_value(value, column_info["type"])
            insert_values.append(converted_value)
            placeholders.append(f"${i}")
        
        if not insert_columns:
            raise TableRowsError("No valid columns to insert")
        
        # Build INSERT query
        columns_str = ", ".join(insert_columns)
        placeholders_str = ", ".join(placeholders)
        
        insert_query = f"""
            INSERT INTO "{table_name}" ({columns_str})
            VALUES ({placeholders_str})
            RETURNING *;
        """
        
        # Execute insertion
        conn = await asyncpg.connect(db_url)
        try:
            logger.info(f"Inserting row into table '{table_name}' with columns: {insert_columns}")
            
            result = await conn.fetchrow(insert_query, *insert_values)
            
            if not result:
                raise TableRowsError("Insert operation failed - no data returned")
            
            # Convert result to dictionary
            row_data = dict(result)
            
            # Convert any datetime objects to ISO strings
            for key, value in row_data.items():
                if isinstance(value, datetime):
                    row_data[key] = value.isoformat()
            
            logger.info(f"Successfully inserted row into table '{table_name}'")
            return row_data
            
        finally:
            await conn.close()
            
    except TableRowsError:
        raise
    except Exception as e:
        logger.error(f"Failed to insert row into table '{table_name}': {e}")
        raise TableRowsError(f"Insert operation failed: {e}")

async def get_table_rows(db_url: str, table_name: str, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get all rows from a table.
    
    Args:
        db_url: Database connection URL
        table_name: Name of the table
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        
    Returns:
        List of row dictionaries
        
    Raises:
        TableRowsError: If query fails
    """
    try:
        # Check if table exists
        if not await check_table_exists(db_url, table_name):
            raise TableRowsError(f"Table '{table_name}' does not exist")
        
        # Build SELECT query
        query = f'SELECT * FROM "{table_name}" ORDER BY id'
        
        if limit is not None:
            query += f" LIMIT {limit}"
        if offset is not None:
            query += f" OFFSET {offset}"
        
        # Execute query
        conn = await asyncpg.connect(db_url)
        try:
            rows = await conn.fetch(query)
            
            # Convert to list of dictionaries
            result = []
            for row in rows:
                row_data = dict(row)
                
                # Convert datetime objects to ISO strings
                for key, value in row_data.items():
                    if isinstance(value, datetime):
                        row_data[key] = value.isoformat()
                
                result.append(row_data)
            
            return result
            
        finally:
            await conn.close()
            
    except TableRowsError:
        raise
    except Exception as e:
        logger.error(f"Failed to get rows from table '{table_name}': {e}")
        raise TableRowsError(f"Failed to retrieve rows: {e}")

@router.post("/projects/{project_id}/tables/{table_name}/rows", response_model=Dict[str, Any])
async def insert_table_row(
    project_id: int = Path(..., description="Project ID", gt=0),
    table_name: str = Path(..., description="Table name", min_length=1, max_length=63),
    payload: Dict[str, Any] = ...,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Insert a new row into a custom table.
    
    This endpoint allows users to insert data into their custom tables
    using dynamic column introspection. The payload should contain
    column names as keys and their values.
    
    **Example payload:**
    ```json
    {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "active": true
    }
    ```
    
    **Features:**
    - Dynamic column validation
    - Type conversion and validation
    - Required column checking
    - Automatic ID generation for primary keys
    - JSON/JSONB support
    
    **Security:**
    - Only project owners can insert data
    - SQL injection prevention through parameterized queries
    - Column existence validation
    """
    # Verify project access
    project = await get_project_and_verify_access(project_id, current_user, session)
    
    try:
        logger.info(f"Inserting row into table '{table_name}' in project {project_id} for user {current_user.id}")
        
        # Get database URL
        db_url = get_project_db_url(project)
        
        # Insert the row
        result = await insert_dynamic_row(db_url, table_name, payload)
        
        # Add context to response
        response = {
            "data": result,
            "table_name": table_name,
            "project_id": project_id,
            "inserted_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully inserted row into table '{table_name}' in project {project_id}")
        
        # Notify WebSocket clients about the new row
        try:
            await notify_table_change(project_id, table_name, "INSERT", result)
        except Exception as e:
            logger.warning(f"Failed to notify WebSocket clients: {e}")
        
        return response
        
    except TableRowsError as e:
        logger.warning(f"Row insertion failed for table '{table_name}' in project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error inserting row into table '{table_name}' in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during row insertion")

@router.get("/projects/{project_id}/tables/{table_name}/rows", response_model=List[Dict[str, Any]])
async def get_table_rows_endpoint(
    project_id: int = Path(..., description="Project ID", gt=0),
    table_name: str = Path(..., description="Table name", min_length=1, max_length=63),
    limit: Optional[int] = Query(None, description="Maximum number of rows to return", ge=1, le=1000),
    offset: Optional[int] = Query(None, description="Number of rows to skip", ge=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get all rows from a custom table.
    
    This endpoint retrieves data from custom tables using dynamic queries.
    Supports basic pagination through limit and offset parameters.
    
    **Parameters:**
    - `limit`: Maximum number of rows to return (default: all)
    - `offset`: Number of rows to skip (default: 0)
    
    **Response:**
    Returns an array of objects where each object represents a row
    with column names as keys and their values.
    
    **Example response:**
    ```json
    [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "active": true,
            "created_at": "2024-07-14T12:00:00"
        }
    ]
    ```
    
    **Security:**
    - Only project owners can read data
    - Table existence validation
    - Safe query construction
    """
    # Verify project access
    project = await get_project_and_verify_access(project_id, current_user, session)
    
    try:
        logger.info(f"Getting rows from table '{table_name}' in project {project_id} for user {current_user.id}")
        
        # Get database URL
        db_url = get_project_db_url(project)
        
        # Get the rows
        rows = await get_table_rows(db_url, table_name, limit, offset)
        
        logger.info(f"Successfully retrieved {len(rows)} rows from table '{table_name}' in project {project_id}")
        return rows
        
    except TableRowsError as e:
        logger.warning(f"Failed to get rows from table '{table_name}' in project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting rows from table '{table_name}' in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving rows")