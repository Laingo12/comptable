import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type { PaiementCreatePayload, PaiementListFilters } from './schemas';

export type PaiementRead = components['schemas']['PaiementRead'];
export type PagePaiements = components['schemas']['Page_PaiementRead_'];

export const paiementsApi = {
  async list(filters: PaiementListFilters): Promise<PagePaiements> {
    const { data } = await apiClient.get<PagePaiements>('/paiements', { params: filters });
    return data;
  },

  async byId(id: number): Promise<PaiementRead> {
    const { data } = await apiClient.get<PaiementRead>(`/paiements/${id}`);
    return data;
  },

  async create(payload: PaiementCreatePayload): Promise<PaiementRead> {
    const { data } = await apiClient.post<PaiementRead>('/paiements', payload);
    return data;
  },

  async annuler(id: number, motif: string): Promise<PaiementRead> {
    const { data } = await apiClient.post<PaiementRead>(`/paiements/${id}/annuler`, { motif });
    return data;
  },
};