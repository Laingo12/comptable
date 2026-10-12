import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge, type StatusKey } from '@/components/StatusBadge';

describe('<StatusBadge>', () => {
  const cases: Array<[StatusKey, string]> = [
    ['PAYE', 'Payé'],
    ['PARTIEL', 'Partiel'],
    ['IMPAYE', 'Impayé'],
    ['ECHU', 'Échu'],
    ['AVANCE', 'Avance'],
    ['RETARD', 'En retard'],
    ['ANNULE', 'Annulé'],
    ['A_COMPLETER', 'À compléter'],
  ];

  for (const [status, label] of cases) {
    it(`affiche "${label}" (status=${status})`, () => {
      render(<StatusBadge status={status} />);
      const node = screen.getByRole('status');
      expect(node).toHaveTextContent(label);
      expect(node).toHaveAttribute('aria-label', label);
    });
  }

  it('expose le hint dans le texte et l\'aria-label', () => {
    render(<StatusBadge status="PARTIEL" hint="reste 25 000 Ar" />);
    const node = screen.getByRole('status');
    expect(node).toHaveTextContent('reste 25 000 Ar');
    expect(node).toHaveAttribute('aria-label', 'Partiel — reste 25 000 Ar');
  });
});