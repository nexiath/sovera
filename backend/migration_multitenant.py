#!/usr/bin/env python3

from sqlmodel import text
from database.session import engine

def migrate_project_multitenant():
    """Add multi-tenant fields to existing project table"""
    
    migration_sql = """
    ALTER TABLE project 
    ADD COLUMN IF NOT EXISTS slug VARCHAR(255) UNIQUE,
    ADD COLUMN IF NOT EXISTS db_name VARCHAR(255) UNIQUE,
    ADD COLUMN IF NOT EXISTS bucket_name VARCHAR(255) UNIQUE,
    ADD COLUMN IF NOT EXISTS provisioning_status VARCHAR(50) DEFAULT 'pending';
    
    CREATE INDEX IF NOT EXISTS idx_project_slug ON project(slug);
    CREATE INDEX IF NOT EXISTS idx_project_db_name ON project(db_name);
    CREATE INDEX IF NOT EXISTS idx_project_bucket_name ON project(bucket_name);
    """
    
    with engine.begin() as conn:
        conn.execute(text(migration_sql))
        print("✅ Multi-tenant migration completed successfully!")

if __name__ == "__main__":
    migrate_project_multitenant()