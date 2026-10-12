import { cn } from '@/lib/utils';

export type StatusKey =
  | 'PAYE' | 'PARTIEL' | 'IMPAYE'
  | 'ECHU' | 'AVANCE' | 'RETARD'
  | 'ANNULE' | 'A_COMPLETER';

// ---------------------------------------------------------------------
// Icônes inline (SVG) — plus de dépendance à lucide-react pour ce
// composant. Style aligné sur lucide (stroke 2, linecap rond, 24x24).
// ---------------------------------------------------------------------

interface IconProps { className?: string }

function IconCheck({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" className={className}
         aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

function IconDot({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" className={className}
         aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="3" fill="currentColor" />
    </svg>
  );
}

function IconXCircle({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" className={className}
         aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="m15 9-6 6M9 9l6 6" />
    </svg>
  );
}

function IconClock({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" className={className}
         aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </svg>
  );
}

function IconFastForward({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" className={className}
         aria-hidden="true">
      <path d="M13 19l9-7-9-7v14z" />
      <path d="M2 19l9-7-9-7v14z" />
    </svg>
  );
}

function IconAlertTriangle({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" className={className}
         aria-hidden="true">
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

function IconBan({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" className={className}
         aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="m4.93 4.93 14.14 14.14" />
    </svg>
  );
}

function IconHelpCircle({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" className={className}
         aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <path d="M12 17h.01" />
    </svg>
  );
}

// ---------------------------------------------------------------------

interface Spec {
  label: string;
  Icon: React.ComponentType<IconProps>;
  classes: string;
}

/**
 * Chaque statut combine : (1) fond clair + texte foncé → contraste AA,
 * (2) une icône + un label → lisible sans dépendre de la couleur seule.
 */
const SPECS: Record<StatusKey, Spec> = {
  PAYE: {
    label: 'Payé',
    Icon: IconCheck,
    classes: 'bg-success-soft text-success-dark ring-1 ring-inset ring-success/40',
  },
  PARTIEL: {
    label: 'Partiel',
    Icon: IconDot,
    classes: 'bg-warning-soft text-warning-dark ring-1 ring-inset ring-warning/40',
  },
  IMPAYE: {
    label: 'Impayé',
    Icon: IconXCircle,
    classes: 'bg-danger-soft text-danger-dark ring-1 ring-inset ring-danger/40',
  },
  ECHU: {
    label: 'Échu',
    Icon: IconClock,
    classes: 'bg-danger-soft text-danger-dark ring-1 ring-inset ring-danger/40',
  },
  AVANCE: {
    label: 'Avance',
    Icon: IconFastForward,
    classes: 'bg-info-soft text-info-dark ring-1 ring-inset ring-info/40',
  },
  RETARD: {
    label: 'En retard',
    Icon: IconAlertTriangle,
    classes: 'bg-warning-soft text-warning-dark ring-1 ring-inset ring-warning/40',
  },
  ANNULE: {
    label: 'Annulé',
    Icon: IconBan,
    classes: 'bg-muted text-muted-foreground ring-1 ring-inset ring-border',
  },
  A_COMPLETER: {
    label: 'À compléter',
    Icon: IconHelpCircle,
    classes: 'bg-accent-soft text-accent-dark ring-1 ring-inset ring-accent/40',
  },
};

interface Props {
  status: StatusKey;
  hint?: string;
  className?: string;
}

export function StatusBadge({ status, hint, className }: Props) {
  const spec = SPECS[status];
  // Défense en profondeur : si un statut inconnu arrive (donnée backend
  // non prévue), on affiche un badge neutre au lieu de planter.
  if (!spec) {
    return (
      <span
        role="status"
        aria-label={`Statut inconnu : ${status}`}
        className={cn(
          'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
          'bg-muted text-muted-foreground ring-1 ring-inset ring-border',
          className,
        )}
      >
        {status}
      </span>
    );
  }

  const { Icon, label, classes } = spec;
  const aria = hint ? `${label} — ${hint}` : label;

  return (
    <span
      role="status"
      aria-label={aria}
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
        classes,
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span>{label}</span>
      {hint && <span className="text-[10px] opacity-80">· {hint}</span>}
    </span>
  );
}