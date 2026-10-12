import { createContext } from 'react';
import type { UserRead } from './api';
import type { Action, Resource } from '@/lib/permissions';

export interface AuthContextValue {
  user: UserRead | null;
  isReady: boolean;
  isAuthenticated: boolean;
  login: (input: { username: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  can: (resource: Resource, action: Action) => boolean;
}

export const AuthContext = createContext<AuthContextValue | null>(null);