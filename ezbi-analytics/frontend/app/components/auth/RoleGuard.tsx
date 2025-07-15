'use client';

import { ReactNode } from 'react';
import { authService, UserRole, Permission } from '../../services/authService';

interface RoleGuardProps {
  children: ReactNode;
  requiredRoles?: UserRole[];
  requiredPermissions?: Permission[];
  requireAll?: boolean; // If true, user must have ALL permissions, if false, user needs ANY permission
  fallback?: ReactNode;
  showFallback?: boolean;
}

export default function RoleGuard({
  children,
  requiredRoles = [],
  requiredPermissions = [],
  requireAll = false,
  fallback = null,
  showFallback = true
}: RoleGuardProps) {
  const user = authService.getCurrentUser();

  if (!user) {
    return showFallback ? (
      fallback || (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded">
          <p className="text-red-400 text-sm">Authentication required</p>
        </div>
      )
    ) : null;
  }

  // Check role requirements
  if (requiredRoles.length > 0) {
    const hasRequiredRole = authService.hasAnyRole(requiredRoles);
    if (!hasRequiredRole) {
      return showFallback ? (
        fallback || (
          <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded">
            <p className="text-yellow-400 text-sm">
              Access denied. Required roles: {requiredRoles.join(', ')}
            </p>
          </div>
        )
      ) : null;
    }
  }

  // Check permission requirements
  if (requiredPermissions.length > 0) {
    const hasPermission = requireAll
      ? requiredPermissions.every(permission => authService.hasPermission(permission))
      : authService.hasAnyPermission(requiredPermissions);

    if (!hasPermission) {
      return showFallback ? (
        fallback || (
          <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded">
            <p className="text-yellow-400 text-sm">
              Access denied. Required permissions: {requiredPermissions.join(', ')}
            </p>
          </div>
        )
      ) : null;
    }
  }

  return <>{children}</>;
}

// Convenience components for specific roles
export function AdminOnly({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <RoleGuard requiredRoles={[UserRole.ADMIN]} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}

export function ManagerOrHigher({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <RoleGuard requiredRoles={[UserRole.ADMIN, UserRole.MANAGER]} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}

export function AnalystOrHigher({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <RoleGuard requiredRoles={[UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}

// Permission-based components
export function CanWriteDashboard({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <RoleGuard requiredPermissions={[Permission.WRITE_DASHBOARD]} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}

export function CanWriteAnalytics({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <RoleGuard requiredPermissions={[Permission.WRITE_ANALYTICS]} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}

export function CanManageUsers({ children, fallback }: { children: ReactNode; fallback?: ReactNode }) {
  return (
    <RoleGuard requiredPermissions={[Permission.USER_MANAGEMENT]} fallback={fallback}>
      {children}
    </RoleGuard>
  );
}