import {
  AlertTriangle, Ban, CheckCircle2, CircleDot, CircleHelp,
  Clock, FastForward, XCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export type StatusKey =
  | 'PAYE' | 'PARTIEL' | 'IMPAYE'
  | 'ECHU' | 'AVANCE' | 'RETARD'
  | 'ANNULE' | 'A_COMPLETER';

interface Spec {
  label: string;
  Icon: React.ComponentType<{ className?: string }>;
  classes: string;
}

const SPECS: Record<StatusKey, Spec> = {
  PAYE: {
    label: 'Payé',
    Icon: CheckCircle2,
    classes: 'bg-success/10 text-success ring-1 ring-inset ring-success/30',
  },
  PARTIEL: {
    label: 'Partiel',
    Icon: CircleDot,
    classes: 'bg-warning/10 text-warning ring-1 ring-inset ring-warning/30',
  },
  IMPAYE: {
    label: 'Impayé',
    Icon: XCircle,
    classes: 'bg-danger/10 text-danger ring-1 ring-inset ring-danger/30',
  },
  ECHU: {
    label: 'Échu',
    Icon: Clock,
    classes: 'bg-warning/10 text-warning ring-1 ring-inset ring-warning/30',
  },
  AVANCE: {
    label: 'Avance',
    Icon: FastForward,
    classes: 'bg-info/10 text-info ring-1 ring-inset ring-info/30',
  },
  RETARD: {
    label: 'En retard',
    Icon: AlertTriangle,
    classes: 'bg-danger/10 text-danger ring-1 ring-inset ring-danger/30',
  },
  ANNULE: {
    label: 'Annulé',
    Icon: Ban,
    classes: 'bg-muted text-muted-foreground ring-1 ring-inset ring-border',
  },
  A_COMPLETER: {
    label: 'À compléter',
    Icon: CircleHelp,
    classes: 'bg-accent/15 text-accent-foreground ring-1 ring-inset ring-accent/40',
  },
};

interface Props {
  status: StatusKey;
  hint?: string;
  className?: string;
}

export function StatusBadge({ status, hint, className }: Props) {
  const { Icon, label, classes } = SPECS[status];
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
      <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
      <span>{label}</span>
      {hint && <span className="text-[10px] opacity-80">· {hint}</span>}
    </span>
  );
}