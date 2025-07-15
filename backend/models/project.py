
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import uuid
import re

if TYPE_CHECKING:
    from models.user import User
    from models.item import Item
    from models.project_membership import ProjectMembership

def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from project name"""
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return f"{slug}-{uuid.uuid4().hex[:8]}"

class ProjectBase(SQLModel):
    name: str
    description: Optional[str] = None

class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    api_key: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Multi-tenant infrastructure
    db_name: str = Field(unique=True, index=True)
    bucket_name: str = Field(unique=True, index=True)
    
    # Configuration fields
    max_items: Optional[int] = Field(default=1000, description="Maximum number of items allowed")
    storage_limit_mb: Optional[int] = Field(default=100, description="Storage limit in MB")
    api_rate_limit: Optional[int] = Field(default=1000, description="API calls per hour limit")
    webhook_url: Optional[str] = Field(default=None, description="Webhook URL for notifications")
    is_public: bool = Field(default=False, description="Whether the project is publicly accessible")
    auto_backup: bool = Field(default=True, description="Enable automatic backups")
    backup_retention_days: Optional[int] = Field(default=30, description="Number of days to retain backups")
    
    # Status tracking
    provisioning_status: str = Field(default="pending", description="Status of infrastructure provisioning")
    
    owner_id: int = Field(foreign_key="user.id")
    
    # Relationships
    owner: "User" = Relationship(back_populates="projects")
    items: List["Item"] = Relationship(back_populates="project")
    memberships: List["ProjectMembership"] = Relationship(back_populates="project")

class ProjectCreate(ProjectBase):
    max_items: Optional[int] = 1000
    storage_limit_mb: Optional[int] = 100
    api_rate_limit: Optional[int] = 1000
    webhook_url: Optional[str] = None
    is_public: Optional[bool] = False
    auto_backup: Optional[bool] = True
    backup_retention_days: Optional[int] = 30

class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_items: Optional[int] = None
    storage_limit_mb: Optional[int] = None
    api_rate_limit: Optional[int] = None
    webhook_url: Optional[str] = None
    is_public: Optional[bool] = None
    auto_backup: Optional[bool] = None
    backup_retention_days: Optional[int] = None

class ProjectPublic(ProjectBase):
    id: int
    slug: Optional[str] = None
    api_key: str
    owner_id: int
    created_at: datetime
    db_name: Optional[str] = None
    bucket_name: Optional[str] = None
    max_items: Optional[int]
    storage_limit_mb: Optional[int]
    api_rate_limit: Optional[int]
    webhook_url: Optional[str]
    is_public: bool
    auto_backup: bool
    backup_retention_days: Optional[int]
    provisioning_status: Optional[str] = "pending"
