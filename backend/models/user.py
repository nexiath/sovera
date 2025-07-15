from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from models.project import Project
    from models.project_membership import ProjectMembership

class UserRole(str, Enum):
    """Global user roles for system-wide permissions"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin" 
    USER = "user"

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_active: bool = True
    role: UserRole = Field(default=UserRole.USER)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    projects: List["Project"] = Relationship(back_populates="owner")
    # Commented out to avoid circular import issues
    # project_memberships: List["ProjectMembership"] = Relationship(back_populates="user")

class UserCreate(UserBase):
    password: str

class UserPublic(UserBase):
    id: int
    created_at: datetime

class UserUpdate(SQLModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

class UserAdmin(UserPublic):
    """Admin view of user with additional fields"""
    pass
