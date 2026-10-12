import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfirmDialog } from '@/components/ConfirmDialog';

describe('<ConfirmDialog>', () => {
  it('n\'appelle pas onConfirm si le motif est vide', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();
    render(
      <ConfirmDialog
        open
        title="Annuler"
        onCancel={() => undefined}
        onConfirm={onConfirm}
      />,
    );
    await user.click(screen.getByRole('button', { name: /confirmer/i }));
    expect(onConfirm).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent(/motif requis/i);
  });

  it('appelle onConfirm avec le motif saisi', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();
    render(
      <ConfirmDialog
        open
        title="Annuler"
        onCancel={() => undefined}
        onConfirm={onConfirm}
      />,
    );
    await user.type(screen.getByLabelText(/motif/i), 'Erreur de saisie');
    await user.click(screen.getByRole('button', { name: /confirmer/i }));
    expect(onConfirm).toHaveBeenCalledWith('Erreur de saisie');
  });
});