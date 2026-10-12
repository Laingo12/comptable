import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';
import type { ChargeCreatePayload, ChargeListFilters } from './schemas';

export type ChargeRead = components['schemas']['ChargeRead'];
export type PageCharges = components['schemas']['Page_ChargeRead_'];
export type ChargeCatalogueRead = components['schemas']['ChargeCatalogueRead'];

export const chargesApi = {
  async list(filters: ChargeListFilters): Promise<PageCharges> {
    const { data } = await apiClient.get<PageCharges>('/charges', { params: filters });
    return data;
  },
  async byId(id: number): Promise<ChargeRead> {
    const { data } = await apiClient.get<ChargeRead>(`/charges/${id}`);
    return data;
  },
  async create(payload: ChargeCreatePayload): Promise<ChargeRead> {
    const { data } = await apiClient.post<ChargeRead>('/charges', payload);
    return data;
  },
  async annuler(id: number, motif: string): Promise<ChargeRead> {
    const { data } = await apiClient.post<ChargeRead>(`/charges/${id}/annuler`, { motif });
    return data;
  },
};