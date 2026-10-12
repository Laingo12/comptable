import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type {
  InscriptionFormOutput,
  InscriptionListFilters,
  InscriptionUpdateOutput,
} from './schemas';

export type InscriptionRead = components['schemas']['InscriptionRead'];
export type PageInscriptions = components['schemas']['Page_InscriptionRead_'];

export const inscriptionsApi = {
  async list(filters: InscriptionListFilters): Promise<PageInscriptions> {
    const { data } = await apiClient.get<PageInscriptions>('/inscriptions', { params: filters });
    return data;
  },
  async byId(id: number): Promise<InscriptionRead> {
    const { data } = await apiClient.get<InscriptionRead>(`/inscriptions/${id}`);
    return data;
  },
  async create(payload: InscriptionFormOutput): Promise<InscriptionRead> {
    const { data } = await apiClient.post<InscriptionRead>('/inscriptions', payload);
    return data;
  },
  async update(id: number, payload: InscriptionUpdateOutput): Promise<InscriptionRead> {
    const { data } = await apiClient.patch<InscriptionRead>(`/inscriptions/${id}`, payload);
    return data;
  },
};