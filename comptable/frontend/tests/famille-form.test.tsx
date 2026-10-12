import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { FamilleForm } from '@/features/familles/components/FamilleForm';

function renderForm(props: Partial<React.ComponentProps<typeof FamilleForm>> = {}) {
  return render(
    <MemoryRouter>
      <FamilleForm
        onSubmit={() => undefined}
        onCancel={() => undefined}
        {...props}
      />
    </MemoryRouter>,
  );
}

describe('<FamilleForm>', () => {
  it('affiche une erreur si le nom est vide', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.click(screen.getByRole('button', { name: /créer la famille/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/nom requis/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('rejette un email invalide', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.type(screen.getByLabelText(/nom de la famille/i), 'Rakoto');
    await user.type(screen.getByLabelText('Email'), 'pas-un-email');
    await user.click(screen.getByRole('button', { name: /créer la famille/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/email invalide/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('convertit les champs vides en null au moment de la soumission', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    renderForm({ onSubmit });

    await user.type(screen.getByLabelText(/nom de la famille/i), 'Rakoto');
    await user.click(screen.getByRole('button', { name: /créer la famille/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      nom: 'Rakoto',
      contact_principal: null,
      telephone: null,
      email: null,
      adresse: null,
      notes: null,
    });
  });

  it('affiche les erreurs 422 propagées par le parent', async () => {
    renderForm({
      fieldErrors: { nom: 'Ce nom existe déjà.' },
    });
    expect(await screen.findByRole('alert')).toHaveTextContent('Ce nom existe déjà.');
  });
});