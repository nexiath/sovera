"""
Multi-tenant database management for project-specific PostgreSQL databases.
Each project gets its own dedicated database with dynamic connection management.
"""

import os
import logging
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)

class MultiTenantManager:
    """Manages dynamic database connections for each project"""
    
    def __init__(self):
        self.engine_cache: Dict[str, async_sessionmaker] = {}
        self.base_url = self._get_base_db_url()
    
    def _get_base_db_url(self) -> str:
        """Get base PostgreSQL connection URL"""
        host = os.getenv("POSTGRES_SERVER", "db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        return f"postgresql+asyncpg://{user}:{password}@{host}"
    
    def get_project_db_url(self, db_name: str) -> str:
        """Generate database URL for a specific project"""
        return f"{self.base_url}/{db_name}"
    
    def get_project_session_factory(self, db_name: str) -> async_sessionmaker:
        """Get or create async session factory for project database"""
        db_url = self.get_project_db_url(db_name)
        
        if db_url not in self.engine_cache:
            logger.info(f"Creating new engine for database: {db_name}")
            engine = create_async_engine(
                db_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            self.engine_cache[db_url] = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        
        return self.engine_cache[db_url]
    
    async def get_project_session(self, db_name: str) -> AsyncSession:
        """Get async session for project database"""
        session_factory = self.get_project_session_factory(db_name)
        return session_factory()
    
    def create_project_schema(self, db_name: str):
        """Create complete schema in project database"""
        try:
            # Use sync engine for schema creation
            sync_url = self.get_project_db_url(db_name).replace('+asyncpg', '')
            engine = create_engine(sync_url)
            
            # Create all tables from SQLModel metadata
            with engine.begin() as conn:
                # Import all models to ensure they're registered
                from models.item import Item
                from models.user import User  # For foreign keys
                
                # Create schema for project-specific models
                self._create_project_tables(conn)
                
            logger.info(f"Schema created successfully for database: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to create schema for {db_name}: {e}")
            raise
    
    def _create_project_tables(self, connection):
        """Create project-specific tables"""
        # Create items table (main project data)
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                label VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_items_label ON items(label);
            CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at);
        """))
        
        # Create project metadata table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS project_metadata (
                id SERIAL PRIMARY KEY,
                key VARCHAR(255) NOT NULL UNIQUE,
                value JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_project_metadata_key ON project_metadata(key);
        """))
        
        # Create files metadata table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                size_bytes BIGINT,
                content_type VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename);
        """))
        
        # Insert initial metadata
        connection.execute(text("""
            INSERT INTO project_metadata (key, value) 
            VALUES ('schema_version', '"1.0"'), ('created_at', to_jsonb(NOW()))
            ON CONFLICT (key) DO NOTHING;
        """))

# Global multi-tenant manager instance
multi_tenant_manager = MultiTenantManager()