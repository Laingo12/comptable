import { z } from 'zod';

const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Format AAAA-MM-JJ attendu');

export const chargeListFiltersSchema = z.object({
  mois_id: z.coerce.number().int().positive().optional(),
  categorie: z.enum(['FIXE', 'VARIABLE', 'AUTRE']).optional(),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  include_annules: z.coerce.boolean().optional().default(false),
  sort: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(20),
});

export type ChargeListFilters = z.infer<typeof chargeListFiltersSchema>;

export const chargeFormSchema = z.object({
  // 0 = non choisi. Rempli automatiquement par le trigger backend
  // (NON_DATE / HORS_ANNEE) ou dérivé de la date.
  mois_id: z.coerce.number().int().min(0).optional(),
  charge_catalogue_id: z.coerce.number().int().min(0).optional(),
  libelle: z.string().trim().min(1, 'Libellé requis').max(200),
  categorie: z.enum(['FIXE', 'VARIABLE', 'AUTRE']),
  montant: z.coerce.number().int().min(1, 'Montant strictement positif (Ariary)'),
  date_operation: isoDate,
  mode_paiement_id: z.coerce.number().int().min(0).optional(),
  reference: z.string().trim().max(100).optional(),
  observation: z.string().trim().optional(),
});

export type ChargeFormValues = z.infer<typeof chargeFormSchema>;

export interface ChargeCreatePayload {
  mois_id: number | null;
  charge_catalogue_id: number | null;
  libelle: string;
  categorie: 'FIXE' | 'VARIABLE' | 'AUTRE';
  montant: number;
  date_operation: string;
  date_a_completer: false;
  mode_paiement_id: number | null;
  reference: string | null;
  observation: string | null;
}

function positiveOrNull(v: number | undefined): number | null {
  return v !== undefined && v > 0 ? v : null;
}

export function toChargePayload(values: ChargeFormValues): ChargeCreatePayload {
  const emptyToNull = (v: string | undefined): string | null => {
    if (v === undefined) return null;
    const t = v.trim();
    return t === '' ? null : t;
  };
  return {
    mois_id: positiveOrNull(values.mois_id),
    charge_catalogue_id: positiveOrNull(values.charge_catalogue_id),
    libelle: values.libelle.trim(),
    categorie: values.categorie,
    montant: values.montant,
    date_operation: values.date_operation,
    date_a_completer: false,
    mode_paiement_id: positiveOrNull(values.mode_paiement_id),
    reference: emptyToNull(values.reference),
    observation: emptyToNull(values.observation),
  };
}