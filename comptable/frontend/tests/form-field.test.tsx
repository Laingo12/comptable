import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FormField } from '@/components/FormField';
import { Input } from '@/components/ui/input';

describe('<FormField>', () => {
  it('associe le label au champ via htmlFor/id', () => {
    render(
      <FormField label="Nom" htmlFor="nom">
        <Input id="nom" />
      </FormField>,
    );
    expect(screen.getByLabelText('Nom')).toBeInTheDocument();
  });

  it('expose une erreur via role=alert et aria-describedby', () => {
    render(
      <FormField label="Nom" htmlFor="nom" error="Champ obligatoire.">
        <Input id="nom" />
      </FormField>,
    );
    const err = screen.getByRole('alert');
    expect(err).toHaveTextContent('Champ obligatoire.');
    const input = screen.getByLabelText('Nom');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input.getAttribute('aria-describedby')).toContain('nom-error');
  });

  it('expose un hint via aria-describedby quand pas d\'erreur', () => {
    render(
      <FormField label="Nom" htmlFor="nom" hint="Indiqué sur le bulletin.">
        <Input id="nom" />
      </FormField>,
    );
    const input = screen.getByLabelText('Nom');
    expect(input.getAttribute('aria-describedby')).toContain('nom-hint');
    expect(screen.getByText('Indiqué sur le bulletin.')).toHaveAttribute('id', 'nom-hint');
  });
});