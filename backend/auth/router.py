from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from auth.security import create_access_token, get_password_hash, verify_password
from database.session import get_session
from auth.dependencies import get_current_user
from models.user import User, UserCreate, UserPublic
from auth.permissions import GlobalPermissionManager

router = APIRouter()

@router.post("/register", response_model=UserPublic)
def register(*, session: Session = Depends(get_session), user_in: UserCreate):
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if user:
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists",
        )
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email, 
        hashed_password=hashed_password,
        is_active=user_in.is_active,
        role=user_in.role
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post("/login")
def login(session: Session = Depends(get_session), form_data: OAuth2PasswordRequestForm = Depends()):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserPublic)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/me/permissions")
def get_user_permissions(current_user: User = Depends(get_current_user)):
    """Get current user's permissions"""
    permissions = GlobalPermissionManager.get_permissions(current_user.role)
    return {
        "role": current_user.role,
        "permissions": list(permissions),
        "can_access_users": GlobalPermissionManager.can_access_users_section(current_user.role),
        "can_manage_users": GlobalPermissionManager.can_manage_users(current_user.role),
        "can_delete_users": GlobalPermissionManager.can_delete_users(current_user.role),
        "can_access_monitoring": GlobalPermissionManager.can_access_monitoring(current_user.role),
        "can_manage_system": GlobalPermissionManager.can_manage_system(current_user.role)
    }
