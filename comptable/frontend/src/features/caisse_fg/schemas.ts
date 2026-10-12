import { z } from 'zod';

const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Format AAAA-MM-JJ attendu');

export const caisseFgListFiltersSchema = z.object({
  mois_id: z.coerce.number().int().positive().optional(),
  sens: z.enum(['ENTREE', 'SORTIE']).optional(),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  include_annules: z.coerce.boolean().optional().default(false),
  sort: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(20),
});

export type CaisseFgListFilters = z.infer<typeof caisseFgListFiltersSchema>;

export const caisseFgFormSchema = z.object({
  sens: z.enum(['ENTREE', 'SORTIE']),
  montant: z.coerce.number().int().min(1, 'Montant strictement positif (Ariary)'),
  libelle: z.string().trim().min(1, 'Libellé requis').max(200),
  date_operation: isoDate,
  remarque: z.string().trim().optional(),
  mode_paiement_id: z.coerce.number().int().min(0).optional(),
  reference: z.string().trim().max(100).optional(),
});

export type CaisseFgFormValues = z.infer<typeof caisseFgFormSchema>;

export interface CaisseFgCreatePayload {
  sens: 'ENTREE' | 'SORTIE';
  montant: number;
  libelle: string;
  date_operation: string;
  date_a_completer: false;
  remarque: string | null;
  mode_paiement_id: number | null;
  reference: string | null;
}

function positiveOrNull(v: number | undefined): number | null {
  return v !== undefined && v > 0 ? v : null;
}

export function toCaisseFgPayload(values: CaisseFgFormValues): CaisseFgCreatePayload {
  const emptyToNull = (v: string | undefined): string | null => {
    if (v === undefined) return null;
    const t = v.trim();
    return t === '' ? null : t;
  };
  return {
    sens: values.sens,
    montant: values.montant,
    libelle: values.libelle.trim(),
    date_operation: values.date_operation,
    date_a_completer: false,
    remarque: emptyToNull(values.remarque),
    mode_paiement_id: positiveOrNull(values.mode_paiement_id),
    reference: emptyToNull(values.reference),
  };
}