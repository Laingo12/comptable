import { z } from 'zod';

export const familleListFiltersSchema = z.object({
  q: z.string().max(200).optional(),
  sort: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(20),
});

export type FamilleListFilters = z.infer<typeof familleListFiltersSchema>;

/**
 * Contrat du formulaire famille.
 * ⚠️ Les transformations ('' → null) sont faites dans le composant
 * (`FamilleForm`) avant l'envoi, pas dans le schéma, pour que
 * `familleFormSchema.shape` reste un `ZodObject` simple et que
 * les règles de validation restent lisibles côté serveur (422).
 */
export const familleFormSchema = z.object({
  nom: z.string().trim().min(1, 'Nom requis').max(200),
  contact_principal: z.string().trim().max(200).optional(),
  telephone: z.string().trim().max(50).optional(),
  email: z
    .union([z.string().trim().email('Email invalide').max(200), z.literal('')])
    .optional(),
  adresse: z.string().trim().optional(),
  notes: z.string().trim().optional(),
});

export type FamilleFormValues = z.infer<typeof familleFormSchema>;

/** Payload envoyé à l'API. */
export interface FamilleFormOutput {
  nom: string;
  contact_principal: string | null;
  telephone: string | null;
  email: string | null;
  adresse: string | null;
  notes: string | null;
}

export function toFamillePayload(values: FamilleFormValues): FamilleFormOutput {
  const emptyToNull = (v: string | undefined): string | null => {
    if (v === undefined) return null;
    const t = v.trim();
    return t === '' ? null : t;
  };
  return {
    nom: values.nom.trim(),
    contact_principal: emptyToNull(values.contact_principal),
    telephone: emptyToNull(values.telephone),
    email: emptyToNull(values.email),
    adresse: emptyToNull(values.adresse),
    notes: emptyToNull(values.notes),
  };
}