/* ============================================================
   GoldenHour — AuthGuard
   Redirects unauthenticated users to /auth, preserving the
   intended destination so they can be sent back after login.
   ============================================================ */
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSessionStore } from '../../store/session';
import type { Role } from '../../types/api';

interface AuthGuardProps {
  children: React.ReactNode;
  /** If provided, only this role (or admin) may access the route */
  requiredRole?: Role;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ children, requiredRole }) => {
  const location = useLocation();
  const { isAuthenticated, user } = useSessionStore();

  if (!isAuthenticated || !user) {
    // Preserve the intended destination so AuthPage can redirect back
    const roleHint = requiredRole ? `?role=${requiredRole}` : '';
    return (
      <Navigate
        to={`/auth${roleHint}`}
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // Role check: admin can always access everything
  if (requiredRole && user.role !== requiredRole && user.role !== 'admin') {
    // Wrong role — send to their own dashboard
    const dashboardMap: Record<Role, string> = {
      donor: '/donor',
      recipient: '/org',
      driver: '/driver',
      admin: '/ops',
    };
    return <Navigate to={dashboardMap[user.role] ?? '/'} replace />;
  }

  return <>{children}</>;
};
