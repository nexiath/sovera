from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from models.project import Project

class ItemBase(SQLModel):
    label: str
    content: str

class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    project_id: int = Field(foreign_key="project.id")
    project: "Project" = Relationship(back_populates="items")

class ItemCreate(ItemBase):
    pass

class ItemUpdate(SQLModel):
    label: Optional[str] = None
    content: Optional[str] = None

class ItemPublic(ItemBase):
    id: int
    created_at: datetime
    project_id: int
