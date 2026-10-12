import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './useAuth';
import type { Action, Resource } from '@/lib/permissions';

interface Props {
  resource?: Resource;
  action?: Action;
}

export function ProtectedRoute({ resource, action }: Props) {
  const { isReady, isAuthenticated, can } = useAuth();
  const location = useLocation();

  if (!isReady) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Chargement…
      </div>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (resource && action && !can(resource, action)) {
    return <Navigate to="/403" replace />;
  }
  return <Outlet />;
}