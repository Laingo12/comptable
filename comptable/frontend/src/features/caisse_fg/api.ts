import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type { CaisseFgCreatePayload, CaisseFgListFilters } from './schemas';

export type CaisseFgRead = components['schemas']['CaisseFgRead'];
export type PageCaisseFg = components['schemas']['Page_CaisseFgRead_'];

export const caisseFgApi = {
  async list(filters: CaisseFgListFilters): Promise<PageCaisseFg> {
    const { data } = await apiClient.get<PageCaisseFg>('/caisse-fg', { params: filters });
    return data;
  },
  async byId(id: number): Promise<CaisseFgRead> {
    const { data } = await apiClient.get<CaisseFgRead>(`/caisse-fg/${id}`);
    return data;
  },
  async create(payload: CaisseFgCreatePayload): Promise<CaisseFgRead> {
    const { data } = await apiClient.post<CaisseFgRead>('/caisse-fg', payload);
    return data;
  },
  async annuler(id: number, motif: string): Promise<CaisseFgRead> {
    const { data } = await apiClient.post<CaisseFgRead>(
      `/caisse-fg/${id}/annuler`,
      { motif },
    );
    return data;
  },
};