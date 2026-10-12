import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { PrelevementForm } from '@/features/prelevements/components/PrelevementForm';

vi.mock('@/features/associes/api', () => ({
  associesApi: {
    list: vi.fn().mockResolvedValue([
      {
        id: 1,
        nom: 'Jessy',
        plafond_mensuel: 5_000_000,
        versement_fixe_mensuel: 3_000_000,
        versement_fixe_mois_debut_ordre: 2,
        is_active: true,
        version: 1,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
      },
    ]),
  },
}));

vi.mock('@/features/referentiels/api', () => ({
  referentielsApi: {
    modesPaiement: vi.fn().mockResolvedValue([
      { id: 1, code: 'ESPECES', libelle: 'Espèces', ordre: 1 },
    ]),
  },
}));

function renderForm(props: Partial<React.ComponentProps<typeof PrelevementForm>> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <PrelevementForm
          onSubmit={() => undefined}
          onCancel={() => undefined}
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

/** Attend que le select Associé contienne au moins une option métier. */
async function waitForAssociesOption(): Promise<void> {
  await waitFor(
    () => {
      const select = screen.getByLabelText(/^Associé/i) as HTMLSelectElement;
      // 1 = placeholder "— Choisir —", 2 = Jessy
      expect(select.options.length).toBeGreaterThan(1);
    },
    { timeout: 5000 },
  );
}

describe('<PrelevementForm>', () => {
  it('affiche les erreurs de validation sur champs requis', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(screen.getByRole('button', { name: /enregistrer le prélèvement/i }));

    const alerts = await screen.findAllByRole('alert');
    const texts = alerts.map((a) => a.textContent ?? '');
    expect(texts.some((t) => /associé requis/i.test(t))).toBe(true);
    expect(texts.some((t) => /montant strictement positif/i.test(t))).toBe(true);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('soumet un prélèvement valide', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await waitForAssociesOption();

    await user.selectOptions(screen.getByLabelText(/^Associé/i), '1');
    await user.clear(screen.getByLabelText(/^Montant/i));
    await user.type(screen.getByLabelText(/^Montant/i), '50000');
    await user.type(screen.getByLabelText(/^Destinataire/i), 'FOURNITURES LUCKAS');
    await user.type(screen.getByLabelText(/^Motif/i), 'Fournitures');

    await user.click(screen.getByRole('button', { name: /enregistrer le prélèvement/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      associe_id: 1,
      type: 'RETRAIT',
      montant: 50_000,
      destinataire: 'FOURNITURES LUCKAS',
      motif: 'Fournitures',
      date_a_completer: false,
    });
  });

  it('convertit destinataire/motif vides en null', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await waitForAssociesOption();

    await user.selectOptions(screen.getByLabelText(/^Associé/i), '1');
    await user.clear(screen.getByLabelText(/^Montant/i));
    await user.type(screen.getByLabelText(/^Montant/i), '1000');
    await user.click(screen.getByRole('button', { name: /enregistrer le prélèvement/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      destinataire: null,
      motif: null,
      reference: null,
    });
  });
});