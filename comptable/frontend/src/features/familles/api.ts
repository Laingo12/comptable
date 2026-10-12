import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type { FamilleFormOutput } from './schemas';

export type FamilleRead = components['schemas']['FamilleRead'];
export type PageFamilles = components['schemas']['Page_FamilleRead_'];

export interface ListFamillesParams {
  page: number;
  page_size: number;
  q?: string;
  sort?: string;
}

export const famillesApi = {
  async list(params: ListFamillesParams): Promise<PageFamilles> {
    const { data } = await apiClient.get<PageFamilles>('/familles', { params });
    return data;
  },
  async byId(id: number): Promise<FamilleRead> {
    const { data } = await apiClient.get<FamilleRead>(`/familles/${id}`);
    return data;
  },
  async create(payload: FamilleFormOutput): Promise<FamilleRead> {
    const { data } = await apiClient.post<FamilleRead>('/familles', payload);
    return data;
  },
  async update(id: number, payload: Partial<FamilleFormOutput>): Promise<FamilleRead> {
    const { data } = await apiClient.patch<FamilleRead>(`/familles/${id}`, payload);
    return data;
  },
};