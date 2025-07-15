"""
Role-Based Access Control (RBAC) utilities for Sovera.
Provides functions for permission checking and role hierarchy management.
"""

from typing import Dict, List, Optional, Set
from fastapi import HTTPException, Depends
from sqlmodel import Session, select

from models.user import User
from models.project import Project
from models.project_membership import ProjectMembership, ProjectRole
from database.session import get_session
from auth.dependencies import get_current_user

class RBACError(Exception):
    """Custom exception for RBAC-related errors"""
    pass

class PermissionManager:
    """Manages role-based permissions for Sovera projects"""
    
    # Define role hierarchy (higher roles include lower role permissions)
    ROLE_HIERARCHY = {
        ProjectRole.OWNER: {ProjectRole.EDITOR, ProjectRole.VIEWER},
        ProjectRole.EDITOR: {ProjectRole.VIEWER},
        ProjectRole.VIEWER: set()
    }
    
    # Define permissions for each role
    PERMISSIONS = {
        ProjectRole.OWNER: {
            # Project management
            'project:read', 'project:update', 'project:delete',
            # Member management
            'members:read', 'members:invite', 'members:update', 'members:remove',
            # Table management
            'tables:read', 'tables:create', 'tables:update', 'tables:delete',
            # Data management
            'data:read', 'data:create', 'data:update', 'data:delete',
            # File management
            'files:read', 'files:upload', 'files:delete',
            # Settings
            'settings:read', 'settings:update'
        },
        ProjectRole.EDITOR: {
            # Project (read only)
            'project:read',
            # Member management (read only)
            'members:read',
            # Table management
            'tables:read', 'tables:create', 'tables:update', 'tables:delete',
            # Data management
            'data:read', 'data:create', 'data:update', 'data:delete',
            # File management
            'files:read', 'files:upload', 'files:delete',
            # Settings (read only)
            'settings:read'
        },
        ProjectRole.VIEWER: {
            # Project (read only)
            'project:read',
            # Member management (read only)
            'members:read',
            # Table management (read only)
            'tables:read',
            # Data management (read only)
            'data:read',
            # File management (read only)
            'files:read',
            # Settings (read only)
            'settings:read'
        }
    }
    
    @classmethod
    def get_user_role(cls, user_id: int, project_id: int, session: Session) -> Optional[ProjectRole]:
        """Get user's role for a specific project"""
        # Check if user is project owner
        project = session.get(Project, project_id)
        if project and project.owner_id == user_id:
            return ProjectRole.OWNER
        
        # Check membership
        membership = session.exec(
            select(ProjectMembership).where(
                ProjectMembership.user_id == user_id,
                ProjectMembership.project_id == project_id,
                ProjectMembership.status == "accepted"
            )
        ).first()
        
        return membership.role if membership else None
    
    @classmethod
    def has_permission(cls, role: ProjectRole, permission: str) -> bool:
        """Check if role has specific permission"""
        return permission in cls.PERMISSIONS.get(role, set())
    
    @classmethod
    def has_role_or_higher(cls, user_role: ProjectRole, required_role: ProjectRole) -> bool:
        """Check if user role is equal to or higher than required role"""
        if user_role == required_role:
            return True
        
        # Check if user role includes required role in hierarchy
        return required_role in cls.ROLE_HIERARCHY.get(user_role, set())
    
    @classmethod
    def get_effective_permissions(cls, role: ProjectRole) -> Set[str]:
        """Get all permissions for a role (including inherited ones)"""
        permissions = set()
        
        # Add direct permissions
        permissions.update(cls.PERMISSIONS.get(role, set()))
        
        # Add inherited permissions from lower roles
        for lower_role in cls.ROLE_HIERARCHY.get(role, set()):
            permissions.update(cls.PERMISSIONS.get(lower_role, set()))
        
        return permissions

# Dependency functions for FastAPI

async def get_project_with_permission(
    permission: str,
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Project:
    """
    Get project if user has specific permission.
    Raises HTTPException if user doesn't have permission.
    """
    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get user role
    user_role = PermissionManager.get_user_role(current_user.id, project_id, session)
    if not user_role:
        raise HTTPException(status_code=403, detail="Access denied: No access to this project")
    
    # Check permission
    if not PermissionManager.has_permission(user_role, permission):
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied: Missing permission '{permission}'"
        )
    
    return project

async def get_project_with_role(
    required_role: ProjectRole,
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Project:
    """
    Get project if user has required role or higher.
    Raises HTTPException if user doesn't have sufficient role.
    """
    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get user role
    user_role = PermissionManager.get_user_role(current_user.id, project_id, session)
    if not user_role:
        raise HTTPException(status_code=403, detail="Access denied: No access to this project")
    
    # Check role hierarchy
    if not PermissionManager.has_role_or_higher(user_role, required_role):
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied: Role '{required_role}' required (you have '{user_role}')"
        )
    
    return project

async def get_project_with_membership(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> tuple[Project, ProjectRole]:
    """
    Get project and user's role.
    Raises HTTPException if user has no access.
    """
    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get user role
    user_role = PermissionManager.get_user_role(current_user.id, project_id, session)
    if not user_role:
        raise HTTPException(status_code=403, detail="Access denied: No access to this project")
    
    return project, user_role

# Specific dependencies for common operations

async def require_project_owner(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Project:
    """Require project owner role"""
    return await get_project_with_role(ProjectRole.OWNER, project_id, current_user, session)

async def require_project_editor(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Project:
    """Require project editor role or higher"""
    return await get_project_with_role(ProjectRole.EDITOR, project_id, current_user, session)

async def require_project_viewer(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Project:
    """Require project viewer role or higher"""
    return await get_project_with_role(ProjectRole.VIEWER, project_id, current_user, session)

# Utility functions

def get_user_projects_with_role(
    user_id: int, 
    role: Optional[ProjectRole] = None,
    session: Session = None
) -> List[Dict]:
    """Get all projects user has access to, optionally filtered by role"""
    # Get owned projects
    owned_projects = session.exec(
        select(Project).where(Project.owner_id == user_id)
    ).all()
    
    projects = []
    for project in owned_projects:
        if not role or role == ProjectRole.OWNER:
            projects.append({
                'project': project,
                'role': ProjectRole.OWNER,
                'membership_id': None
            })
    
    # Get member projects
    memberships = session.exec(
        select(ProjectMembership).where(
            ProjectMembership.user_id == user_id,
            ProjectMembership.status == "accepted"
        )
    ).all()
    
    for membership in memberships:
        if not role or role == membership.role:
            projects.append({
                'project': membership.project,
                'role': membership.role,
                'membership_id': membership.id
            })
    
    return projects

def can_user_access_project(user_id: int, project_id: int, session: Session) -> bool:
    """Check if user can access project (any role)"""
    role = PermissionManager.get_user_role(user_id, project_id, session)
    return role is not None