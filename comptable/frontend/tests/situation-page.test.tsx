import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EleveSituationPage } from '@/features/situation/pages/EleveSituationPage';

// --- Données de mock, hoistées AVANT les vi.mock() ---------------------

const { mockedEleve, mockedSituation } = vi.hoisted(() => ({
  mockedEleve: {
    id: 1, matricule: 'SK-2026-0001', nom: 'Rakoto', prenoms: 'Naina',
    sexe: 'M', date_naissance: '2018-05-01', famille_id: null,
    version: 1, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
  },
  mockedSituation: {
    eleve_id: 1,
    inscription_id: 10,
    annee_scolaire_id: 1,
    matricule: 'SK-2026-0001',
    nom: 'Rakoto',
    prenoms: 'Naina',
    niveau_id: 3,
    mois_entree_id: 1,
    ecolage_mensuel: 100_000,
    remise_pct: 10,
    droits_inscription: { du: 50_000, paye: 50_000, reste_du: 0, statut: 'PAYE' },
    frais_generaux:    { du: 20_000, paye: 10_000, reste_du: 10_000, statut: 'PARTIEL' },
    mois: [
      {
        mois_id: 1, code: '2026-09', libelle: 'Septembre 2026', ordre: 1,
        date_limite_paiement: '2026-09-05',
        du: 90_000, paye: 90_000, reste_du: 0, statut: 'PAYE', echu: false, en_retard: false,
        paiements: [
          { id: 501, montant: 90_000, date_paiement: '2026-09-04',
            mode_paiement_id: 1, reference: 'REC-1', qualificatif: 'NORMAL' },
        ],
      },
      {
        mois_id: 2, code: '2026-10', libelle: 'Octobre 2026', ordre: 2,
        date_limite_paiement: '2026-10-05',
        du: 90_000, paye: 0, reste_du: 90_000, statut: 'IMPAYE', echu: true, en_retard: true,
        paiements: [],
      },
    ],
    totaux: { du: 200_000, paye: 100_000, reste_du: 100_000, taux_recouvrement: 50.0 },
  },
}));

// --- Mocks -------------------------------------------------------------

vi.mock('@/features/eleves/api', () => ({
  elevesApi: {
    byId: vi.fn().mockResolvedValue(mockedEleve),
  },
}));

vi.mock('@/features/situation/api', () => ({
  situationApi: {
    byEleve: vi.fn().mockResolvedValue(mockedSituation),
  },
  downloadReceipt: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('@/features/referentiels/api', () => ({
  referentielsApi: {
    niveaux: vi.fn().mockResolvedValue([{ id: 3, code: 'PS', libelle: 'PS', ordre: 3 }]),
  },
}));

// --- Helpers -----------------------------------------------------------

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/eleves/1/situation']}>
        <Routes>
          <Route path="/eleves/:id/situation" element={<EleveSituationPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

// --- Tests -------------------------------------------------------------

describe('<EleveSituationPage>', () => {
  it("affiche les KPI d'écolage, droits, FG et le détail par mois", async () => {
    renderPage();

    // En-tête
    expect(
      await screen.findByRole('heading', { name: /Situation écolage — Rakoto Naina/i }),
    ).toBeInTheDocument();

    // KPI
    expect(screen.getByText(/Écolage attendu/i)).toBeInTheDocument();
    expect(screen.getByText(/200 000 Ar/)).toBeInTheDocument();   // totaux.du
    expect(screen.getByText(/50,0 %/)).toBeInTheDocument();       // taux (formatPercent)

    // Cartes droits + FG (CardTitle → h3 → role="heading")
    expect(screen.getByRole('heading', { name: /droit d'inscription/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /frais généraux/i })).toBeInTheDocument();

    // Mois : présents dans le tableau en tant que texte (cellules <td>),
    // → on cherche par texte, pas par rôle heading.
    expect(screen.getByText('Septembre 2026')).toBeInTheDocument();
    expect(screen.getByText('Octobre 2026')).toBeInTheDocument();
  });

  it('affiche un bouton Reçu par paiement listé', async () => {
    renderPage();
    await screen.findByRole('heading', { name: /Situation écolage/i });
    const receiptButtons = screen.getAllByRole('button', { name: /télécharger le reçu/i });
    expect(receiptButtons).toHaveLength(1);
  });

  it("affiche l'ErrorState quand l'API situation échoue", async () => {
    const { situationApi } = await import('@/features/situation/api');
    (situationApi.byEleve as ReturnType<typeof vi.fn>).mockRejectedValueOnce(new Error('boom'));

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Situation indisponible/i);
    });
  });
});