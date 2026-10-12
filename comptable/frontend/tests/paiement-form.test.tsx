import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { PaiementForm } from '@/features/paiements/components/PaiementForm';

vi.mock('@/features/referentiels/api', () => ({
  referentielsApi: {
    typesPaiement: vi.fn().mockResolvedValue([
      { id: 1, code: 'ECOLAGE',        libelle: 'Écolage',             ordre: 1 },
      { id: 2, code: 'INSCRIPTION',    libelle: "Droit d'inscription", ordre: 2 },
      { id: 3, code: 'FRAIS_GENERAUX', libelle: 'Frais généraux',      ordre: 3 },
      { id: 4, code: 'AUTRE',          libelle: 'Autre recette',       ordre: 4 },
    ]),
    modesPaiement: vi.fn().mockResolvedValue([
      { id: 1, code: 'ESPECES', libelle: 'Espèces', ordre: 1 },
    ]),
    moisScolaires: vi.fn().mockResolvedValue([
      { id: 10, code: '2026-09', libelle: 'Septembre 2026', ordre: 1,
        date_debut: '2026-09-01', date_fin: '2026-09-30',
        date_limite_paiement: '2026-09-05', est_scolaire: true, annee_scolaire_id: 1 },
    ]),
  },
}));

vi.mock('@/features/inscriptions/api', () => ({
  inscriptionsApi: {
    byId: vi.fn().mockResolvedValue({
      id: 42, eleve_id: 1, annee_scolaire_id: 1, niveau_id: 3,
      mois_entree_id: 10, ecolage_mensuel: 100_000, remise_pct: 10,
      droit_inscription_du: 50_000, frais_generaux_du: 20_000,
      statut: 'ACTIF', date_sortie: null, version: 1,
      created_at: '', updated_at: '',
    }),
  },
}));

function renderForm(props: Partial<React.ComponentProps<typeof PaiementForm>> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <PaiementForm
          inscriptionId={42}
          onSubmit={() => undefined}
          onCancel={() => undefined}
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('<PaiementForm>', () => {
  it('affiche les erreurs de validation sur champs requis', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(screen.getByRole('button', { name: /enregistrer le paiement/i }));

    const alerts = await screen.findAllByRole('alert');
    const texts = alerts.map((a) => a.textContent ?? '');
    expect(texts.some((t) => /type requis/i.test(t))).toBe(true);
    expect(texts.some((t) => /montant strictement positif/i.test(t))).toBe(true);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('affiche le select des mois uniquement si ECOLAGE', async () => {
    const user = userEvent.setup();
    renderForm();

    await screen.findByRole('option', { name: 'Écolage' });

    // ECOLAGE → mois apparaît
    await user.selectOptions(screen.getByLabelText(/^Type de paiement/i), '1');
    expect(await screen.findByLabelText(/^Mois concerné/i)).toBeInTheDocument();

    // INSCRIPTION → mois disparaît
    await user.selectOptions(screen.getByLabelText(/^Type de paiement/i), '2');
    expect(screen.queryByLabelText(/^Mois concerné/i)).not.toBeInTheDocument();
  });

  it('soumet un écolage avec mois', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    // 1. Sélectionner ECOLAGE (fait apparaître le select mois)
    await screen.findByRole('option', { name: 'Écolage' });
    await user.selectOptions(screen.getByLabelText(/^Type de paiement/i), '1');

    // 2. Attendre le select mois (rendu conditionnel) et son option
    await screen.findByRole('option', { name: 'Septembre 2026' });
    await user.selectOptions(screen.getByLabelText(/^Mois concerné/i), '10');

    // 3. Montant + submit
    await user.clear(screen.getByLabelText(/^Montant/i));
    await user.type(screen.getByLabelText(/^Montant/i), '90000');
    await user.click(screen.getByRole('button', { name: /enregistrer le paiement/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      inscription_id: 42,
      type_paiement_id: 1,
      mois_concerne_id: 10,
      montant: 90_000,
      date_a_completer: false,
    });
  });

  it('refuse un écolage sans mois', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await screen.findByRole('option', { name: 'Écolage' });
    await user.selectOptions(screen.getByLabelText(/^Type de paiement/i), '1');

    // Attendre le select mois, mais ne rien choisir
    await screen.findByLabelText(/^Mois concerné/i);

    await user.clear(screen.getByLabelText(/^Montant/i));
    await user.type(screen.getByLabelText(/^Montant/i), '90000');
    await user.click(screen.getByRole('button', { name: /enregistrer le paiement/i }));

    expect(await screen.findByText(/mois obligatoire/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});