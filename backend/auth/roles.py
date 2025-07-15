from fastapi import Depends, HTTPException, status
from models.user import User, UserRole
from auth.dependencies import get_current_user

def get_current_active_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user
