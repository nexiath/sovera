from sqlmodel import Session, select

from auth.security import get_password_hash
from models.user import User, UserCreate

def get_user_by_email(session: Session, *, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()

def create_user(session: Session, *, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    user = User.from_orm(user_in, {"hashed_password": hashed_password})
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
