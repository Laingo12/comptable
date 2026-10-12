const _AR = new Intl.NumberFormat('fr-MG', { maximumFractionDigits: 0 });
const _DATE = new Intl.DateTimeFormat('fr-FR', {
  timeZone: 'Indian/Antananarivo',
  year: 'numeric', month: '2-digit', day: '2-digit',
});
const _DATETIME = new Intl.DateTimeFormat('fr-FR', {
  timeZone: 'Indian/Antananarivo',
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit',
});

export function formatAr(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || !Number.isFinite(amount)) return '—';
  return `${_AR.format(Math.trunc(amount))} Ar`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : _DATE.format(d);
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : _DATETIME.format(d);
}
const _PCT = new Intl.NumberFormat('fr-FR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

/**
 * Formate un pourcentage déjà calculé (0..100) en français.
 * Ex : 50 → "50,0 %" ; 12.34 → "12,3 %".
 * N'ajoute PAS le signe % dans Intl (préférence : espace insécable avant).
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—';
  return `${_PCT.format(value)} %`;
}