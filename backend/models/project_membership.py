"""
Project membership models for RBAC (Role-Based Access Control).
Allows project owners to invite users with specific roles.
"""

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from models.user import User
    from models.project import Project

class ProjectRole(str, Enum):
    """Project roles hierarchy"""
    OWNER = "owner"      # Full access, can manage members
    EDITOR = "editor"    # Can create/edit/delete data and tables
    VIEWER = "viewer"    # Read-only access to data

class InvitationStatus(str, Enum):
    """Invitation status"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ProjectMembershipBase(SQLModel):
    """Base model for project membership"""
    project_id: int = Field(foreign_key="project.id")
    user_id: int = Field(foreign_key="user.id")
    role: ProjectRole = Field(default=ProjectRole.VIEWER)
    invited_by: Optional[int] = Field(default=None, foreign_key="user.id")
    invited_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = Field(default=None)
    status: InvitationStatus = Field(default=InvitationStatus.PENDING)

class ProjectMembership(ProjectMembershipBase, table=True):
    """Project membership model"""
    __tablename__ = "project_memberships"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    # user: "User" = Relationship(back_populates="project_memberships")  # Removed to avoid circular import
    project: "Project" = Relationship(back_populates="memberships")
    
    # Unique constraint: user can only have one membership per project
    __table_args__ = (
        {"extend_existing": True},
    )

class ProjectMembershipCreate(SQLModel):
    """Create project membership (invitation)"""
    project_id: int
    user_email: str  # Email of user to invite
    role: ProjectRole = ProjectRole.VIEWER
    message: Optional[str] = None  # Optional invitation message

class ProjectMembershipUpdate(SQLModel):
    """Update project membership"""
    role: Optional[ProjectRole] = None
    status: Optional[InvitationStatus] = None

class ProjectMembershipPublic(ProjectMembershipBase):
    """Public project membership model"""
    id: int
    user_email: str
    user_name: Optional[str] = None
    inviter_email: Optional[str] = None
    
class ProjectMembershipResponse(SQLModel):
    """Response model for membership operations"""
    id: int
    project_id: int
    project_name: str
    user_id: int
    user_email: str
    role: ProjectRole
    status: InvitationStatus
    invited_at: datetime
    accepted_at: Optional[datetime]
    inviter_email: Optional[str]

class ProjectInvitation(SQLModel):
    """Model for invitation details"""
    id: int
    project_id: int
    project_name: str
    project_description: Optional[str]
    role: ProjectRole
    invited_by_name: Optional[str]
    invited_by_email: str
    invited_at: datetime
    message: Optional[str]
    status: InvitationStatus