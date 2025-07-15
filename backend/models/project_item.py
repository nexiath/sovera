"""
Project-specific item models for multi-tenant architecture.
These models are used within each project's dedicated database.
"""

from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class ProjectItemBase(SQLModel):
    """Base model for items within a project database"""
    label: str
    content: str

class ProjectItem(ProjectItemBase, table=True):
    """Item model for project-specific databases"""
    __tablename__ = "items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProjectItemCreate(ProjectItemBase):
    """Model for creating new items in project database"""
    pass

class ProjectItemUpdate(SQLModel):
    """Model for updating items in project database"""
    label: Optional[str] = None
    content: Optional[str] = None

class ProjectItemPublic(ProjectItemBase):
    """Public model for returning item data"""
    id: int
    created_at: datetime
    updated_at: datetime