import { z } from 'zod';

export const associeFormSchema = z.object({
  nom: z.string().trim().min(1, 'Nom requis').max(200),
  plafond_mensuel: z.coerce.number().int().min(0).optional(),
  versement_fixe_mensuel: z.coerce.number().int().min(0).optional(),
  versement_fixe_mois_debut_ordre: z.coerce.number().int().min(1).max(99).optional(),
  is_active: z.boolean().default(true),
});

export type AssocieFormValues = z.infer<typeof associeFormSchema>;

export interface AssocieInput {
  nom: string;
  plafond_mensuel: number | null;
  versement_fixe_mensuel: number | null;
  versement_fixe_mois_debut_ordre: number | null;
  is_active: boolean;
}

function positiveOrNull(v: number | undefined): number | null {
  return v !== undefined && v > 0 ? v : null;
}

export function toAssociePayload(values: AssocieFormValues): AssocieInput {
  return {
    nom: values.nom.trim(),
    plafond_mensuel: positiveOrNull(values.plafond_mensuel),
    versement_fixe_mensuel: positiveOrNull(values.versement_fixe_mensuel),
    versement_fixe_mois_debut_ordre:
      values.versement_fixe_mois_debut_ordre &&
      values.versement_fixe_mois_debut_ordre > 0
        ? values.versement_fixe_mois_debut_ordre
        : null,
    is_active: values.is_active,
  };
}