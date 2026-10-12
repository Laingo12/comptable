import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { EleveForm } from '@/features/eleves/components/EleveForm';

vi.mock('@/features/familles/api', () => ({
  famillesApi: {
    list: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 }),
  },
}));

function renderForm(props: Partial<React.ComponentProps<typeof EleveForm>> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <EleveForm
          onSubmit={() => undefined}
          onCancel={() => undefined}
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('<EleveForm>', () => {
  it('affiche les erreurs de validation sur champs requis', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(screen.getByRole('button', { name: /créer l'élève/i }));

    const alerts = await screen.findAllByRole('alert');
    const texts = alerts.map((a) => a.textContent ?? '');
    expect(texts.some((t) => /nom requis/i.test(t))).toBe(true);
    expect(texts.some((t) => /prénoms requis/i.test(t))).toBe(true);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('soumet les valeurs converties (sexe "" → null, famille "" → null)', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    // Les labels contiennent un astérisque requis (`Nom *`) :
    // on cible par regex pour tolérer cet indicateur.
    await user.type(screen.getByLabelText(/^Nom/i), 'Rakoto');
    await user.type(screen.getByLabelText(/^Prénoms/i), 'Naina');
    await user.click(screen.getByRole('button', { name: /créer l'élève/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      nom: 'Rakoto',
      prenoms: 'Naina',
      sexe: null,
      date_naissance: null,
      famille_id: null,
    });
  });

  it('affiche les erreurs 422 propagées par le parent', async () => {
    renderForm({
      fieldErrors: { nom: 'Ce nom est déjà utilisé.' },
    });
    expect(await screen.findByRole('alert')).toHaveTextContent('Ce nom est déjà utilisé.');
  });

  it('en mode édition, le matricule est en lecture seule', () => {
    renderForm({
      initial: {
        id: 1, matricule: 'SK-2026-0001', nom: 'Rakoto', prenoms: 'Naina',
        sexe: 'M', date_naissance: '2018-05-01', famille_id: null,
        version: 1, created_at: '', updated_at: '',
      },
    });
    const input = screen.getByLabelText('Matricule');
    expect(input).toHaveAttribute('readonly');
  });
});