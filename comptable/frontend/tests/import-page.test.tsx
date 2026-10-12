import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { ImportPage } from '@/features/import/pages/ImportPage';

// --- Mocks --------------------------------------------------------------

const { mockAuth } = vi.hoisted(() => ({
  mockAuth: { can: vi.fn().mockReturnValue(true) },
}));

vi.mock('@/features/auth/useAuth', () => ({
  useAuth: () => mockAuth,
}));

const { mockImportReport } = vi.hoisted(() => ({
  mockImportReport: {
    file_name: 'ecole.xlsx',
    dry_run: true,
    sheets: [
      { sheet: 'SUIVI ECOLAGES', total: 10, created: 9, skipped: 0, errors: 1,
        warnings: ['L5: élève introuvable (SK-2026-9999)'] },
      { sheet: 'DROITS & FG', total: 5, created: 5, skipped: 0, errors: 0, warnings: [] },
    ],
    total_created: 14,
    total_skipped: 0,
    total_errors: 1,
    started_at: '2026-10-12T08:00:00Z',
    finished_at: '2026-10-12T08:00:02Z',
  },
}));

vi.mock('@/features/import/api', () => ({
  importApi: {
    importExcel: vi.fn().mockResolvedValue(mockImportReport),
    listLignes: vi.fn().mockResolvedValue([]),
  },
}));

// --- Helpers ------------------------------------------------------------

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ImportPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function makeXlsxFile(name = 'ecole.xlsx'): File {
  // Contenu arbitraire (le backend n'est pas appelé dans ce test).
  return new File([new Uint8Array([0x50, 0x4b, 0x03, 0x04])], name, {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
}

// --- Tests --------------------------------------------------------------

describe('<ImportPage>', () => {
  it('refuse un fichier avec une mauvaise extension', async () => {
    const user = userEvent.setup();
    renderPage();

    const input = screen.getByLabelText(/fichier excel à importer/i) as HTMLInputElement;
    const badFile = new File(['abc'], 'ecole.csv', { type: 'text/csv' });

    await user.upload(input, badFile);

    // Le fichier n'est pas retenu
    expect(screen.getByText(/formats acceptés/i)).toBeInTheDocument();
    expect(screen.queryByText('ecole.csv')).not.toBeInTheDocument();
  });

  it('affiche le rapport en mode simulation', async () => {
    const user = userEvent.setup();
    renderPage();

    const input = screen.getByLabelText(/fichier excel à importer/i) as HTMLInputElement;
    await user.upload(input, makeXlsxFile());

    // Sim par défaut (dryRun=true)
    const btn = screen.getByRole('button', { name: /simuler l'import/i });
    await user.click(btn);

    await waitFor(() => {
      expect(screen.getByText(/rapport d'import — ecole.xlsx/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/14/)).toBeInTheDocument();
    expect(screen.getByText(/SUIVI ECOLAGES/)).toBeInTheDocument();
    expect(screen.getByText(/DROITS & FG/)).toBeInTheDocument();
    expect(screen.getByText(/Simulation : aucune donnée n'a été écrite/i)).toBeInTheDocument();
  });

  it("n'affiche pas l'upload si l'utilisateur n'a pas la permission", () => {
    mockAuth.can.mockReturnValueOnce(false);
    renderPage();
    expect(screen.getByText(/accès restreint/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/fichier excel à importer/i)).not.toBeInTheDocument();
  });
});