import { cn } from '@/lib/utils';
import { formatAr } from '@/lib/format';

interface Props {
  value: number | null | undefined;
  align?: boolean;
  highlightNegative?: boolean;
  className?: string;
}

export function MoneyCell({
  value, align = true, highlightNegative = true, className,
}: Props) {
  const isNegative = typeof value === 'number' && value < 0;
  return (
    <span
      className={cn(
        'tabular whitespace-nowrap',
        align && 'block text-right',
        isNegative && highlightNegative && 'font-medium text-danger',
        className,
      )}
      data-negative={isNegative || undefined}
    >
      {formatAr(value)}
    </span>
  );
}