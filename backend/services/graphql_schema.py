"""
Dynamic GraphQL schema generator for Sovera.
Creates GraphQL schemas based on project table structures.
"""

import logging
from typing import Dict, List, Any, Optional, Type
import strawberry
from strawberry.types import Info
from dataclasses import dataclass
import asyncpg
import json
from datetime import datetime

from models.project import Project
from models.user import User
from utils.rbac import PermissionManager

logger = logging.getLogger(__name__)

class GraphQLSchemaError(Exception):
    """Custom exception for GraphQL schema generation errors"""
    pass

# Type mapping from PostgreSQL to GraphQL/Python types
PG_TO_GRAPHQL_TYPE_MAP = {
    'integer': int,
    'bigint': int,
    'smallint': int,
    'decimal': float,
    'numeric': float,
    'real': float,
    'double precision': float,
    'text': str,
    'varchar': str,
    'char': str,
    'timestamp': datetime,
    'timestamptz': datetime,
    'date': datetime,
    'time': str,
    'boolean': bool,
    'json': str,  # JSON as string for GraphQL
    'jsonb': str,
    'uuid': str,
}

class DynamicGraphQLSchema:
    """Generates dynamic GraphQL schemas for project tables"""
    
    def __init__(self, project: Project):
        self.project = project
        self.db_url = self._get_project_db_url()
        self._type_cache: Dict[str, Type] = {}
        self._tables_info: Dict[str, List[Dict]] = {}
    
    def _get_project_db_url(self) -> str:
        """Generate database URL for project"""
        import os
        pg_host = os.getenv("POSTGRES_SERVER", "localhost")
        pg_user = os.getenv("POSTGRES_USER", "postgres")
        pg_password = os.getenv("POSTGRES_PASSWORD")
        return f"postgresql://{pg_user}:{pg_password}@{pg_host}/{self.project.db_name}"
    
    async def introspect_tables(self) -> Dict[str, List[Dict]]:
        """Introspect all tables in the project database"""
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                # Get all user tables (excluding system tables)
                tables_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    AND table_name NOT IN ('items', 'project_metadata', 'files')
                    ORDER BY table_name;
                """
                
                tables = await conn.fetch(tables_query)
                tables_info = {}
                
                for table_row in tables:
                    table_name = table_row['table_name']
                    
                    # Get columns for this table
                    columns_query = """
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
                    """
                    
                    columns = await conn.fetch(columns_query, table_name)
                    tables_info[table_name] = [dict(col) for col in columns]
                
                self._tables_info = tables_info
                return tables_info
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Failed to introspect tables for project {self.project.id}: {e}")
            raise GraphQLSchemaError(f"Database introspection failed: {e}")
    
    def _create_strawberry_type(self, table_name: str, columns: List[Dict]) -> Type:
        """Create a Strawberry GraphQL type from table columns"""
        if table_name in self._type_cache:
            return self._type_cache[table_name]
        
        # Build type annotations
        annotations = {}
        for col in columns:
            col_name = col['column_name']
            pg_type = col['data_type'].lower()
            is_nullable = col['is_nullable'] == 'YES'
            
            # Map PostgreSQL type to Python type
            python_type = PG_TO_GRAPHQL_TYPE_MAP.get(pg_type, str)
            
            # Handle nullable fields
            if is_nullable and col_name != 'id':  # ID is usually required
                annotations[col_name] = Optional[python_type]
            else:
                annotations[col_name] = python_type
        
        # Create the type dynamically
        type_name = f"{table_name.title()}Type"
        
        @strawberry.type(name=type_name)
        class DynamicType:
            pass
        
        # Add annotations to the class
        DynamicType.__annotations__ = annotations
        
        # Cache the type
        self._type_cache[table_name] = DynamicType
        return DynamicType
    
    def _create_input_type(self, table_name: str, columns: List[Dict], operation: str = "create") -> Type:
        """Create input types for mutations"""
        input_name = f"{table_name.title()}{operation.title()}Input"
        
        annotations = {}
        for col in columns:
            col_name = col['column_name']
            pg_type = col['data_type'].lower()
            is_nullable = col['is_nullable'] == 'YES'
            has_default = col['column_default'] is not None
            is_auto_increment = 'nextval' in str(col['column_default']) if col['column_default'] else False
            
            # Skip auto-increment fields for create operations
            if operation == "create" and is_auto_increment:
                continue
            
            # Map PostgreSQL type to Python type
            python_type = PG_TO_GRAPHQL_TYPE_MAP.get(pg_type, str)
            
            # For update operations, most fields are optional
            # For create operations, only nullable fields with defaults are optional
            if operation == "update" or (is_nullable and has_default):
                annotations[col_name] = Optional[python_type]
            else:
                annotations[col_name] = python_type
        
        @strawberry.input(name=input_name)
        class DynamicInput:
            pass
        
        DynamicInput.__annotations__ = annotations
        return DynamicInput
    
    async def _execute_query(self, query: str, params: List = None) -> List[Dict]:
        """Execute a query against the project database"""
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                if params:
                    rows = await conn.fetch(query, *params)
                else:
                    rows = await conn.fetch(query)
                return [dict(row) for row in rows]
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise GraphQLSchemaError(f"Query execution failed: {e}")
    
    async def _execute_mutation(self, query: str, params: List = None) -> Dict:
        """Execute a mutation against the project database"""
        try:
            conn = await asyncpg.connect(self.db_url)
            try:
                if params:
                    row = await conn.fetchrow(query, *params)
                else:
                    row = await conn.fetchrow(query)
                return dict(row) if row else {}
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"Database mutation failed: {e}")
            raise GraphQLSchemaError(f"Mutation execution failed: {e}")
    
    def _create_resolvers(self, table_name: str, columns: List[Dict]) -> Dict[str, Any]:
        """Create resolver functions for a table"""
        
        async def list_resolver(info: Info, limit: int = 100, offset: int = 0) -> List[Dict]:
            """List all records from table"""
            # Check permissions
            context = info.context
            user = context.get('user')
            if not user:
                raise GraphQLSchemaError("Authentication required")
            
            user_role = PermissionManager.get_user_role(user.id, self.project.id, context.get('session'))
            if not user_role or not PermissionManager.has_permission(user_role, "data:read"):
                raise GraphQLSchemaError("Access denied: Missing data:read permission")
            
            query = f'SELECT * FROM "{table_name}" ORDER BY id LIMIT $1 OFFSET $2'
            return await self._execute_query(query, [limit, offset])
        
        async def get_resolver(info: Info, id: int) -> Optional[Dict]:
            """Get a single record by ID"""
            context = info.context
            user = context.get('user')
            if not user:
                raise GraphQLSchemaError("Authentication required")
            
            user_role = PermissionManager.get_user_role(user.id, self.project.id, context.get('session'))
            if not user_role or not PermissionManager.has_permission(user_role, "data:read"):
                raise GraphQLSchemaError("Access denied: Missing data:read permission")
            
            query = f'SELECT * FROM "{table_name}" WHERE id = $1'
            rows = await self._execute_query(query, [id])
            return rows[0] if rows else None
        
        async def create_resolver(info: Info, input_data: Dict) -> Dict:
            """Create a new record"""
            context = info.context
            user = context.get('user')
            if not user:
                raise GraphQLSchemaError("Authentication required")
            
            user_role = PermissionManager.get_user_role(user.id, self.project.id, context.get('session'))
            if not user_role or not PermissionManager.has_permission(user_role, "data:create"):
                raise GraphQLSchemaError("Access denied: Missing data:create permission")
            
            # Build INSERT query
            fields = list(input_data.keys())
            values = list(input_data.values())
            placeholders = ', '.join(f'${i+1}' for i in range(len(fields)))
            fields_str = ', '.join(f'"{field}"' for field in fields)
            
            query = f'INSERT INTO "{table_name}" ({fields_str}) VALUES ({placeholders}) RETURNING *'
            result = await self._execute_mutation(query, values)
            
            # Notify WebSocket clients
            try:
                from utils.websocket_manager import notify_table_change
                await notify_table_change(self.project.id, table_name, "INSERT", result)
            except Exception as e:
                logger.warning(f"Failed to notify WebSocket clients: {e}")
            
            return result
        
        async def update_resolver(info: Info, id: int, input_data: Dict) -> Dict:
            """Update an existing record"""
            context = info.context
            user = context.get('user')
            if not user:
                raise GraphQLSchemaError("Authentication required")
            
            user_role = PermissionManager.get_user_role(user.id, self.project.id, context.get('session'))
            if not user_role or not PermissionManager.has_permission(user_role, "data:update"):
                raise GraphQLSchemaError("Access denied: Missing data:update permission")
            
            # Build UPDATE query
            fields = list(input_data.keys())
            values = list(input_data.values()) + [id]
            set_clause = ', '.join(f'"{field}" = ${i+1}' for i, field in enumerate(fields))
            
            query = f'UPDATE "{table_name}" SET {set_clause} WHERE id = ${len(values)} RETURNING *'
            result = await self._execute_mutation(query, values)
            
            if not result:
                raise GraphQLSchemaError("Record not found")
            
            # Notify WebSocket clients
            try:
                from utils.websocket_manager import notify_table_change
                await notify_table_change(self.project.id, table_name, "UPDATE", result)
            except Exception as e:
                logger.warning(f"Failed to notify WebSocket clients: {e}")
            
            return result
        
        async def delete_resolver(info: Info, id: int) -> bool:
            """Delete a record"""
            context = info.context
            user = context.get('user')
            if not user:
                raise GraphQLSchemaError("Authentication required")
            
            user_role = PermissionManager.get_user_role(user.id, self.project.id, context.get('session'))
            if not user_role or not PermissionManager.has_permission(user_role, "data:delete"):
                raise GraphQLSchemaError("Access denied: Missing data:delete permission")
            
            # Get record before deletion for notification
            get_query = f'SELECT * FROM "{table_name}" WHERE id = $1'
            rows = await self._execute_query(get_query, [id])
            if not rows:
                raise GraphQLSchemaError("Record not found")
            
            old_record = rows[0]
            
            # Delete record
            query = f'DELETE FROM "{table_name}" WHERE id = $1'
            await self._execute_query(query, [id])
            
            # Notify WebSocket clients
            try:
                from utils.websocket_manager import notify_table_change
                await notify_table_change(self.project.id, table_name, "DELETE", old_record)
            except Exception as e:
                logger.warning(f"Failed to notify WebSocket clients: {e}")
            
            return True
        
        return {
            'list': list_resolver,
            'get': get_resolver,
            'create': create_resolver,
            'update': update_resolver,
            'delete': delete_resolver
        }
    
    async def generate_schema(self) -> strawberry.Schema:
        """Generate complete GraphQL schema for the project"""
        try:
            # Introspect tables
            tables_info = await self.introspect_tables()
            
            if not tables_info:
                # Create empty schema if no tables
                @strawberry.type
                class EmptyQuery:
                    @strawberry.field
                    def hello(self) -> str:
                        return f"No tables found in project {self.project.name}"
                
                return strawberry.Schema(query=EmptyQuery)
            
            # Generate types and resolvers for each table
            query_fields = {}
            mutation_fields = {}
            
            for table_name, columns in tables_info.items():
                # Create GraphQL type
                table_type = self._create_strawberry_type(table_name, columns)
                
                # Create input types
                create_input = self._create_input_type(table_name, columns, "create")
                update_input = self._create_input_type(table_name, columns, "update")
                
                # Create resolvers
                resolvers = self._create_resolvers(table_name, columns)
                
                # Add query fields
                query_fields[f"list_{table_name}"] = strawberry.field(
                    resolver=resolvers['list'],
                    description=f"List all {table_name} records"
                )
                query_fields[f"get_{table_name}"] = strawberry.field(
                    resolver=resolvers['get'],
                    description=f"Get a single {table_name} record by ID"
                )
                
                # Add mutation fields
                mutation_fields[f"create_{table_name}"] = strawberry.field(
                    resolver=resolvers['create'],
                    description=f"Create a new {table_name} record"
                )
                mutation_fields[f"update_{table_name}"] = strawberry.field(
                    resolver=resolvers['update'],
                    description=f"Update an existing {table_name} record"
                )
                mutation_fields[f"delete_{table_name}"] = strawberry.field(
                    resolver=resolvers['delete'],
                    description=f"Delete a {table_name} record"
                )
            
            # Create Query type
            @strawberry.type
            class Query:
                pass
            
            # Add fields to Query
            for field_name, field_def in query_fields.items():
                setattr(Query, field_name, field_def)
            
            # Create Mutation type
            @strawberry.type
            class Mutation:
                pass
            
            # Add fields to Mutation
            for field_name, field_def in mutation_fields.items():
                setattr(Mutation, field_name, field_def)
            
            # Create and return schema
            schema = strawberry.Schema(query=Query, mutation=Mutation)
            return schema
            
        except Exception as e:
            logger.error(f"Failed to generate GraphQL schema for project {self.project.id}: {e}")
            raise GraphQLSchemaError(f"Schema generation failed: {e}")

# Schema cache for projects
_schema_cache: Dict[int, strawberry.Schema] = {}

async def get_project_schema(project: Project, force_refresh: bool = False) -> strawberry.Schema:
    """Get or generate GraphQL schema for a project"""
    if force_refresh or project.id not in _schema_cache:
        generator = DynamicGraphQLSchema(project)
        schema = await generator.generate_schema()
        _schema_cache[project.id] = schema
        logger.info(f"Generated GraphQL schema for project {project.id}")
    
    return _schema_cache[project.id]

def clear_project_schema_cache(project_id: int):
    """Clear cached schema for a project"""
    if project_id in _schema_cache:
        del _schema_cache[project_id]
        logger.info(f"Cleared GraphQL schema cache for project {project_id}")

def get_schema_stats() -> Dict[str, Any]:
    """Get statistics about cached schemas"""
    return {
        "cached_schemas": len(_schema_cache),
        "project_ids": list(_schema_cache.keys())
    }