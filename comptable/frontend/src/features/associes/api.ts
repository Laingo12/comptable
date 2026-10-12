import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type { AssocieInput } from './schemas';

export type AssocieRead = components['schemas']['AssocieRead'];

export const associesApi = {
  async list(): Promise<AssocieRead[]> {
    const { data } = await apiClient.get<AssocieRead[]>('/associes');
    return data;
  },
  async byId(id: number): Promise<AssocieRead> {
    const { data } = await apiClient.get<AssocieRead>(`/associes/${id}`);
    return data;
  },
  async create(payload: AssocieInput): Promise<AssocieRead> {
    const { data } = await apiClient.post<AssocieRead>('/associes', payload);
    return data;
  },
  async update(id: number, payload: Partial<AssocieInput>): Promise<AssocieRead> {
    const { data } = await apiClient.patch<AssocieRead>(`/associes/${id}`, payload);
    return data;
  },
};