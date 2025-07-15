from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
import logging

from auth.dependencies import get_current_user
from database.session import get_session
from models.user import User
from models.project import Project, ProjectCreate, ProjectPublic, ProjectUpdate, generate_slug
from services.provisioning import provisioning_service, ProvisioningError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[ProjectPublic])
def read_projects(
    *, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)
):
    projects = session.exec(select(Project).where(Project.owner_id == current_user.id)).all()
    return projects

async def provision_project_infrastructure(project_id: int, project_name: str, session: Session):
    """Background task to provision project infrastructure"""
    try:
        logger.info(f"Starting infrastructure provisioning for project {project_id}")
        
        # Provision infrastructure
        slug, db_name, bucket_name = provisioning_service.provision_project(project_name)
        
        # Update project with provisioned infrastructure details
        project = session.get(Project, project_id)
        if project:
            project.slug = slug
            project.db_name = db_name
            project.bucket_name = bucket_name
            project.provisioning_status = "completed"
            session.add(project)
            session.commit()
            
            logger.info(f"Successfully provisioned infrastructure for project {project_id}")
        else:
            logger.error(f"Project {project_id} not found for infrastructure update")
            
    except ProvisioningError as e:
        logger.error(f"Provisioning failed for project {project_id}: {e}")
        # Update project status to failed
        project = session.get(Project, project_id)
        if project:
            project.provisioning_status = "failed"
            session.add(project)
            session.commit()
    except Exception as e:
        logger.error(f"Unexpected error during provisioning for project {project_id}: {e}")
        # Update project status to failed
        project = session.get(Project, project_id)
        if project:
            project.provisioning_status = "failed"
            session.add(project)
            session.commit()

@router.post("/", response_model=ProjectPublic)
def create_project(
    *, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session), 
    project_in: ProjectCreate, 
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project with dedicated infrastructure provisioning.
    
    This endpoint:
    1. Creates the project record in the database
    2. Triggers background provisioning of:
       - Dedicated PostgreSQL database
       - Dedicated MinIO bucket
    3. Returns immediately while provisioning happens in background
    
    The project status can be checked via the GET endpoint.
    """
    try:
        # Generate initial infrastructure names
        slug = generate_slug(project_in.name)
        db_name = f"project_{slug.replace('-', '_')}_db"
        bucket_name = f"project-{slug}-bucket"
        
        # Create project record with pending status
        project = Project(
            name=project_in.name,
            description=project_in.description,
            owner_id=current_user.id,
            slug=slug,
            db_name=db_name,
            bucket_name=bucket_name,
            provisioning_status="pending",
            max_items=project_in.max_items or 1000,
            storage_limit_mb=project_in.storage_limit_mb or 100,
            api_rate_limit=project_in.api_rate_limit or 1000,
            webhook_url=project_in.webhook_url,
            is_public=project_in.is_public or False,
            auto_backup=project_in.auto_backup if project_in.auto_backup is not None else True,
            backup_retention_days=project_in.backup_retention_days or 30
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        
        # Schedule infrastructure provisioning in background
        background_tasks.add_task(
            provision_project_infrastructure,
            project.id,
            project.name,
            session
        )
        
        logger.info(f"Created project {project.id} for user {current_user.id}, provisioning scheduled")
        return project
        
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=f"Project creation failed: {str(e)}")

@router.get("/{project_id}", response_model=ProjectPublic)
def read_project(
    *, session: Session = Depends(get_session), project_id: int, current_user: User = Depends(get_current_user)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return project

@router.put("/{project_id}", response_model=ProjectPublic)
def update_project(
    *, session: Session = Depends(get_session), project_id: int, project_update: ProjectUpdate, current_user: User = Depends(get_current_user)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@router.delete("/{project_id}")
def delete_project(
    *, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session), 
    project_id: int, 
    current_user: User = Depends(get_current_user)
):
    """
    Delete a project and cleanup its dedicated infrastructure.
    
    This will:
    1. Delete the project record
    2. Schedule cleanup of dedicated PostgreSQL database
    3. Schedule cleanup of dedicated MinIO bucket
    
    WARNING: This permanently deletes all project data!
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Store infrastructure details for cleanup
    db_name = project.db_name
    bucket_name = project.bucket_name
    
    # Delete project record
    session.delete(project)
    session.commit()
    
    # Schedule infrastructure cleanup in background
    if project.provisioning_status == "completed":
        background_tasks.add_task(
            cleanup_project_infrastructure,
            db_name,
            bucket_name
        )
    
    logger.info(f"Deleted project {project_id}, infrastructure cleanup scheduled")
    return {"ok": True}

async def cleanup_project_infrastructure(db_name: str, bucket_name: str):
    """Background task to cleanup project infrastructure"""
    try:
        logger.info(f"Starting infrastructure cleanup for DB: {db_name}, Bucket: {bucket_name}")
        
        success = provisioning_service.cleanup_project(db_name, bucket_name)
        
        if success:
            logger.info(f"Successfully cleaned up infrastructure: {db_name}, {bucket_name}")
        else:
            logger.warning(f"Partial cleanup failure for: {db_name}, {bucket_name}")
            
    except Exception as e:
        logger.error(f"Infrastructure cleanup failed for {db_name}, {bucket_name}: {e}")
