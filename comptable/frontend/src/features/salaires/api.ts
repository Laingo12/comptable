import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type { GenererSalairesValues, PaiementSalairePayload } from './schemas';

export type SalaireMensuelRead = components['schemas']['SalaireMensuelRead'];
export type PaiementSalaireRead = components['schemas']['PaiementSalaireRead'];
export type PagePaiementsSalaires = components['schemas']['Page_PaiementSalaireRead_'];

export interface GenererSalairesReport {
  created: number;
  skipped: number;
  total: number;
}

export const salairesApi = {
  async genererMensuel(values: GenererSalairesValues): Promise<GenererSalairesReport> {
    const { data } = await apiClient.post<GenererSalairesReport>(
      '/salaires-mensuels/generer',
      {
        mois_id: values.mois_id,
        annee_scolaire_id: values.annee_scolaire_id ?? null,
        montant_brut_par_defaut: values.montant_brut_par_defaut ?? null,
      },
    );
    return data;
  },

  async listSalairesMensuels(mois_id: number): Promise<SalaireMensuelRead[]> {
    const { data } = await apiClient.get<SalaireMensuelRead[]>('/salaires-mensuels', {
      params: { mois_id },
    });
    return data;
  },

  async listPaiementsSalaires(salaire_mensuel_id: number): Promise<PagePaiementsSalaires> {
    const { data } = await apiClient.get<PagePaiementsSalaires>('/paiements-salaires', {
      params: { salaire_mensuel_id, page: 1, page_size: 50 },
    });
    return data;
  },

  async creerPaiementSalaire(payload: PaiementSalairePayload): Promise<PaiementSalaireRead> {
    const { data } = await apiClient.post<PaiementSalaireRead>(
      '/paiements-salaires',
      payload,
    );
    return data;
  },

  async annulerPaiementSalaire(id: number, motif: string): Promise<PaiementSalaireRead> {
    const { data } = await apiClient.post<PaiementSalaireRead>(
      `/paiements-salaires/${id}/annuler`,
      { motif },
    );
    return data;
  },
};