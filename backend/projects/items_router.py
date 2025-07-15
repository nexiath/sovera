"""
Multi-tenant items router that uses project-specific databases.
Each project's items are stored in its dedicated PostgreSQL database.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlmodel import Session, select
import logging

from auth.dependencies import get_current_user
from database.session import get_session
from database.multi_tenant import multi_tenant_manager
from models.user import User
from models.project import Project
from models.project_item import (
    ProjectItem, 
    ProjectItemCreate, 
    ProjectItemUpdate, 
    ProjectItemPublic
)

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
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if project.provisioning_status != "completed":
        raise HTTPException(status_code=400, detail="Project infrastructure not ready")
    return project

@router.get("/projects/{project_id}/items/", response_model=List[ProjectItemPublic])
async def read_project_items(
    project_id: int = Path(..., description="Project ID"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all items from project's dedicated database"""
    # Verify access to project
    project = await get_project_and_verify_access(project_id, current_user, session)
    
    try:
        # Get session for project's dedicated database
        project_session = await multi_tenant_manager.get_project_session(project.db_name)
        
        async with project_session as ps:
            # Build query
            query = select(ProjectItem)
            
            if search:
                query = query.where(ProjectItem.label.contains(search))
            
            # Execute query in project database
            result = await ps.execute(query.offset(offset).limit(limit))
            items = result.scalars().all()
            
            return items
            
    except Exception as e:
        logger.error(f"Failed to read items from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read project items")

@router.post("/projects/{project_id}/items/", response_model=ProjectItemPublic)
async def create_project_item(
    project_id: int = Path(..., description="Project ID"),
    item_in: ProjectItemCreate = ...,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create new item in project's dedicated database"""
    # Verify access to project
    project = await get_project_and_verify_access(project_id, current_user, session)
    
    try:
        # Get session for project's dedicated database
        project_session = await multi_tenant_manager.get_project_session(project.db_name)
        
        async with project_session as ps:
            # Create item in project database
            item = ProjectItem(
                label=item_in.label,
                content=item_in.content
            )
            
            ps.add(item)
            await ps.commit()
            await ps.refresh(item)
            
            logger.info(f"Created item {item.id} in project {project_id} database")
            return item
            
    except Exception as e:
        logger.error(f"Failed to create item in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project item")

@router.get("/projects/{project_id}/items/{item_id}", response_model=ProjectItemPublic)
async def read_project_item(
    project_id: int = Path(..., description="Project ID"),
    item_id: int = Path(..., description="Item ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get specific item from project's dedicated database"""
    # Verify access to project
    project = await get_project_and_verify_access(project_id, current_user, session)
    
    try:
        # Get session for project's dedicated database
        project_session = await multi_tenant_manager.get_project_session(project.db_name)
        
        async with project_session as ps:
            item = await ps.get(ProjectItem, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            return item
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read item {item_id} from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read project item")

@router.put("/projects/{project_id}/items/{item_id}", response_model=ProjectItemPublic)
async def update_project_item(
    project_id: int = Path(..., description="Project ID"),
    item_id: int = Path(..., description="Item ID"),
    item_update: ProjectItemUpdate = ...,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update item in project's dedicated database"""
    # Verify access to project
    project = await get_project_and_verify_access(project_id, current_user, session)
    
    try:
        # Get session for project's dedicated database
        project_session = await multi_tenant_manager.get_project_session(project.db_name)
        
        async with project_session as ps:
            item = await ps.get(ProjectItem, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            # Update fields
            update_data = item_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(item, field, value)
            
            # Update timestamp
            from datetime import datetime
            item.updated_at = datetime.utcnow()
            
            await ps.commit()
            await ps.refresh(item)
            
            logger.info(f"Updated item {item_id} in project {project_id} database")
            return item
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update item {item_id} in project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project item")

@router.delete("/projects/{project_id}/items/{item_id}")
async def delete_project_item(
    project_id: int = Path(..., description="Project ID"),
    item_id: int = Path(..., description="Item ID"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete item from project's dedicated database"""
    # Verify access to project
    project = await get_project_and_verify_access(project_id, current_user, session)
    
    try:
        # Get session for project's dedicated database
        project_session = await multi_tenant_manager.get_project_session(project.db_name)
        
        async with project_session as ps:
            item = await ps.get(ProjectItem, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            await ps.delete(item)
            await ps.commit()
            
            logger.info(f"Deleted item {item_id} from project {project_id} database")
            return {"ok": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete item {item_id} from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project item")