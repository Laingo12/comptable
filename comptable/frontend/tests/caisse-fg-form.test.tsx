import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { CaisseFgForm } from '@/features/caisse_fg/components/CaisseFgForm';

vi.mock('@/features/referentiels/api', () => ({
  referentielsApi: {
    modesPaiement: vi.fn().mockResolvedValue([
      { id: 1, code: 'ESPECES', libelle: 'Espèces', ordre: 1 },
    ]),
  },
}));

function renderForm(props: Partial<React.ComponentProps<typeof CaisseFgForm>> = {}) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <CaisseFgForm
          onSubmit={() => undefined}
          onCancel={() => undefined}
          {...props}
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('<CaisseFgForm>', () => {
  it('affiche les erreurs sur champs requis', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(screen.getByRole('button', { name: /enregistrer l'opération/i }));

    const alerts = await screen.findAllByRole('alert');
    const texts = alerts.map((a) => a.textContent ?? '');
    expect(texts.some((t) => /libellé requis/i.test(t))).toBe(true);
    expect(texts.some((t) => /montant strictement positif/i.test(t))).toBe(true);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('soumet une entrée', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.type(screen.getByLabelText(/^Libellé/i), 'Recette FG test');
    await user.clear(screen.getByLabelText(/^Montant/i));
    await user.type(screen.getByLabelText(/^Montant/i), '25000');
    await user.click(screen.getByRole('button', { name: /enregistrer l'opération/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      sens: 'ENTREE',
      libelle: 'Recette FG test',
      montant: 25_000,
      date_a_completer: false,
      remarque: null,
      reference: null,
    });
  });

  it('soumet une sortie', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit, defaultSens: 'SORTIE' });

    await user.type(screen.getByLabelText(/^Libellé/i), 'Achat fournitures');
    await user.clear(screen.getByLabelText(/^Montant/i));
    await user.type(screen.getByLabelText(/^Montant/i), '15000');
    await user.click(screen.getByRole('button', { name: /enregistrer l'opération/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      sens: 'SORTIE',
      libelle: 'Achat fournitures',
      montant: 15_000,
    });
  });
});