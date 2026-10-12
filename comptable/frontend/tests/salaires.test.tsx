import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { PaiementSalaireForm } from '@/features/salaires/components/PaiementSalaireForm';
import type { SalaireMensuelRead, PaiementSalaireRead } from '@/features/salaires/api';

vi.mock('@/features/referentiels/api', () => ({
  referentielsApi: {
    modesPaiement: vi.fn().mockResolvedValue([
      { id: 1, code: 'ESPECES', libelle: 'Espèces', ordre: 1 },
    ]),
  },
}));

const salaire: SalaireMensuelRead = {
  id: 100,
  employe_id: 5,
  annee_scolaire_id: 1,
  mois_id: 10,
  montant_brut: 200_000,
  notes: null,
};

function renderForm(
  props: Partial<React.ComponentProps<typeof PaiementSalaireForm>> = {},
) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <PaiementSalaireForm
          salaire={salaire}
          paiementsExistants={[]}
          onSubmit={() => undefined}
          onCancel={() => undefined}
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('<PaiementSalaireForm>', () => {
  it('affiche les montants 70/30 et pré-remplit le montant AVANCE_70', async () => {
    renderForm();

    // 200 000 * 70 % = 140 000 → apparaît dans le bloc récap ET l'option
    // du select. On attend donc au moins 2 occurrences.
    expect(screen.getAllByText(/140 000 Ar/).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText(/60 000 Ar/).length).toBeGreaterThanOrEqual(2);

    const montant = screen.getByLabelText(/^Montant/i) as HTMLInputElement;
    expect(montant.value).toBe('140000');
  });

  it("soumet un paiement AVANCE_70 avec les valeurs attendues", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(screen.getByRole('button', { name: /enregistrer le paiement/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      salaire_mensuel_id: 100,
      type_part: 'AVANCE_70',
      montant: 140_000,
      date_a_completer: false,
    });
  });

  it('bascule sur SOLDE_30 et propose 60 000', async () => {
    const user = userEvent.setup();
    renderForm();

    await user.selectOptions(screen.getByLabelText(/^Part/i), 'SOLDE_30');

    await waitFor(() => {
      const m = screen.getByLabelText(/^Montant/i) as HTMLInputElement;
      expect(m.value).toBe('60000');
    });
  });

  it('calcule le reste après un paiement partiel déjà enregistré', () => {
    const deja: PaiementSalaireRead = {
      id: 1,
      annee_scolaire_id: 1,
      employe_id: 5,
      salaire_mensuel_id: 100,
      type_part: 'AVANCE_70',
      montant: 100_000,
      date_paiement: '2026-09-25',
      date_a_completer: false,
      mode_paiement_id: null,
      reference: null,
      observation: null,
      parent_paiement_salaire_id: null,
      created_by: 1,
      created_at: '',
    };

    renderForm({ paiementsExistants: [deja] });

    // 140 000 - 100 000 = 40 000 à proposer
    const m = screen.getByLabelText(/^Montant/i) as HTMLInputElement;
    expect(m.value).toBe('40000');
  });
});