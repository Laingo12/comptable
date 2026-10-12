import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';

export type ImportReport = components['schemas']['ImportReport'];
export type SheetStat = components['schemas']['SheetStat'];
export type ImportLigneRead = components['schemas']['ImportLigneRead'];

export interface ImportParams {
  file: File;
  dry_run: boolean;
}

export const importApi = {
  async importExcel({ file, dry_run }: ImportParams): Promise<ImportReport> {
    const form = new FormData();
    form.append('file', file);

    const { data } = await apiClient.post<ImportReport>(
      `/import/excel?dry_run=${dry_run ? 'true' : 'false'}`,
      form,
      {
        // Axios détecte automatiquement le Content-Type et le boundary,
        // on n'override PAS les en-têtes.
        headers: { 'Content-Type': undefined as unknown as string },
      },
    );
    return data;
  },

  async listLignes(sheet?: string, limit = 100): Promise<ImportLigneRead[]> {
    const { data } = await apiClient.get<ImportLigneRead[]>('/import/lignes', {
      params: { sheet, limit },
    });
    return data;
  },
};