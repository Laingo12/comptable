import {
  useCallback, useEffect, useMemo, useState, type ReactNode,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { authApi, type TokenPair, type UserRead } from './api';
import {
  getAccessToken, setAccessToken, setRefreshToken, getRefreshToken,
} from '@/lib/tokenStore';
import { onForceLogout } from '@/lib/apiClient';
import { hasPermission, type Action, type Resource, type Role } from '@/lib/permissions';
import { AuthContext, type AuthContextValue } from './authContext';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserRead | null>(null);
  const [isReady, setReady] = useState(false);
  const queryClient = useQueryClient();

  const clear = useCallback(() => {
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    queryClient.clear();
  }, [queryClient]);

  useEffect(() => onForceLogout(clear), [clear]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        if (!getAccessToken() && !getRefreshToken()) return;
        const me = await authApi.me();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) clear();
      } finally {
        if (!cancelled) setReady(true);
      }
    })();
    return () => { cancelled = true; };
  }, [clear]);

  const login = useCallback(
    async (input: { username: string; password: string }) => {
      const pair: TokenPair = await authApi.login(input);
      setAccessToken(pair.access_token);
      setRefreshToken(pair.refresh_token);
      setUser(pair.user);
    },
    [],
  );

  const logout = useCallback(async () => {
    const rt = getRefreshToken();
    try { if (rt) await authApi.logout(rt); } catch { /* ignore */ }
    clear();
  }, [clear]);

  const can = useCallback(
    (resource: Resource, action: Action) =>
      hasPermission(user?.role as Role | undefined, resource, action),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({ user, isReady, isAuthenticated: user !== null, login, logout, can }),
    [user, isReady, login, logout, can],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}