"""
Global permission system for system-wide access control
"""

from typing import Set
from models.user import UserRole

# Global permissions
GLOBAL_PERMISSIONS = {
    UserRole.SUPER_ADMIN: {
        'users:read', 'users:create', 'users:update', 'users:delete',
        'system:read', 'system:update', 'system:monitor',
        'projects:read_all', 'projects:manage_all'
    },
    UserRole.ADMIN: {
        'users:read', 'users:create',
        'system:read', 'system:monitor',
        'projects:read_all'
    },
    UserRole.USER: {
        'profile:read', 'profile:update',
        'projects:create', 'projects:own'
    }
}

class GlobalPermissionManager:
    """Manage global permissions for users"""
    
    @staticmethod
    def get_permissions(role: UserRole) -> Set[str]:
        """Get all permissions for a role"""
        return GLOBAL_PERMISSIONS.get(role, set())
    
    @staticmethod
    def has_permission(user_role: UserRole, permission: str) -> bool:
        """Check if a role has a specific permission"""
        permissions = GlobalPermissionManager.get_permissions(user_role)
        return permission in permissions
    
    @staticmethod
    def can_access_users_section(user_role: UserRole) -> bool:
        """Check if user can access users management section"""
        return GlobalPermissionManager.has_permission(user_role, 'users:read')
    
    @staticmethod
    def can_manage_users(user_role: UserRole) -> bool:
        """Check if user can create/edit/delete users"""
        return GlobalPermissionManager.has_permission(user_role, 'users:create')
    
    @staticmethod
    def can_delete_users(user_role: UserRole) -> bool:
        """Check if user can delete users"""
        return GlobalPermissionManager.has_permission(user_role, 'users:delete')
    
    @staticmethod
    def can_access_monitoring(user_role: UserRole) -> bool:
        """Check if user can access monitoring/supervision section"""
        return GlobalPermissionManager.has_permission(user_role, 'system:monitor')
    
    @staticmethod
    def can_manage_system(user_role: UserRole) -> bool:
        """Check if user can modify system settings"""
        return GlobalPermissionManager.has_permission(user_role, 'system:update')