import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/features/auth/AuthProvider';
import { ProtectedRoute } from '@/features/auth/ProtectedRoute';
import { setRefreshToken } from '@/lib/tokenStore';
import type { UserRead } from '@/features/auth/api';

const makeUser = (role: UserRead['role']): UserRead => ({
  id: 1, username: 'u', email: null, full_name: 'U',
  role, is_active: true, last_login_at: null, created_at: '2026-01-01T00:00:00Z',
});

const mockedMe = vi.fn();

vi.mock('@/features/auth/api', () => ({
  authApi: {
    me: () => mockedMe(),
    login: vi.fn(),
    logout: vi.fn(),
  },
}));

function renderAt(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div data-testid="login">login</div>} />
            <Route path="/403" element={<div data-testid="forbidden">forbidden</div>} />
            <Route element={<ProtectedRoute />}>
              <Route path="/dashboard" element={<div data-testid="dash">dash</div>} />
            </Route>
            <Route element={<ProtectedRoute resource="eleves" action="read" />}>
              <Route path="/eleves" element={<div data-testid="eleves">eleves</div>} />
            </Route>
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    mockedMe.mockReset();
    sessionStorage.clear();
  });

  it('non authentifié → redirige vers /login', async () => {
    renderAt('/dashboard');
    expect(await screen.findByTestId('login')).toBeInTheDocument();
    expect(screen.queryByTestId('dash')).not.toBeInTheDocument();
  });

  it('authentifié sans permission → redirige vers /403', async () => {
    setRefreshToken('RT-TEST');
    mockedMe.mockResolvedValue(makeUser('CAISSE_FG'));
    renderAt('/eleves');
    expect(await screen.findByTestId('forbidden')).toBeInTheDocument();
    expect(screen.queryByTestId('eleves')).not.toBeInTheDocument();
  });

  it('authentifié avec permission → affiche la page', async () => {
    setRefreshToken('RT-TEST');
    mockedMe.mockResolvedValue(makeUser('LECTURE'));
    renderAt('/eleves');
    expect(await screen.findByTestId('eleves')).toBeInTheDocument();
  });
});