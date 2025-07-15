"""
Dynamic table provisioning service for Sovera.
Handles creation of custom tables in project-specific PostgreSQL databases.
"""

import os
import logging
import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.table_schema import TableSchemaCreate, ColumnSchema, ColumnType

logger = logging.getLogger(__name__)

class TableProvisioningError(Exception):
    """Custom exception for table provisioning errors"""
    pass

class TableProvisioningService:
    """Service for managing dynamic table creation in project databases"""
    
    def __init__(self):
        self.pg_host = os.getenv("POSTGRES_SERVER", "db")
        self.pg_user = os.getenv("POSTGRES_USER", "postgres")
        self.pg_password = os.getenv("POSTGRES_PASSWORD")
    
    def get_project_db_url(self, db_name: str) -> str:
        """Generate database URL for a specific project"""
        return f"postgresql://{self.pg_user}:{self.pg_password}@{self.pg_host}/{db_name}"
    
    def build_column_definition(self, column: ColumnSchema) -> str:
        """Build SQL column definition from schema"""
        parts = [f'"{column.name}"']
        
        # Add column type with optional length
        if column.type in [ColumnType.VARCHAR, ColumnType.CHAR] and column.length:
            parts.append(f"{column.type.value}({column.length})")
        else:
            parts.append(column.type.value)
        
        # Add constraints
        if not column.nullable:
            parts.append("NOT NULL")
        
        if column.unique and not column.primary_key:
            parts.append("UNIQUE")
        
        if column.primary_key:
            if column.type == ColumnType.INTEGER:
                # Use SERIAL for auto-incrementing integer primary keys
                parts[1] = "SERIAL"
            parts.append("PRIMARY KEY")
        
        if column.default is not None:
            parts.append(f"DEFAULT {column.default}")
        
        return " ".join(parts)
    
    def build_create_table_sql(self, schema: TableSchemaCreate) -> str:
        """Build CREATE TABLE SQL statement"""
        column_definitions = [
            self.build_column_definition(col) for col in schema.columns
        ]
        
        sql = f'''
        CREATE TABLE "{schema.table_name}" (
            {",".join(column_definitions)}
        );
        '''
        
        # Add indexes for performance
        indexes = []
        for col in schema.columns:
            if col.unique and not col.primary_key:
                indexes.append(f'CREATE UNIQUE INDEX "idx_{schema.table_name}_{col.name}" ON "{schema.table_name}" ("{col.name}");')
        
        if indexes:
            sql += "\n" + "\n".join(indexes)
        
        return sql
    
    async def check_table_exists(self, db_url: str, table_name: str) -> bool:
        """Check if table already exists in the database"""
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
            raise TableProvisioningError(f"Failed to check table existence: {e}")
    
    async def provision_table(self, db_name: str, schema: TableSchemaCreate) -> Dict[str, Any]:
        """
        Create a new table in the specified project database.
        
        Args:
            db_name: Name of the project database
            schema: Table schema definition
            
        Returns:
            Dictionary with creation details
            
        Raises:
            TableProvisioningError: If table creation fails
        """
        db_url = self.get_project_db_url(db_name)
        
        try:
            # Check if table already exists
            if await self.check_table_exists(db_url, schema.table_name):
                raise TableProvisioningError(f"Table '{schema.table_name}' already exists")
            
            # Build SQL
            create_sql = self.build_create_table_sql(schema)
            logger.info(f"Creating table '{schema.table_name}' in database '{db_name}'")
            logger.debug(f"SQL: {create_sql}")
            
            # Execute table creation
            conn = await asyncpg.connect(db_url)
            try:
                await conn.execute(create_sql)
                
                # Verify table was created successfully
                table_exists = await self.check_table_exists(db_url, schema.table_name)
                if not table_exists:
                    raise TableProvisioningError("Table creation verification failed")
                
                logger.info(f"Successfully created table '{schema.table_name}' in database '{db_name}'")
                
                return {
                    "table_name": schema.table_name,
                    "database": db_name,
                    "columns": len(schema.columns),
                    "created_at": datetime.utcnow().isoformat(),
                    "sql": create_sql
                }
                
            finally:
                await conn.close()
                
        except TableProvisioningError:
            raise
        except Exception as e:
            logger.error(f"Failed to create table '{schema.table_name}' in database '{db_name}': {e}")
            raise TableProvisioningError(f"Table creation failed: {e}")
    
    async def list_tables(self, db_name: str) -> List[Dict[str, Any]]:
        """
        List all user-created tables in the project database.
        
        Args:
            db_name: Name of the project database
            
        Returns:
            List of table information
        """
        db_url = self.get_project_db_url(db_name)
        
        try:
            conn = await asyncpg.connect(db_url)
            try:
                tables = await conn.fetch("""
                    SELECT 
                        t.table_name,
                        COUNT(c.column_name) as column_count,
                        obj_description(pgc.oid, 'pg_class') as comment
                    FROM information_schema.tables t
                    LEFT JOIN information_schema.columns c 
                        ON t.table_name = c.table_name 
                        AND t.table_schema = c.table_schema
                    LEFT JOIN pg_class pgc ON pgc.relname = t.table_name
                    WHERE t.table_schema = 'public'
                        AND t.table_type = 'BASE TABLE'
                        AND t.table_name NOT IN ('items', 'project_metadata', 'files')
                    GROUP BY t.table_name, pgc.oid
                    ORDER BY t.table_name;
                """)
                
                result = []
                for table in tables:
                    # Get row count
                    try:
                        row_count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table["table_name"]}"')
                    except:
                        row_count = None
                    
                    result.append({
                        "table_name": table["table_name"],
                        "column_count": table["column_count"],
                        "row_count": row_count,
                        "comment": table["comment"]
                    })
                
                return result
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Failed to list tables in database '{db_name}': {e}")
            raise TableProvisioningError(f"Failed to list tables: {e}")
    
    async def get_table_schema(self, db_name: str, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed schema information for a specific table.
        
        Args:
            db_name: Name of the project database
            table_name: Name of the table
            
        Returns:
            Table schema information or None if table doesn't exist
        """
        db_url = self.get_project_db_url(db_name)
        
        try:
            conn = await asyncpg.connect(db_url)
            try:
                # Check if table exists
                table_exists = await self.check_table_exists(db_url, table_name)
                if not table_exists:
                    return None
                
                # Get column information
                columns = await conn.fetch("""
                    SELECT 
                        c.column_name,
                        c.data_type,
                        c.is_nullable,
                        c.column_default,
                        c.character_maximum_length,
                        tc.constraint_type
                    FROM information_schema.columns c
                    LEFT JOIN information_schema.key_column_usage kcu 
                        ON c.table_name = kcu.table_name 
                        AND c.column_name = kcu.column_name
                        AND c.table_schema = kcu.table_schema
                    LEFT JOIN information_schema.table_constraints tc 
                        ON kcu.constraint_name = tc.constraint_name
                        AND kcu.table_schema = tc.table_schema
                    WHERE c.table_schema = 'public' 
                        AND c.table_name = $1
                    ORDER BY c.ordinal_position;
                """, table_name)
                
                return {
                    "table_name": table_name,
                    "columns": [dict(col) for col in columns]
                }
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Failed to get schema for table '{table_name}' in database '{db_name}': {e}")
            raise TableProvisioningError(f"Failed to get table schema: {e}")
    
    async def drop_table(self, db_name: str, table_name: str) -> bool:
        """
        Drop a table from the project database.
        
        Args:
            db_name: Name of the project database
            table_name: Name of the table to drop
            
        Returns:
            True if successful
            
        Raises:
            TableProvisioningError: If table drop fails
        """
        db_url = self.get_project_db_url(db_name)
        
        try:
            # Check if table exists
            if not await self.check_table_exists(db_url, table_name):
                raise TableProvisioningError(f"Table '{table_name}' does not exist")
            
            # Prevent dropping system tables
            system_tables = ['items', 'project_metadata', 'files']
            if table_name in system_tables:
                raise TableProvisioningError(f"Cannot drop system table '{table_name}'")
            
            conn = await asyncpg.connect(db_url)
            try:
                await conn.execute(f'DROP TABLE "{table_name}" CASCADE;')
                logger.info(f"Successfully dropped table '{table_name}' from database '{db_name}'")
                return True
                
            finally:
                await conn.close()
                
        except TableProvisioningError:
            raise
        except Exception as e:
            logger.error(f"Failed to drop table '{table_name}' from database '{db_name}': {e}")
            raise TableProvisioningError(f"Table drop failed: {e}")

# Global table provisioning service instance
table_provisioning_service = TableProvisioningService()