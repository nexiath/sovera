from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from auth.dependencies import get_current_user
from database.session import get_session
from models.user import User
from models.project import Project
from models.item import Item, ItemCreate, ItemUpdate, ItemPublic

router = APIRouter()

def get_project_for_user(project_id: int, session: Session, current_user: User) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return project

@router.get("/", response_model=List[ItemPublic])
def read_items(
    *, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
    project_id: int,
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
    sort_by: Optional[str] = None,
    order: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    project = get_project_for_user(project_id, session, current_user)
    query = select(Item).where(Item.project_id == project.id)

    if search:
        query = query.where(Item.label.contains(search))
    if date_from:
        query = query.where(Item.created_at >= date_from)
    if date_to:
        query = query.where(Item.created_at <= date_to)

    if sort_by:
        if order == "desc":
            query = query.order_by(getattr(Item, sort_by).desc())
        else:
            query = query.order_by(getattr(Item, sort_by).asc())

    items = session.exec(query.offset(offset).limit(limit)).all()
    return items

@router.post("/", response_model=ItemPublic)
def create_item(
    *, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
    project_id: int,
    item_in: ItemCreate,
):
    project = get_project_for_user(project_id, session, current_user)
    item = Item.model_validate(item_in, update={"project_id": project.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.get("/{item_id}", response_model=ItemPublic)
def read_item(
    *, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
    project_id: int,
    item_id: int,
):
    project = get_project_for_user(project_id, session, current_user)
    item = session.get(Item, item_id)
    if not item or item.project_id != project.id:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/{item_id}", response_model=ItemPublic)
def update_item(
    *, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
    project_id: int,
    item_id: int,
    item_in: ItemUpdate,
):
    project = get_project_for_user(project_id, session, current_user)
    item = session.get(Item, item_id)
    if not item or item.project_id != project.id:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item_data = item_in.model_dump(exclude_unset=True)
    for key, value in item_data.items():
        setattr(item, key, value)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_item(
    *, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
    project_id: int,
    item_id: int,
):
    project = get_project_for_user(project_id, session, current_user)
    item = session.get(Item, item_id)
    if not item or item.project_id != project.id:
        raise HTTPException(status_code=404, detail="Item not found")
    
    session.delete(item)
    session.commit()
    return {"ok": True}
