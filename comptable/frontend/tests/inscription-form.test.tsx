import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { InscriptionForm } from '@/features/inscriptions/components/InscriptionForm';

vi.mock('@/features/referentiels/api', () => ({
  referentielsApi: {
    niveaux: vi.fn().mockResolvedValue([
      { id: 1, code: 'PS', libelle: 'PS', ordre: 3 },
    ]),
    moisScolaires: vi.fn().mockResolvedValue([
      { id: 10, code: '2026-09', libelle: 'Septembre 2026', ordre: 1,
        date_debut: '2026-09-01', date_fin: '2026-09-30',
        date_limite_paiement: '2026-09-05', est_scolaire: true,
        annee_scolaire_id: 1 },
    ]),
    grilleTarifaire: vi.fn().mockResolvedValue([
      { id: 1, annee_scolaire_id: 1, niveau_id: 1,
        ecolage_mensuel: 120_000, droit_inscription: 50_000,
        frais_generaux: 20_000, version: 1 },
    ]),
  },
}));

function renderForm(props: Partial<React.ComponentProps<typeof InscriptionForm>> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <InscriptionForm
          eleveId={1}
          onSubmit={() => undefined}
          onCancel={() => undefined}
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('<InscriptionForm>', () => {
  it('affiche les erreurs de validation sur champs requis', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(screen.getByRole('button', { name: /créer l'inscription/i }));

    const alerts = await screen.findAllByRole('alert');
    const texts = alerts.map((a) => a.textContent ?? '');
    expect(texts.some((t) => /niveau requis/i.test(t))).toBe(true);
    expect(texts.some((t) => /mois d'entrée requis/i.test(t))).toBe(true);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('préremplit les tarifs depuis la grille quand on choisit un niveau', async () => {
    const user = userEvent.setup();
    renderForm();

    await screen.findByRole('option', { name: 'PS' });
    await user.selectOptions(screen.getByLabelText(/^Niveau/i), '1');

    await waitFor(() => {
      const eco = screen.getByLabelText(/écolage mensuel \(avant remise\)/i) as HTMLInputElement;
      expect(eco.value).toBe('120000');
    });
    const droits = screen.getByLabelText(/droit d'inscription dû/i) as HTMLInputElement;
    expect(droits.value).toBe('50000');
    const fg = screen.getByLabelText(/frais généraux dus/i) as HTMLInputElement;
    expect(fg.value).toBe('20000');
  });

  it('soumet les valeurs saisies', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await screen.findByRole('option', { name: 'PS' });
    await screen.findByRole('option', { name: 'Septembre 2026' });

    await user.selectOptions(screen.getByLabelText(/^Niveau/i), '1');
    await user.selectOptions(screen.getByLabelText(/^Mois d'entrée/i), '10');
    await user.click(screen.getByRole('button', { name: /créer l'inscription/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      eleve_id: 1,
      niveau_id: 1,
      mois_entree_id: 10,
      ecolage_mensuel: 120_000,
      droit_inscription_du: 50_000,
      frais_generaux_du: 20_000,
    });
  });
});