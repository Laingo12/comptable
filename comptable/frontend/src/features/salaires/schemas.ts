import { z } from 'zod';

const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Format AAAA-MM-JJ attendu');

// --- Génération mensuelle ---

export const genererSalairesSchema = z.object({
  mois_id: z.coerce.number().int().positive('Mois requis'),
  annee_scolaire_id: z.coerce.number().int().positive().optional(),
  montant_brut_par_defaut: z.coerce.number().int().min(0).optional(),
});

export type GenererSalairesValues = z.infer<typeof genererSalairesSchema>;

// --- Paiement salaire (70 / 30) ---

export const paiementSalaireSchema = z.object({
  salaire_mensuel_id: z.coerce.number().int().positive(),
  type_part: z.enum(['AVANCE_70', 'SOLDE_30']),
  montant: z.coerce.number().int().min(1, 'Montant strictement positif (Ariary)'),
  date_paiement: isoDate,
  mode_paiement_id: z.coerce.number().int().min(0).optional(),
  reference: z.string().trim().max(100).optional(),
  observation: z.string().trim().optional(),
});

export type PaiementSalaireValues = z.infer<typeof paiementSalaireSchema>;

export interface PaiementSalairePayload {
  salaire_mensuel_id: number;
  type_part: 'AVANCE_70' | 'SOLDE_30';
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

export function toPaiementSalairePayload(
  values: PaiementSalaireValues,
): PaiementSalairePayload {
  const emptyToNull = (v: string | undefined): string | null => {
    if (v === undefined) return null;
    const t = v.trim();
    return t === '' ? null : t;
  };
  return {
    salaire_mensuel_id: values.salaire_mensuel_id,
    type_part: values.type_part,
    montant: values.montant,
    date_paiement: values.date_paiement,
    date_a_completer: false,
    mode_paiement_id: positiveOrNull(values.mode_paiement_id),
    reference: emptyToNull(values.reference),
    observation: emptyToNull(values.observation),
  };
}