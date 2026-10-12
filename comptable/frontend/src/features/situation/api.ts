import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';

export type EleveSituation = components['schemas']['EleveSituation'];
export type MoisSituation = components['schemas']['MoisSituation'];
export type PaiementLigne = components['schemas']['PaiementLigne'];

export const situationApi = {
  async byEleve(eleveId: number, annee_scolaire_id?: number): Promise<EleveSituation> {
    const { data } = await apiClient.get<EleveSituation>(`/eleves/${eleveId}/situation`, {
      params: annee_scolaire_id ? { annee_scolaire_id } : undefined,
    });
    return data;
  },

  async byInscription(inscriptionId: number): Promise<EleveSituation> {
    const { data } = await apiClient.get<EleveSituation>(
      `/inscriptions/${inscriptionId}/situation`,
    );
    return data;
  },
};

/** Télécharge le reçu (PDF, ou HTML en repli si WeasyPrint indisponible). */
export async function downloadReceipt(
  paiementId: number,
  format: 'pdf' | 'html' = 'pdf',
): Promise<void> {
  const res = await apiClient.get(`/exports/paiements/${paiementId}/recu`, {
    params: { format },
    responseType: 'blob',
  });

  const contentType = (res.headers['content-type'] as string | undefined) ?? '';
  const isPdf = contentType.startsWith('application/pdf');
  const isHtml = contentType.startsWith('text/html');

  const blob = new Blob([res.data], {
    type: isPdf ? 'application/pdf' : 'text/html;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);

  if (isHtml) {
    // Repli : ouvrir dans un nouvel onglet pour impression manuelle.
    window.open(url, '_blank', 'noopener');
    // Libération différée de l'URL.
    setTimeout(() => URL.revokeObjectURL(url), 60_000);
    return;
  }

  const a = document.createElement('a');
  a.href = url;
  a.download = `recu_${paiementId}.${isPdf ? 'pdf' : 'html'}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5_000);
}