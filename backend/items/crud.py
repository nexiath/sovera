from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select

from models.item import Item, ItemCreate, ItemUpdate
from models.project import Project

def get_items_by_project(
    session: Session, 
    *, 
    project: Project,
    offset: int = 0,
    limit: int = 100,
    sort_by: Optional[str] = None,
    order: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[Item]:
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

    return session.exec(query.offset(offset).limit(limit)).all()

def create_item(session: Session, *, item_in: ItemCreate, project: Project) -> Item:
    item = Item.from_orm(item_in, {"project_id": project.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def get_item_by_id(session: Session, *, item_id: int) -> Item | None:
    return session.get(Item, item_id)

def update_item(session: Session, *, item: Item, item_in: ItemUpdate) -> Item:
    item_data = item_in.dict(exclude_unset=True)
    for key, value in item_data.items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def delete_item(session: Session, *, item: Item):
    session.delete(item)
    session.commit()
