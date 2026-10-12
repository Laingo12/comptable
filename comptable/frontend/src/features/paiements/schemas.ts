import { z } from 'zod';

const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Format AAAA-MM-JJ attendu');

// --- Liste ---

export const paiementListFiltersSchema = z.object({
  type_paiement_id: z.coerce.number().int().positive().optional(),
  inscription_id: z.coerce.number().int().positive().optional(),
  mois_concerne_id: z.coerce.number().int().positive().optional(),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  include_annules: z.coerce.boolean().optional().default(false),
  sort: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(20),
});

export type PaiementListFilters = z.infer<typeof paiementListFiltersSchema>;

// --- Formulaire de création ---

export const paiementFormSchema = z.object({
  inscription_id: z.coerce.number().int().positive('Inscription requise'),
  type_paiement_id: z.coerce.number().int().positive('Type requis'),
  // 0 = « non choisi ». Le check ECOLAGE est fait au submit.
  mois_concerne_id: z.coerce.number().int().min(0).optional(),
  montant: z.coerce.number().int().min(1, 'Montant strictement positif (Ariary)'),
  date_paiement: isoDate,
  // 0 = « non renseigné » (option par défaut du select).
  mode_paiement_id: z.coerce.number().int().min(0).optional(),
  reference: z.string().trim().max(100).optional(),
  observation: z.string().trim().optional(),
});

export type PaiementFormValues = z.infer<typeof paiementFormSchema>;

/** Payload envoyé à l'API. */
export interface PaiementCreatePayload {
  inscription_id: number;
  type_paiement_id: number;
  mois_concerne_id: number | null;
  montant: number;
  date_paiement: string;
  date_a_completer: false;
  mode_paiement_id: number | null;
  reference: string | null;
  observation: string | null;
}

function positiveOrNull(v: number | undefined): number | null {
  return v !== undefined && v > 0 ? v : null;
}

export function toPaiementPayload(values: PaiementFormValues): PaiementCreatePayload {
  const emptyToNull = (v: string | undefined): string | null => {
    if (v === undefined) return null;
    const t = v.trim();
    return t === '' ? null : t;
  };
  return {
    inscription_id: values.inscription_id,
    type_paiement_id: values.type_paiement_id,
    mois_concerne_id: positiveOrNull(values.mois_concerne_id),
    montant: values.montant,
    date_paiement: values.date_paiement,
    date_a_completer: false,
    mode_paiement_id: positiveOrNull(values.mode_paiement_id),
    reference: emptyToNull(values.reference),
    observation: emptyToNull(values.observation),
  };
}

// --- Annulation ---

export const annulationSchema = z.object({
  motif: z
    .string()
    .trim()
    .min(3, 'Motif requis (3 caractères minimum)')
    .max(500, 'Motif trop long (500 caractères max)'),
});

export type AnnulationValues = z.infer<typeof annulationSchema>;