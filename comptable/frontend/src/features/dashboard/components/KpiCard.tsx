import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';

type Tone = 'neutral' | 'success' | 'warning' | 'danger' | 'info';

const TONES: Record<Tone, string> = {
  neutral: 'text-foreground',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
  info: 'text-info',
};

interface Props {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: Tone;
  icon?: ReactNode;
}

export function KpiCard({ label, value, hint, tone = 'neutral', icon }: Props) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-2">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          {icon && <span className="text-muted-foreground">{icon}</span>}
        </div>
        <p className={cn('mt-1 text-xl font-semibold tabular', TONES[tone])}>
          {value}
        </p>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}