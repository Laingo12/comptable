import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MoneyCell } from '@/components/MoneyCell';

describe('<MoneyCell>', () => {
  it('formate un entier positif en Ariary', () => {
    render(<MoneyCell value={1_500_000} />);
    expect(screen.getByText('1 500 000 Ar')).toBeInTheDocument();
  });

  it('formate zéro', () => {
    render(<MoneyCell value={0} />);
    expect(screen.getByText('0 Ar')).toBeInTheDocument();
  });

  it('affiche un tiret pour null', () => {
    render(<MoneyCell value={null} />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });

  it('met en évidence les montants négatifs', () => {
    render(<MoneyCell value={-75_000} />);
    const node = screen.getByText('-75 000 Ar');
    expect(node).toHaveAttribute('data-negative', 'true');
    expect(node.className).toContain('text-danger');
  });

  it('n\'ajoute pas la classe danger sur un positif', () => {
    render(<MoneyCell value={100_000} />);
    const node = screen.getByText('100 000 Ar');
    expect(node).not.toHaveAttribute('data-negative');
    expect(node.className).not.toContain('text-danger');
  });
});