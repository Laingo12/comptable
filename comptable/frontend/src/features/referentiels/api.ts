import { apiClient } from '@/lib/apiClient';
import type { components } from '@/types/api';

export type NiveauRead = components['schemas']['NiveauRead'];
export type AnneeScolaireRead = components['schemas']['AnneeScolaireRead'];
export type MoisScolaireRead = components['schemas']['MoisScolaireRead'];
export type GrilleTarifaireRead = components['schemas']['GrilleTarifaireRead'];
export type TypePaiementRead = components['schemas']['TypePaiementRead'];
export type ModePaiementRead = components['schemas']['ModePaiementRead'];
export type ChargeCatalogueRead = components['schemas']['ChargeCatalogueRead'];

export const referentielsApi = {
  async niveaux(): Promise<NiveauRead[]> {
    const { data } = await apiClient.get<NiveauRead[]>('/niveaux');
    return data;
  },
  async anneeActive(): Promise<AnneeScolaireRead> {
    const { data } = await apiClient.get<AnneeScolaireRead>('/annees/active');
    return data;
  },
  async moisScolaires(annee_scolaire_id?: number): Promise<MoisScolaireRead[]> {
    const { data } = await apiClient.get<MoisScolaireRead[]>('/mois-scolaires', {
      params: annee_scolaire_id ? { annee_scolaire_id } : undefined,
    });
    return data;
  },
  async grilleTarifaire(annee_scolaire_id?: number): Promise<GrilleTarifaireRead[]> {
    const { data } = await apiClient.get<GrilleTarifaireRead[]>('/grille-tarifaire', {
      params: annee_scolaire_id ? { annee_scolaire_id } : undefined,
    });
    return data;
  },
  async typesPaiement(): Promise<TypePaiementRead[]> {
    const { data } = await apiClient.get<TypePaiementRead[]>('/types-paiement');
    return data;
  },
  async modesPaiement(): Promise<ModePaiementRead[]> {
    const { data } = await apiClient.get<ModePaiementRead[]>('/modes-paiement');
    return data;
  },
  async chargesCatalogue(): Promise<ChargeCatalogueRead[]> {
    const { data } = await apiClient.get<ChargeCatalogueRead[]>('/charges-catalogue');
    return data;
  },
};