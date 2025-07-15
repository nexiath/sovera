"""
Admin user management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from auth.dependencies import require_admin, require_super_admin, require_users_access, get_current_active_user
from database.session import get_session
from models.user import User, UserCreate, UserUpdate, UserAdmin, UserRole
from auth.security import get_password_hash

router = APIRouter()

@router.get("/users", response_model=List[UserAdmin])
def list_users(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_users_access),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by email"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    List all users (admin only)
    """
    query = select(User)
    
    # Apply filters
    if search:
        query = query.where(User.email.contains(search))
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    users = session.exec(query).all()
    return users

@router.post("/users", response_model=UserAdmin)
def create_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
    user_in: UserCreate
):
    """
    Create a new user (admin only)
    """
    # Check if user already exists
    existing_user = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    # Create user
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=user_in.is_active,
        role=user_in.role
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return db_user

@router.get("/users/{user_id}", response_model=UserAdmin)
def get_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_users_access),
    user_id: int
):
    """
    Get user by ID (admin only)
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{user_id}", response_model=UserAdmin)
def update_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
    user_id: int,
    user_update: UserUpdate
):
    """
    Update user (admin only)
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only super admin can change roles
    if user_update.role and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Only super admin can change user roles"
        )
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user

@router.delete("/users/{user_id}")
def delete_user(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_super_admin),
    user_id: int
):
    """
    Delete user (super admin only)
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    session.delete(user)
    session.commit()
    
    return {"message": "User deleted successfully"}

@router.get("/users/me", response_model=UserAdmin)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's own profile
    """
    return current_user

@router.patch("/users/me", response_model=UserAdmin)
def update_current_user_profile(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    user_update: UserUpdate
):
    """
    Update current user's own profile (limited fields)
    """
    # Users can only update their email, not role or active status
    allowed_fields = {"email"}
    update_data = {k: v for k, v in user_update.dict(exclude_unset=True).items() if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    # Check if email is already taken
    if "email" in update_data:
        existing_user = session.exec(
            select(User).where(User.email == update_data["email"], User.id != current_user.id)
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already taken")
    
    # Update fields
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user