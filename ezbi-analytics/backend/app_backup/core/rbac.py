"""
Role-Based Access Control (RBAC) System for Manufacturing Analytics
Provides comprehensive role and permission management for production systems
"""

from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import structlog

from app.models.user import User, Role, Permission
from app.core.database import get_db_session
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = structlog.get_logger()

class RoleType(Enum):
    """Standard role types for manufacturing analytics"""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    SALES_USER = "sales_user"
    ACCOUNTING_USER = "accounting_user"
    OPERATIONS_USER = "operations_user"
    FINANCE_USER = "finance_user"
    HR_USER = "hr_user"
    VIEWER = "viewer"

class PermissionType(Enum):
    """Permission types for manufacturing operations"""
    # Read permissions
    SALES_READ = "sales_read"
    ACCOUNTING_READ = "accounting_read"
    OPERATIONS_READ = "operations_read"
    FINANCE_READ = "finance_read"
    HR_READ = "hr_read"
    ANALYTICS_READ = "analytics_read"
    
    # Write permissions
    SALES_WRITE = "sales_write"
    ACCOUNTING_WRITE = "accounting_write"
    OPERATIONS_WRITE = "operations_write"
    FINANCE_WRITE = "finance_write"
    HR_WRITE = "hr_write"
    
    # Admin permissions
    ADMIN_ACCESS = "admin_access"
    MANAGER_ACCESS = "manager_access"
    ANALYST_ACCESS = "analyst_access"
    
    # System permissions
    SYSTEM_CONFIG = "system_config"
    USER_MANAGEMENT = "user_management"
    AUDIT_LOG_ACCESS = "audit_log_access"
    
    # Special permissions
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    EXPORT_DATA = "export_data"
    DELETE_RECORDS = "delete_records"

@dataclass
class AccessContext:
    """Context for access control decisions"""
    user: User
    resource_type: str
    resource_id: Optional[str] = None
    action: str = "read"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_data: Optional[Dict] = None

class RBACManager:
    """Role-Based Access Control Manager"""
    
    def __init__(self):
        self.role_hierarchy = {
            RoleType.ADMIN: 100,
            RoleType.MANAGER: 80,
            RoleType.ANALYST: 60,
            RoleType.SALES_USER: 40,
            RoleType.ACCOUNTING_USER: 40,
            RoleType.OPERATIONS_USER: 40,
            RoleType.FINANCE_USER: 40,
            RoleType.HR_USER: 40,
            RoleType.VIEWER: 20,
        }
        
        self.default_role_permissions = {
            RoleType.ADMIN: [
                PermissionType.ADMIN_ACCESS,
                PermissionType.MANAGER_ACCESS,
                PermissionType.ANALYST_ACCESS,
                PermissionType.SALES_READ, PermissionType.SALES_WRITE,
                PermissionType.ACCOUNTING_READ, PermissionType.ACCOUNTING_WRITE,
                PermissionType.OPERATIONS_READ, PermissionType.OPERATIONS_WRITE,
                PermissionType.FINANCE_READ, PermissionType.FINANCE_WRITE,
                PermissionType.HR_READ, PermissionType.HR_WRITE,
                PermissionType.ANALYTICS_READ,
                PermissionType.SYSTEM_CONFIG,
                PermissionType.USER_MANAGEMENT,
                PermissionType.AUDIT_LOG_ACCESS,
                PermissionType.SENSITIVE_DATA_ACCESS,
                PermissionType.EXPORT_DATA,
                PermissionType.DELETE_RECORDS,
            ],
            RoleType.MANAGER: [
                PermissionType.MANAGER_ACCESS,
                PermissionType.ANALYST_ACCESS,
                PermissionType.SALES_READ, PermissionType.SALES_WRITE,
                PermissionType.ACCOUNTING_READ, PermissionType.ACCOUNTING_WRITE,
                PermissionType.OPERATIONS_READ, PermissionType.OPERATIONS_WRITE,
                PermissionType.FINANCE_READ, PermissionType.FINANCE_WRITE,
                PermissionType.HR_READ, PermissionType.HR_WRITE,
                PermissionType.ANALYTICS_READ,
                PermissionType.EXPORT_DATA,
            ],
            RoleType.ANALYST: [
                PermissionType.ANALYST_ACCESS,
                PermissionType.SALES_READ,
                PermissionType.ACCOUNTING_READ,
                PermissionType.OPERATIONS_READ,
                PermissionType.FINANCE_READ,
                PermissionType.HR_READ,
                PermissionType.ANALYTICS_READ,
                PermissionType.EXPORT_DATA,
            ],
            RoleType.SALES_USER: [
                PermissionType.SALES_READ,
                PermissionType.SALES_WRITE,
                PermissionType.ANALYTICS_READ,
            ],
            RoleType.ACCOUNTING_USER: [
                PermissionType.ACCOUNTING_READ,
                PermissionType.ACCOUNTING_WRITE,
                PermissionType.ANALYTICS_READ,
            ],
            RoleType.OPERATIONS_USER: [
                PermissionType.OPERATIONS_READ,
                PermissionType.OPERATIONS_WRITE,
                PermissionType.ANALYTICS_READ,
            ],
            RoleType.FINANCE_USER: [
                PermissionType.FINANCE_READ,
                PermissionType.FINANCE_WRITE,
                PermissionType.ANALYTICS_READ,
                PermissionType.SENSITIVE_DATA_ACCESS,
            ],
            RoleType.HR_USER: [
                PermissionType.HR_READ,
                PermissionType.HR_WRITE,
                PermissionType.ANALYTICS_READ,
                PermissionType.SENSITIVE_DATA_ACCESS,
            ],
            RoleType.VIEWER: [
                PermissionType.SALES_READ,
                PermissionType.OPERATIONS_READ,
                PermissionType.ANALYTICS_READ,
            ],
        }
    
    async def check_permission(self, context: AccessContext, required_permission: PermissionType) -> bool:
        """Check if user has required permission for the given context"""
        try:
            # Get user with roles and permissions
            async with get_db_session() as db:
                user = await db.execute(
                    select(User)
                    .options(selectinload(User.roles).selectinload(Role.permissions))
                    .options(selectinload(User.permissions))
                    .where(User.id == context.user.id)
                )
                user = user.scalar_one()
                
                # Check if user is active
                if not user.is_active or user.is_locked:
                    return False
                
                # Check direct permissions
                user_permissions = {perm.name for perm in user.permissions}
                if required_permission.value in user_permissions:
                    return True
                
                # Check role-based permissions
                for role in user.roles:
                    role_permissions = {perm.name for perm in role.permissions}
                    if required_permission.value in role_permissions:
                        return True
                
                # Check against default role permissions
                for role in user.roles:
                    role_type = RoleType(role.name)
                    if role_type in self.default_role_permissions:
                        default_permissions = self.default_role_permissions[role_type]
                        if required_permission in default_permissions:
                            return True
                
                return False
                
        except Exception as e:
            logger.error("Permission check failed", error=str(e), user_id=context.user.id)
            return False
    
    async def check_multiple_permissions(self, context: AccessContext, required_permissions: List[PermissionType]) -> bool:
        """Check if user has any of the required permissions"""
        for permission in required_permissions:
            if await self.check_permission(context, permission):
                return True
        return False
    
    async def get_user_permissions(self, user: User) -> Set[str]:
        """Get all permissions for a user"""
        try:
            async with get_db_session() as db:
                user_with_perms = await db.execute(
                    select(User)
                    .options(selectinload(User.roles).selectinload(Role.permissions))
                    .options(selectinload(User.permissions))
                    .where(User.id == user.id)
                )
                user_with_perms = user_with_perms.scalar_one()
                
                permissions = set()
                
                # Add direct permissions
                for perm in user_with_perms.permissions:
                    permissions.add(perm.name)
                
                # Add role-based permissions
                for role in user_with_perms.roles:
                    for perm in role.permissions:
                        permissions.add(perm.name)
                
                # Add default role permissions
                for role in user_with_perms.roles:
                    try:
                        role_type = RoleType(role.name)
                        if role_type in self.default_role_permissions:
                            for perm in self.default_role_permissions[role_type]:
                                permissions.add(perm.value)
                    except ValueError:
                        # Role type not in enum, skip
                        continue
                
                return permissions
                
        except Exception as e:
            logger.error("Failed to get user permissions", error=str(e), user_id=user.id)
            return set()
    
    async def get_user_role_level(self, user: User) -> int:
        """Get user's highest role level"""
        try:
            async with get_db_session() as db:
                user_with_roles = await db.execute(
                    select(User)
                    .options(selectinload(User.roles))
                    .where(User.id == user.id)
                )
                user_with_roles = user_with_roles.scalar_one()
                
                max_level = 0
                for role in user_with_roles.roles:
                    try:
                        role_type = RoleType(role.name)
                        level = self.role_hierarchy.get(role_type, 0)
                        max_level = max(max_level, level)
                    except ValueError:
                        # Role type not in enum, skip
                        continue
                
                return max_level
                
        except Exception as e:
            logger.error("Failed to get user role level", error=str(e), user_id=user.id)
            return 0
    
    async def can_access_resource(self, context: AccessContext, resource_permissions: Dict[str, List[PermissionType]]) -> bool:
        """Check if user can access a specific resource based on action"""
        action = context.action.lower()
        
        # Get required permissions for this action
        required_permissions = resource_permissions.get(action, [])
        
        # If no specific permissions required, allow access
        if not required_permissions:
            return True
        
        # Check if user has any of the required permissions
        return await self.check_multiple_permissions(context, required_permissions)
    
    async def filter_accessible_resources(self, user: User, resources: List[Dict], resource_type: str) -> List[Dict]:
        """Filter resources based on user permissions"""
        accessible_resources = []
        user_permissions = await self.get_user_permissions(user)
        
        for resource in resources:
            # Define resource-specific access rules
            can_access = True
            
            if resource_type == "financial_data":
                # Financial data requires special permission
                if not any(perm in user_permissions for perm in [
                    PermissionType.FINANCE_READ.value,
                    PermissionType.ADMIN_ACCESS.value,
                    PermissionType.MANAGER_ACCESS.value
                ]):
                    can_access = False
            
            elif resource_type == "hr_data":
                # HR data requires special permission
                if not any(perm in user_permissions for perm in [
                    PermissionType.HR_READ.value,
                    PermissionType.ADMIN_ACCESS.value,
                    PermissionType.MANAGER_ACCESS.value
                ]):
                    can_access = False
            
            elif resource_type == "sensitive_data":
                # Sensitive data requires explicit permission
                if PermissionType.SENSITIVE_DATA_ACCESS.value not in user_permissions:
                    can_access = False
            
            if can_access:
                accessible_resources.append(resource)
        
        return accessible_resources
    
    async def create_default_roles_and_permissions(self):
        """Create default roles and permissions in the database"""
        try:
            async with get_db_session() as db:
                # Create permissions
                permissions_created = 0
                for perm_type in PermissionType:
                    # Check if permission exists
                    result = await db.execute(
                        select(Permission).where(Permission.name == perm_type.value)
                    )
                    existing_perm = result.scalar_one_or_none()
                    
                    if not existing_perm:
                        # Create permission
                        permission = Permission(
                            name=perm_type.value,
                            display_name=perm_type.value.replace("_", " ").title(),
                            description=f"Permission for {perm_type.value}",
                            category=perm_type.value.split("_")[0],
                            action=perm_type.value.split("_")[-1] if "_" in perm_type.value else "access",
                            is_system=True
                        )
                        db.add(permission)
                        permissions_created += 1
                
                await db.commit()
                
                # Create roles
                roles_created = 0
                for role_type in RoleType:
                    # Check if role exists
                    result = await db.execute(
                        select(Role).where(Role.name == role_type.value)
                    )
                    existing_role = result.scalar_one_or_none()
                    
                    if not existing_role:
                        # Create role
                        role = Role(
                            name=role_type.value,
                            display_name=role_type.value.replace("_", " ").title(),
                            description=f"Default {role_type.value} role",
                            level=self.role_hierarchy.get(role_type, 0),
                            is_system=True
                        )
                        db.add(role)
                        roles_created += 1
                
                await db.commit()
                
                # Assign permissions to roles
                for role_type, permissions in self.default_role_permissions.items():
                    role_result = await db.execute(
                        select(Role).where(Role.name == role_type.value)
                    )
                    role = role_result.scalar_one()
                    
                    for perm_type in permissions:
                        perm_result = await db.execute(
                            select(Permission).where(Permission.name == perm_type.value)
                        )
                        permission = perm_result.scalar_one()
                        
                        # Check if permission is already assigned to role
                        if permission not in role.permissions:
                            role.permissions.append(permission)
                
                await db.commit()
                
                logger.info(
                    "Default roles and permissions created",
                    permissions_created=permissions_created,
                    roles_created=roles_created
                )
                
        except Exception as e:
            logger.error("Failed to create default roles and permissions", error=str(e))
            raise

# Global RBAC manager instance
rbac_manager = RBACManager()

# Convenience functions for common permission checks
async def check_manufacturing_access(user: User, module: str, action: str = "read") -> bool:
    """Check access to manufacturing modules"""
    context = AccessContext(
        user=user,
        resource_type="manufacturing",
        action=action
    )
    
    permission_map = {
        "sales": PermissionType.SALES_READ if action == "read" else PermissionType.SALES_WRITE,
        "accounting": PermissionType.ACCOUNTING_READ if action == "read" else PermissionType.ACCOUNTING_WRITE,
        "operations": PermissionType.OPERATIONS_READ if action == "read" else PermissionType.OPERATIONS_WRITE,
        "finance": PermissionType.FINANCE_READ if action == "read" else PermissionType.FINANCE_WRITE,
        "hr": PermissionType.HR_READ if action == "read" else PermissionType.HR_WRITE,
    }
    
    required_permission = permission_map.get(module)
    if not required_permission:
        return False
    
    return await rbac_manager.check_permission(context, required_permission)

async def check_admin_access(user: User) -> bool:
    """Check if user has admin access"""
    context = AccessContext(user=user, resource_type="admin")
    return await rbac_manager.check_permission(context, PermissionType.ADMIN_ACCESS)

async def check_manager_access(user: User) -> bool:
    """Check if user has manager access"""
    context = AccessContext(user=user, resource_type="manager")
    return await rbac_manager.check_permission(context, PermissionType.MANAGER_ACCESS)

async def check_sensitive_data_access(user: User) -> bool:
    """Check if user can access sensitive data"""
    context = AccessContext(user=user, resource_type="sensitive_data")
    return await rbac_manager.check_permission(context, PermissionType.SENSITIVE_DATA_ACCESS)

async def check_export_permission(user: User) -> bool:
    """Check if user can export data"""
    context = AccessContext(user=user, resource_type="export")
    return await rbac_manager.check_permission(context, PermissionType.EXPORT_DATA)