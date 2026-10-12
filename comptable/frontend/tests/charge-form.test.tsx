import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { ChargeForm } from '@/features/charges/components/ChargeForm';

vi.mock('@/features/referentiels/api', () => ({
  referentielsApi: {
    moisScolaires: vi.fn().mockResolvedValue([
      { id: 10, code: '2026-09', libelle: 'Septembre 2026', ordre: 1,
        date_debut: '2026-09-01', date_fin: '2026-09-30',
        date_limite_paiement: '2026-09-05', est_scolaire: true, annee_scolaire_id: 1 },
    ]),
    modesPaiement: vi.fn().mockResolvedValue([
      { id: 1, code: 'ESPECES', libelle: 'Espèces', ordre: 1 },
    ]),
    chargesCatalogue: vi.fn().mockResolvedValue([
      { id: 7, annee_scolaire_id: 1, code: 'JIRAMA', libelle: 'JIRAMA',
        categorie: 'VARIABLE', montant_previsionnel: 0, is_active: true, version: 1 },
    ]),
  },
}));

function renderForm(props: Partial<React.ComponentProps<typeof ChargeForm>> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ChargeForm
          onSubmit={() => undefined}
          onCancel={() => undefined}
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('<ChargeForm>', () => {
  it('affiche les erreurs sur champs requis', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(screen.getByRole('button', { name: /enregistrer la charge/i }));

    const alerts = await screen.findAllByRole('alert');
    const texts = alerts.map((a) => a.textContent ?? '');
    expect(texts.some((t) => /libellé requis/i.test(t))).toBe(true);
    expect(texts.some((t) => /montant strictement positif/i.test(t))).toBe(true);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("pré-remplit libellé et catégorie depuis le catalogue", async () => {
    const user = userEvent.setup();
    renderForm();

    await screen.findByRole('option', { name: /JIRAMA/i });

    await user.selectOptions(
      screen.getByLabelText(/^Catalogue/i),
      '7',
    );

    await waitFor(() => {
      const libelle = screen.getByLabelText(/^Libellé/i) as HTMLInputElement;
      expect(libelle.value).toBe('JIRAMA');
    });
    const cat = screen.getByLabelText(/^Catégorie/i) as HTMLSelectElement;
    expect(cat.value).toBe('VARIABLE');
  });

  it('soumet une charge valide', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    // Attendre le catalogue puis pré-remplir
    await screen.findByRole('option', { name: /JIRAMA/i });
    await user.selectOptions(screen.getByLabelText(/^Catalogue/i), '7');

    // Saisir le montant
    await user.clear(screen.getByLabelText(/^Montant/i));
    await user.type(screen.getByLabelText(/^Montant/i), '45000');

    await user.click(screen.getByRole('button', { name: /enregistrer la charge/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      libelle: 'JIRAMA',
      categorie: 'VARIABLE',
      montant: 45_000,
      date_a_completer: false,
    });
  });
});