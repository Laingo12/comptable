import { ArrowDownRight, ArrowUpRight, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

type Qualificatif = 'NORMAL' | 'AVANCE' | 'RETARD';

const SPECS: Record<Qualificatif, { label: string; Icon: React.ComponentType<{ className?: string }>; classes: string }> = {
  NORMAL: {
    label: 'Normal',
    Icon: Minus,
    classes: 'bg-muted text-muted-foreground ring-1 ring-inset ring-border',
  },
  AVANCE: {
    label: 'Avance',
    Icon: ArrowUpRight,
    classes: 'bg-info/10 text-info ring-1 ring-inset ring-info/30',
  },
  RETARD: {
    label: 'Retard',
    Icon: ArrowDownRight,
    classes: 'bg-danger/10 text-danger ring-1 ring-inset ring-danger/30',
  },
};

interface Props { value: string; className?: string }

export function QualificatifBadge({ value, className }: Props) {
  const key = (['NORMAL', 'AVANCE', 'RETARD'].includes(value) ? value : 'NORMAL') as Qualificatif;
  const { label, Icon, classes } = SPECS[key];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide',
        classes,
        className,
      )}
      aria-label={`Qualificatif : ${label}`}
    >
      <Icon className="h-3 w-3" aria-hidden="true" />
      {label}
    </span>
  );
}