import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { AuthProvider } from '@/features/auth/AuthProvider';
import { useAuth } from '@/features/auth/useAuth';
import { Can } from '@/features/auth/Can';
import { setRefreshToken } from '@/lib/tokenStore';
import type { UserRead } from '@/features/auth/api';

const makeUser = (role: UserRead['role']): UserRead => ({
  id: 1, username: 'u', email: null, full_name: 'User Test',
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

function Harness() {
  const { user, isReady } = useAuth();
  if (!isReady) return <span>loading</span>;
  return (
    <div>
      <span data-testid="role">{user?.role ?? 'none'}</span>
      <Can resource="eleves" action="read">
        <span data-testid="can-read">READ</span>
      </Can>
      <Can resource="eleves" action="create">
        <span data-testid="can-create">CREATE</span>
      </Can>
    </div>
  );
}

function wrap(children: ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}

describe('<Can>', () => {
  beforeEach(() => {
    mockedMe.mockReset();
    setRefreshToken('RT-TEST');
  });

  it('ADMIN voit create et read', async () => {
    mockedMe.mockResolvedValue(makeUser('ADMIN'));
    render(wrap(<Harness />));
    expect(await screen.findByTestId('role')).toHaveTextContent('ADMIN');
    expect(screen.getByTestId('can-create')).toBeInTheDocument();
    expect(screen.getByTestId('can-read')).toBeInTheDocument();
  });

  it('LECTURE ne voit que read', async () => {
    mockedMe.mockResolvedValue(makeUser('LECTURE'));
    render(wrap(<Harness />));
    expect(await screen.findByTestId('role')).toHaveTextContent('LECTURE');
    expect(screen.getByTestId('can-read')).toBeInTheDocument();
    expect(screen.queryByTestId('can-create')).not.toBeInTheDocument();
  });

  it('CAISSE_FG ne voit ni read ni create sur eleves', async () => {
    mockedMe.mockResolvedValue(makeUser('CAISSE_FG'));
    render(wrap(<Harness />));
    expect(await screen.findByTestId('role')).toHaveTextContent('CAISSE_FG');
    expect(screen.queryByTestId('can-read')).not.toBeInTheDocument();
    expect(screen.queryByTestId('can-create')).not.toBeInTheDocument();
  });
});