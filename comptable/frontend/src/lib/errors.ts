import { AxiosError } from 'axios';
import { toast } from 'sonner';

export interface FieldError { field: string; message: string }

export interface ParsedApiError {
  status: number;
  message: string;
  fields: FieldError[];
}

interface FastApiValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export function parseApiError(err: unknown): ParsedApiError {
  if (err instanceof AxiosError && err.response) {
    const { status, data } = err.response;
    const detail = (data as { detail?: unknown })?.detail;

    // 422 — erreur de validation FastAPI, une entrée par champ
    if (status === 422 && Array.isArray(detail)) {
      const fields = (detail as FastApiValidationError[]).map((d) => ({
        field: d.loc.filter((p) => p !== 'body').join('.'),
        message: d.msg,
      }));
      return { status, message: 'Données invalides', fields };
    }
    if (typeof detail === 'string') return { status, message: detail, fields: [] };
    return { status, message: err.message, fields: [] };
  }
  if (err instanceof Error) return { status: 0, message: err.message, fields: [] };
  return { status: 0, message: 'Erreur inconnue', fields: [] };
}

export function toastApiError(err: unknown, opts?: { silent?: boolean }): ParsedApiError {
  const parsed = parseApiError(err);
  if (opts?.silent) return parsed;
  if (parsed.status === 403) toast.error("Accès refusé pour cette action.");
  else if (parsed.status === 401) toast.error("Session expirée.");
  else if (parsed.status === 409) toast.error(parsed.message || 'Conflit.');
  else if (parsed.status >= 500) toast.error('Erreur serveur. Réessayez plus tard.');
  else if (parsed.status === 422) toast.error(parsed.message || 'Données invalides.');
  else toast.error(parsed.message || 'Erreur.');
  return parsed;
}