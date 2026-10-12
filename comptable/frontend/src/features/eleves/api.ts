import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type { EleveFormOutput } from './schemas';

export type EleveRead = components['schemas']['EleveRead'];
export type PageEleves = components['schemas']['Page_EleveRead_'];

export interface ListElevesParams {
  page: number;
  page_size: number;
  q?: string;
  famille_id?: number;
  sort?: string;
}

export const elevesApi = {
  async list(params: ListElevesParams): Promise<PageEleves> {
    const { data } = await apiClient.get<PageEleves>('/eleves', { params });
    return data;
  },
  async byId(id: number): Promise<EleveRead> {
    const { data } = await apiClient.get<EleveRead>(`/eleves/${id}`);
    return data;
  },
  async create(payload: EleveFormOutput): Promise<EleveRead> {
    const { data } = await apiClient.post<EleveRead>('/eleves', payload);
    return data;
  },
  async update(id: number, payload: Partial<EleveFormOutput>): Promise<EleveRead> {
    const { data } = await apiClient.patch<EleveRead>(`/eleves/${id}`, payload);
    return data;
  },
};