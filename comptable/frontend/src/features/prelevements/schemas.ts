import { z } from 'zod';

const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Format AAAA-MM-JJ attendu');

export const prelevementListFiltersSchema = z.object({
  associe_id: z.coerce.number().int().positive().optional(),
  mois_id: z.coerce.number().int().positive().optional(),
  type: z.enum(['RETRAIT', 'VERSEMENT_FIXE', 'SUPPLEMENT']).optional(),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  include_annules: z.coerce.boolean().optional().default(false),
  sort: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(20),
});

export type PrelevementListFilters = z.infer<typeof prelevementListFiltersSchema>;

export const prelevementFormSchema = z.object({
  associe_id: z.coerce.number().int().positive('Associé requis'),
  type: z.enum(['RETRAIT', 'VERSEMENT_FIXE', 'SUPPLEMENT']),
  montant: z.coerce.number().int().min(1, 'Montant strictement positif (Ariary)'),
  date_prelevement: isoDate,
  destinataire: z.string().trim().max(200).optional(),
  motif: z.string().trim().optional(),
  mode_paiement_id: z.coerce.number().int().min(0).optional(),
  reference: z.string().trim().max(100).optional(),
});

export type PrelevementFormValues = z.infer<typeof prelevementFormSchema>;

export interface PrelevementCreatePayload {
  associe_id: number;
  type: 'RETRAIT' | 'VERSEMENT_FIXE' | 'SUPPLEMENT';
  montant: number;
  date_prelevement: string;
  date_a_completer: false;
  destinataire: string | null;
  motif: string | null;
  mode_paiement_id: number | null;
  reference: string | null;
}

function positiveOrNull(v: number | undefined): number | null {
  return v !== undefined && v > 0 ? v : null;
}

export function toPrelevementPayload(
  values: PrelevementFormValues,
): PrelevementCreatePayload {
  const emptyToNull = (v: string | undefined): string | null => {
    if (v === undefined) return null;
    const t = v.trim();
    return t === '' ? null : t;
  };
  return {
    associe_id: values.associe_id,
    type: values.type,
    montant: values.montant,
    date_prelevement: values.date_prelevement,
    date_a_completer: false,
    destinataire: emptyToNull(values.destinataire),
    motif: emptyToNull(values.motif),
    mode_paiement_id: positiveOrNull(values.mode_paiement_id),
    reference: emptyToNull(values.reference),
  };
}