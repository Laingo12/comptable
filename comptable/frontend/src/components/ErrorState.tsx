import { AlertOctagon } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  title?: string;
  message?: string;
  onRetry?: () => void;
  compact?: boolean;
}

export function ErrorState({
  title = 'Une erreur est survenue', message, onRetry, compact,
}: Props) {
  return (
    <div
      role="alert"
      className={compact
        ? 'py-6 text-center'
        : 'flex flex-col items-center justify-center py-12 text-center'}
    >
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-danger/10 text-danger">
        <AlertOctagon className="h-5 w-5" aria-hidden="true" />
      </div>
      <p className="text-sm font-medium">{title}</p>
      {message && <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>}
      {onRetry && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
          Réessayer
        </Button>
      )}
    </div>
  );
}