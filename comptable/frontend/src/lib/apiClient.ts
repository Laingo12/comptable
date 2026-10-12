import axios, { AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import {
  getAccessToken, setAccessToken, setRefreshToken, getRefreshToken,
} from './tokenStore';
import type { components } from '@/types/api';

type TokenPair = components['schemas']['TokenPair'];

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export const rawClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

const logoutListeners = new Set<() => void>();
export function onForceLogout(cb: () => void): () => void {
  logoutListeners.add(cb);
  return () => { logoutListeners.delete(cb); };
}
function forceLogout(): void {
  setAccessToken(null);
  setRefreshToken(null);
  for (const l of logoutListeners) l();
}

let refreshPromise: Promise<string> | null = null;

async function performRefresh(): Promise<string> {
  const rt = getRefreshToken();
  if (!rt) throw new Error('no_refresh_token');
  const res = await rawClient.post<TokenPair>('/auth/refresh', {
    refresh_token: rt,
  });
  setAccessToken(res.data.access_token);
  setRefreshToken(res.data.refresh_token);
  return res.data.access_token;
}

function refreshSingleFlight(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.set('Authorization', `Bearer ${token}`);
  return config;
});

interface RetryConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

apiClient.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const cfg = error.config as RetryConfig | undefined;
    const status = error.response?.status;
    const isRefreshCall = cfg?.url?.includes('/auth/refresh');

    if (status === 401 && cfg && !cfg._retried && !isRefreshCall) {
      cfg._retried = true;
      try {
        const newToken = await refreshSingleFlight();
        cfg.headers.set('Authorization', `Bearer ${newToken}`);
        return apiClient.request(cfg);
      } catch {
        forceLogout();
      }
    }
    return Promise.reject(error);
  },
);

export function resetRefreshState(): void {
  refreshPromise = null;
}