import type { ReactNode } from 'react';
import { useAuth } from './useAuth';
import type { Action, Resource } from '@/lib/permissions';

interface Props {
  resource: Resource;
  action: Action;
  children: ReactNode;
  fallback?: ReactNode;
}

export function Can({ resource, action, children, fallback = null }: Props) {
  const { can } = useAuth();
  return can(resource, action) ? <>{children}</> : <>{fallback}</>;
}