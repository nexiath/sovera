"""
Migration script to add RBAC (Role-Based Access Control) support to Sovera.
Adds the project_memberships table for managing project access and roles.
"""

import logging
from sqlmodel import SQLModel, create_engine, Session

from core.config import settings
from models.user import User
from models.project import Project
from models.project_membership import ProjectMembership

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the RBAC migration"""
    logger.info("Starting RBAC migration...")
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Create tables
    logger.info("Creating project_memberships table...")
    SQLModel.metadata.create_all(engine)
    
    logger.info("✅ RBAC migration completed successfully!")
    logger.info("New table created: project_memberships")
    logger.info("Project owners can now invite users with roles: owner, editor, viewer")

if __name__ == "__main__":
    run_migration()