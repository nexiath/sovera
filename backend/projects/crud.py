from typing import List
from sqlmodel import Session

from models.project import Project, ProjectCreate
from models.user import User

def get_projects_by_owner(session: Session, *, owner: User) -> List[Project]:
    return owner.projects

def create_project(session: Session, *, project_in: ProjectCreate, owner: User) -> Project:
    project = Project.from_orm(project_in, {"owner_id": owner.id})
    session.add(project)
    session.commit()
    session.refresh(project)
    return project
