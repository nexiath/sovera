#!/usr/bin/env python3

from sqlmodel import text
from database.session import engine

def migrate_project_config():
    """Add configuration fields to existing project table"""
    
    migration_sql = """
    ALTER TABLE project 
    ADD COLUMN IF NOT EXISTS max_items INTEGER DEFAULT 1000,
    ADD COLUMN IF NOT EXISTS storage_limit_mb INTEGER DEFAULT 100,
    ADD COLUMN IF NOT EXISTS api_rate_limit INTEGER DEFAULT 1000,
    ADD COLUMN IF NOT EXISTS webhook_url VARCHAR,
    ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS auto_backup BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS backup_retention_days INTEGER DEFAULT 30;
    """
    
    with engine.begin() as conn:
        conn.execute(text(migration_sql))
        print("✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate_project_config()