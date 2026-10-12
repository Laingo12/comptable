import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from '@/pages/DashboardPage';

const { mockedMois, mockedMensuel, mockedAnnuel } = vi.hoisted(() => ({
  mockedMois: [
    { id: 1, code: '2026-09', libelle: 'Septembre 2026', ordre: 1,
      date_debut: '2026-09-01', date_fin: '2026-09-30',
      date_limite_paiement: '2026-09-05', est_scolaire: true, annee_scolaire_id: 1 },
    { id: 2, code: '2026-10', libelle: 'Octobre 2026', ordre: 2,
      date_debut: '2026-10-01', date_fin: '2026-10-31',
      date_limite_paiement: '2026-10-05', est_scolaire: true, annee_scolaire_id: 1 },
  ],
  mockedMensuel: {
    annee_scolaire_id: 1, mois_id: 1,
    mois_code: '2026-09', mois_libelle: 'Septembre 2026', ordre: 1,
    ca_ecolage: 100_000, ca_inscription: 50_000, ca_frais_generaux: 20_000, ca_autre: 0,
    ca_total_brut: 170_000, ca_retenu: 170_000,
    avances: 0, retards_regularises: 0,
    par_mode: [], par_type: [], par_jour: [],
    ecolage_attendu: 200_000, ecolage_recu: 100_000, ecolage_reste_du: 100_000,
    taux_recouvrement: 50.0,
    compteurs: { payes: 1, partiels: 0, impayes: 1, en_retard: 0 },
    charges: 30_000,
    salaires_payes: 0,
    resultat_avant_prelevements: 140_000, prelevements_mois: 0,
    resultat_apres_prelevements: 140_000,
    tresorerie_debut: 0, tresorerie_fin: 140_000,
    jessy_prioritaire_10: 0,
    salaires: {
      brut_total: 0, du_70: 0, du_30: 0, paye_70: 0, paye_30: 0,
      disponible_pour_70: 140_000, pct_payable_25: 100.0, somme_manquante_25: 0,
    },
    comparatif: [],
  },
  mockedAnnuel: {
    annee_scolaire_id: 1, libelle: '2026-2027', effectif: 10,
    ca_ecolage: 1_000_000, ca_inscription: 500_000, ca_frais_generaux: 200_000, ca_autre: 0,
    ca_total_brut: 1_700_000, ca_retenu: 1_700_000,
    verse_associes: 500_000,
    retards_a_recouvrer: 100_000, avances_percues: 50_000,
    fg_restants_dus: 20_000, droits_inscription_restants_dus: 100_000,
    tresorerie_actuelle: 800_000, somme_manquante_cumulee: 0,
    mois: [
      { mois_code: '2026-09', mois_libelle: 'Septembre 2026', ordre: 1,
        ca_retenu: 170_000, charges: 30_000, salaires: 0, prelevements: 0,
        resultat_apres_prelevements: 140_000, tresorerie_fin: 140_000 },
      { mois_code: '2026-10', mois_libelle: 'Octobre 2026', ordre: 2,
        ca_retenu: 180_000, charges: 40_000, salaires: 0, prelevements: 0,
        resultat_apres_prelevements: 140_000, tresorerie_fin: 280_000 },
    ],
  },
}));

vi.mock('@/features/referentiels/api', () => ({
  referentielsApi: {
    moisScolaires: vi.fn().mockResolvedValue(mockedMois),
  },
}));

vi.mock('@/features/dashboard/api', () => ({
  dashboardApi: {
    mensuel: vi.fn().mockResolvedValue(mockedMensuel),
    annuel: vi.fn().mockResolvedValue(mockedAnnuel),
  },
}));

function renderPage(path = '/') {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard/annuel" element={<DashboardPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('<DashboardPage>', () => {
  it('affiche le dashboard mensuel par défaut (KPI, taux)', async () => {
    renderPage('/');

    expect(
      await screen.findByRole('heading', { name: /Tableau de bord mensuel/i }),
    ).toBeInTheDocument();

    // Plusieurs occurrences possibles (CA brut et CA retenu dans le mock).
    await screen.findAllByText('170 000 Ar');
    await screen.findAllByText('50,0 %');
    await screen.findAllByText('100 000 Ar');
  });

  it('bascule sur la vue annuelle', async () => {
    renderPage('/dashboard/annuel');

    expect(
      await screen.findByRole('heading', { name: /Tableau de bord annuel/i }),
    ).toBeInTheDocument();
    expect(await screen.findByText(/Effectif actif/i)).toBeInTheDocument();
    expect((await screen.findAllByText(/Octobre 2026/)).length).toBeGreaterThanOrEqual(1);
  });

  it('affiche le taux de recouvrement en pourcentage français', async () => {
    renderPage('/');
    expect(await screen.findByText(/50,0 %/)).toBeInTheDocument();
  });
});