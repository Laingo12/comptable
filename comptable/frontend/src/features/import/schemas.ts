import { z } from 'zod';

/**
 * Contrat du formulaire d'import.
 * Le fichier est validé côté client (extension + taille) et côté serveur.
 */
export const importFormSchema = z.object({
  dry_run: z.boolean().default(false),
});

export type ImportFormValues = z.infer<typeof importFormSchema>;

/** Extensions acceptées. */
export const ACCEPTED_EXTENSIONS = ['.xlsx', '.xlsm'] as const;

/** Taille max du fichier : 10 Mo. */
export const MAX_FILE_SIZE = 10 * 1024 * 1024;

export function validateFile(file: File): string | null {
  const name = file.name.toLowerCase();
  const ext = name.slice(name.lastIndexOf('.'));
  if (!ACCEPTED_EXTENSIONS.includes(ext as (typeof ACCEPTED_EXTENSIONS)[number])) {
    return `Format non supporté. Attendu : ${ACCEPTED_EXTENSIONS.join(', ')}`;
  }
  if (file.size === 0) {
    return 'Fichier vide.';
  }
  if (file.size > MAX_FILE_SIZE) {
    return `Fichier trop volumineux (max ${Math.round(MAX_FILE_SIZE / 1024 / 1024)} Mo).`;
  }
  return null;
}