import { z } from 'zod';

export const eleveListFiltersSchema = z.object({
  q: z.string().max(200).optional(),
  famille_id: z.coerce.number().int().positive().optional(),
  sort: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  page_size: z.coerce.number().int().min(1).max(200).default(20),
});

export type EleveListFilters = z.infer<typeof eleveListFiltersSchema>;

// --- Formulaire création / édition élève ------------------------------

const isoDate = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, 'Format attendu : AAAA-MM-JJ');

export const eleveFormSchema = z.object({
  // Matricule : vide en création → généré par le backend. Jamais modifiable en édition.
  matricule: z.string().trim().max(50).optional(),
  nom: z.string().trim().min(1, 'Nom requis').max(200),
  prenoms: z.string().trim().min(1, 'Prénoms requis').max(200),
  // Le select utilise '' pour « aucun ». On convertit en null plus bas.
  sexe: z.enum(['', 'M', 'F']).transform((v) => (v === '' ? null : v)),
  date_naissance: z
    .union([isoDate, z.literal('')])
    .transform((v) => (v === '' ? null : v)),
  famille_id: z
    .union([z.coerce.number().int().positive(), z.literal('')])
    .transform((v) => (v === '' ? null : (v as number))),
});

export type EleveFormValues = z.input<typeof eleveFormSchema>;
export type EleveFormOutput = z.output<typeof eleveFormSchema>;