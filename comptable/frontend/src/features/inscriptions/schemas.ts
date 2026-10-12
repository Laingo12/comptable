import { z } from 'zod';

export const inscriptionListFiltersSchema = z.object({
  eleve_id: z.coerce.number().int().positive().optional(),
  niveau_id: z.coerce.number().int().positive().optional(),
  statut: z.enum(['ACTIF', 'SORTI']).optional(),
  sort: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(20),
});

export type InscriptionListFilters = z.infer<typeof inscriptionListFiltersSchema>;

/**
 * Contrat du formulaire inscription (création).
 * ⚠️ Les transformations sont faites à la sortie, pas dans le schéma,
 * pour préserver `inscriptionFormSchema.shape`.
 */
export const inscriptionFormSchema = z.object({
  eleve_id: z.coerce.number().int().positive(),
  niveau_id: z.coerce.number().int().positive('Niveau requis'),
  mois_entree_id: z.coerce.number().int().positive("Mois d'entrée requis"),
  ecolage_mensuel: z.coerce.number().int().min(0, 'Montant positif'),
  remise_pct: z.coerce.number().int().min(0).max(100),
  droit_inscription_du: z.coerce.number().int().min(0),
  frais_generaux_du: z.coerce.number().int().min(0),
});

export type InscriptionFormValues = z.infer<typeof inscriptionFormSchema>;

/** Payload création envoyé à l'API. */
export interface InscriptionFormOutput {
  eleve_id: number;
  niveau_id: number;
  mois_entree_id: number;
  ecolage_mensuel: number;
  remise_pct: number;
  droit_inscription_du: number;
  frais_generaux_du: number;
}

/** Payload mise à jour (eleve_id non modifiable). */
export interface InscriptionUpdateOutput {
  niveau_id?: number;
  mois_entree_id?: number;
  ecolage_mensuel?: number;
  remise_pct?: number;
  droit_inscription_du?: number;
  frais_generaux_du?: number;
  statut?: 'ACTIF' | 'SORTI';
  date_sortie?: string | null;
}

export function toInscriptionUpdatePayload(
  values: InscriptionFormValues,
): InscriptionUpdateOutput {
  return {
    niveau_id: values.niveau_id,
    mois_entree_id: values.mois_entree_id,
    ecolage_mensuel: values.ecolage_mensuel,
    remise_pct: values.remise_pct,
    droit_inscription_du: values.droit_inscription_du,
    frais_generaux_du: values.frais_generaux_du,
  };
}