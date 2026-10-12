import { afterEach, describe, expect, it } from 'vitest';
import type { AxiosRequestConfig, AxiosResponse } from 'axios';
import {
  apiClient, rawClient, resetRefreshState, onForceLogout,
} from '@/lib/apiClient';
import {
  getAccessToken, setAccessToken, getRefreshToken, setRefreshToken,
} from '@/lib/tokenStore';

type Adapter = NonNullable<AxiosRequestConfig['adapter']>;

interface CannedResponse {
  data: unknown;
  status?: number;
  headers?: Record<string, string>;
}

function adaptersFrom(
  rawHandler: (cfg: AxiosRequestConfig) => Promise<CannedResponse> | CannedResponse,
  apiHandler: (cfg: AxiosRequestConfig) => Promise<CannedResponse> | CannedResponse,
): { raw: Adapter; api: Adapter } {
  const wrap = (
    handler: (cfg: AxiosRequestConfig) => Promise<CannedResponse> | CannedResponse,
  ): Adapter => async (config) => {
    const r = await handler(config);
    const status = r.status ?? 200;
    const response: AxiosResponse = {
      data: r.data,
      status,
      statusText: status === 200 ? 'OK' : 'Error',
      headers: r.headers ?? {},
      config: config as never,
      request: {},
    };
    if (status >= 400) {
      const err = Object.assign(new Error(`HTTP ${status}`), {
        isAxiosError: true,
        config,
        response,
      });
      return Promise.reject(err);
    }
    return response;
  };
  return { raw: wrap(rawHandler), api: wrap(apiHandler) };
}

const originalApiAdapter = apiClient.defaults.adapter;
const originalRawAdapter = rawClient.defaults.adapter;

function readAuth(config: AxiosRequestConfig): string | null {
  const h = config.headers as unknown;
  if (!h) return null;
  if (typeof (h as { get?: unknown }).get === 'function') {
    return (h as { get: (k: string) => string | null }).get('Authorization');
  }
  const anyH = h as Record<string, string>;
  return anyH.Authorization ?? anyH.authorization ?? null;
}

afterEach(() => {
  apiClient.defaults.adapter = originalApiAdapter;
  rawClient.defaults.adapter = originalRawAdapter;
  setAccessToken(null);
  setRefreshToken(null);
  resetRefreshState();
});

describe('refresh single-flight', () => {
  it('3 requêtes concurrentes avec access périmé → 1 seul /auth/refresh', async () => {
    let refreshCalls = 0;
    let apiCalls = 0;

    const { raw, api } = adaptersFrom(
      (cfg) => {
        if (cfg.url?.includes('/auth/refresh')) {
          refreshCalls += 1;
          return new Promise((resolve) =>
            setTimeout(() => resolve({
              data: {
                access_token: 'AT-NEW',
                refresh_token: 'RT-NEW',
                token_type: 'bearer',
                user: { id: 1 },
              },
            }), 15),
          );
        }
        throw new Error(`raw call inattendue: ${cfg.url}`);
      },
      (cfg) => {
        apiCalls += 1;
        const auth = readAuth(cfg);
        if (auth === 'Bearer AT-NEW') return { data: { ok: true }, status: 200 };
        return { data: {}, status: 401 };
      },
    );
    rawClient.defaults.adapter = raw;
    apiClient.defaults.adapter = api;

    setRefreshToken('RT-OLD');
    setAccessToken('AT-OLD');

    const results = await Promise.all([
      apiClient.get('/eleves'),
      apiClient.get('/eleves'),
      apiClient.get('/eleves'),
    ]);

    expect(results).toHaveLength(3);
    expect(results.every((r) => r.status === 200)).toBe(true);
    expect(refreshCalls).toBe(1);
    expect(apiCalls).toBe(6);
    expect(getAccessToken()).toBe('AT-NEW');
  });

  it('/auth/refresh 401 → forceLogout, pas de retry infini', async () => {
    let refreshCalls = 0;
    let apiCalls = 0;
    let forcedLogout = 0;
    const unsub = onForceLogout(() => { forcedLogout += 1; });

    const { raw, api } = adaptersFrom(
      (cfg) => {
        if (cfg.url?.includes('/auth/refresh')) {
          refreshCalls += 1;
          return { data: {}, status: 401 };
        }
        throw new Error('raw inattendue');
      },
      (cfg) => {
        apiCalls += 1;
        void readAuth(cfg);
        return { data: {}, status: 401 };
      },
    );
    rawClient.defaults.adapter = raw;
    apiClient.defaults.adapter = api;

    setRefreshToken('RT-OLD');
    setAccessToken('AT-OLD');

    await expect(apiClient.get('/eleves')).rejects.toBeTruthy();

    expect(refreshCalls).toBe(1);
    expect(apiCalls).toBe(1);
    expect(forcedLogout).toBe(1);
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    unsub();
  });

  it('rotation : nouveau refresh_token stocké après /auth/refresh', async () => {
    const { raw, api } = adaptersFrom(
      (cfg) => {
        if (cfg.url?.includes('/auth/refresh')) {
          return {
            data: {
              access_token: 'AT-XYZ',
              refresh_token: 'RT-NEW',
              token_type: 'bearer',
              user: { id: 1 },
            },
          };
        }
        throw new Error('raw inattendue');
      },
      (cfg) => {
        const auth = readAuth(cfg);
        if (auth === 'Bearer AT-XYZ') return { data: { ok: true }, status: 200 };
        return { data: {}, status: 401 };
      },
    );
    rawClient.defaults.adapter = raw;
    apiClient.defaults.adapter = api;

    setRefreshToken('RT-OLD');
    setAccessToken('AT-OLD');

    await apiClient.get('/eleves');

    expect(getAccessToken()).toBe('AT-XYZ');
    expect(getRefreshToken()).toBe('RT-NEW');
  });

  it('un 403 ne déclenche pas de refresh', async () => {
    let refreshCalls = 0;
    const { raw, api } = adaptersFrom(
      () => { refreshCalls += 1; return { data: {}, status: 401 }; },
      () => ({ data: {}, status: 403 }),
    );
    rawClient.defaults.adapter = raw;
    apiClient.defaults.adapter = api;

    setRefreshToken('RT-OLD');
    setAccessToken('AT-OLD');

    await expect(apiClient.get('/users')).rejects.toMatchObject({
      response: { status: 403 },
    });
    expect(refreshCalls).toBe(0);
  });

  it('un 422 ne déclenche pas de refresh', async () => {
    let refreshCalls = 0;
    const { raw, api } = adaptersFrom(
      () => { refreshCalls += 1; return { data: {}, status: 401 }; },
      () => ({ data: {}, status: 422 }),
    );
    rawClient.defaults.adapter = raw;
    apiClient.defaults.adapter = api;

    setRefreshToken('RT-OLD');
    setAccessToken('AT-OLD');

    await expect(apiClient.post('/x', {})).rejects.toMatchObject({
      response: { status: 422 },
    });
    expect(refreshCalls).toBe(0);
  });

  it('un 500 ne déclenche pas de refresh', async () => {
    let refreshCalls = 0;
    const { raw, api } = adaptersFrom(
      () => { refreshCalls += 1; return { data: {}, status: 401 }; },
      () => ({ data: {}, status: 500 }),
    );
    rawClient.defaults.adapter = raw;
    apiClient.defaults.adapter = api;

    setRefreshToken('RT-OLD');
    setAccessToken('AT-OLD');

    await expect(apiClient.get('/x')).rejects.toMatchObject({
      response: { status: 500 },
    });
    expect(refreshCalls).toBe(0);
  });
});