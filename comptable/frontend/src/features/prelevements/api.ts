import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type { PrelevementCreatePayload, PrelevementListFilters } from './schemas';

export type PrelevementRead = components['schemas']['PrelevementRead'];
export type PagePrelevements = components['schemas']['Page_PrelevementRead_'];

export const prelevementsApi = {
  async list(filters: PrelevementListFilters): Promise<PagePrelevements> {
    const { data } = await apiClient.get<PagePrelevements>('/prelevements', {
      params: filters,
    });
    return data;
  },
  async byId(id: number): Promise<PrelevementRead> {
    const { data } = await apiClient.get<PrelevementRead>(`/prelevements/${id}`);
    return data;
  },
  async create(payload: PrelevementCreatePayload): Promise<PrelevementRead> {
    const { data } = await apiClient.post<PrelevementRead>('/prelevements', payload);
    return data;
  },
  async annuler(id: number, motif: string): Promise<PrelevementRead> {
    const { data } = await apiClient.post<PrelevementRead>(
      `/prelevements/${id}/annuler`,
      { motif },
    );
    return data;
  },
};