"""
Dynamic tables router for Sovera.
Allows users to create and manage custom tables in their project databases.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session
import logging

from auth.dependencies import get_current_user
from database.session import get_session
from models.user import User
from models.project import Project
from models.table_schema import TableSchemaCreate, TableSchemaResponse, TableInfo
from services.table_provisioning import table_provisioning_service, TableProvisioningError
from utils.rbac import require_project_editor, require_project_viewer

logger = logging.getLogger(__name__)
router = APIRouter()

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

@router.post("/projects/{project_id}/tables/", response_model=Dict[str, Any])
async def create_table(
    project_id: int = Path(..., description="Project ID", gt=0),
    table_schema: TableSchemaCreate = ...,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_editor)
):
    """
    Create a new custom table in the project's dedicated database.
    
    This endpoint allows users to dynamically create tables with custom schemas
    in their project's PostgreSQL database. Each table is created with the
    specified columns and constraints.
    
    **Features:**
    - Custom column types (INTEGER, TEXT, TIMESTAMP, JSON, etc.)
    - Primary key and unique constraints
    - Automatic ID column if no primary key specified
    - Validation of table and column names
    - Prevention of SQL injection through parameter validation
    
    **Security:**
    - Only project editors and owners can create tables
    - Table names are validated against reserved keywords
    - Column types are restricted to safe PostgreSQL types
    """
    # Project access already verified by require_project_editor dependency
    if project.provisioning_status != "completed":
        raise HTTPException(
            status_code=400, 
            detail="Project infrastructure not ready. Please wait for provisioning to complete."
        )
    
    try:
        logger.info(f"Creating table '{table_schema.table_name}' in project {project_id} for user {current_user.id}")
        
        # Create table in project's dedicated database
        result = await table_provisioning_service.provision_table(
            db_name=project.db_name,
            schema=table_schema
        )
        
        # Add project context to response
        result.update({
            "project_id": project_id,
            "project_name": project.name,
            "database_name": project.db_name
        })
        
        logger.info(f"Successfully created table '{table_schema.table_name}' in project {project_id}")
        return result
        
    except TableProvisioningError as e:
        logger.warning(f"Table creation failed for project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating table in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during table creation")

@router.get("/projects/{project_id}/tables/", response_model=List[TableInfo])
async def list_tables(
    project_id: int = Path(..., description="Project ID", gt=0),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
):
    """
    List all custom tables in the project's database.
    
    Returns information about all user-created tables in the project,
    excluding system tables used by Sovera internally.
    
    **Returns:**
    - Table name
    - Column count
    - Row count (if accessible)
    - Creation metadata
    """
    # Project access already verified by require_project_viewer dependency
    
    try:
        logger.info(f"Listing tables for project {project_id}")
        
        tables = await table_provisioning_service.list_tables(project.db_name)
        
        # Convert to response models
        result = [
            TableInfo(
                table_name=table["table_name"],
                column_count=table["column_count"],
                row_count=table.get("row_count"),
                size_mb=table.get("size_mb")
            )
            for table in tables
        ]
        
        logger.info(f"Found {len(result)} tables in project {project_id}")
        return result
        
    except TableProvisioningError as e:
        logger.warning(f"Failed to list tables for project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error listing tables for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while listing tables")

@router.get("/projects/{project_id}/tables/{table_name}/schema", response_model=Dict[str, Any])
async def get_table_schema(
    project_id: int = Path(..., description="Project ID", gt=0),
    table_name: str = Path(..., description="Table name", min_length=1, max_length=63),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_viewer)
):
    """
    Get detailed schema information for a specific table.
    
    Returns complete column definitions, constraints, and metadata
    for the specified table in the project's database.
    """
    # Project access already verified by require_project_viewer dependency
    
    try:
        logger.info(f"Getting schema for table '{table_name}' in project {project_id}")
        
        schema_info = await table_provisioning_service.get_table_schema(
            project.db_name, 
            table_name
        )
        
        if schema_info is None:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        # Add project context
        schema_info.update({
            "project_id": project_id,
            "database_name": project.db_name
        })
        
        return schema_info
        
    except HTTPException:
        raise
    except TableProvisioningError as e:
        logger.warning(f"Failed to get schema for table '{table_name}' in project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting table schema for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while getting table schema")

@router.delete("/projects/{project_id}/tables/{table_name}")
async def drop_table(
    project_id: int = Path(..., description="Project ID", gt=0),
    table_name: str = Path(..., description="Table name", min_length=1, max_length=63),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    project: Project = Depends(require_project_editor)
):
    """
    Drop (delete) a custom table from the project's database.
    
    **Warning:** This operation is irreversible and will permanently
    delete the table and all its data. System tables cannot be dropped.
    
    **Security:**
    - Only project editors and owners can drop tables
    - System tables are protected from deletion
    - Cascade delete removes dependent objects
    """
    # Project access already verified by require_project_editor dependency
    
    try:
        logger.info(f"Dropping table '{table_name}' from project {project_id}")
        
        success = await table_provisioning_service.drop_table(
            project.db_name,
            table_name
        )
        
        if success:
            logger.info(f"Successfully dropped table '{table_name}' from project {project_id}")
            return {
                "message": f"Table '{table_name}' has been successfully deleted",
                "table_name": table_name,
                "project_id": project_id
            }
        else:
            raise HTTPException(status_code=500, detail="Table deletion failed")
            
    except TableProvisioningError as e:
        logger.warning(f"Failed to drop table '{table_name}' from project {project_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error dropping table '{table_name}' from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while dropping table")