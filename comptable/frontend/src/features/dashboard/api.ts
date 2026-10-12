import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';

export type DashboardMensuel = components['schemas']['DashboardMensuel'];
export type DashboardAnnuel = components['schemas']['DashboardAnnuel'];
export type SalairesInfo = components['schemas']['SalairesInfo'];
export type ComparatifLigne = components['schemas']['ComparatifLigne'];
export type EncaissementJour = components['schemas']['EncaissementJour'];
export type EncaissementParMode = components['schemas']['EncaissementParMode'];

export const dashboardApi = {
  async mensuel(mois_id: number, annee_scolaire_id?: number): Promise<DashboardMensuel> {
    const { data } = await apiClient.get<DashboardMensuel>('/dashboard/mensuel', {
      params: { mois_id, annee_scolaire_id },
    });
    return data;
  },
  async annuel(annee_scolaire_id?: number): Promise<DashboardAnnuel> {
    const { data } = await apiClient.get<DashboardAnnuel>('/dashboard/annuel', {
      params: annee_scolaire_id ? { annee_scolaire_id } : undefined,
    });
    return data;
  },
};