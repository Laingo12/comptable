import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface Props {
  title?: string;
  message?: string;
  icon?: ReactNode;
  action?: ReactNode;
  compact?: boolean;
}

export function EmptyState({
  title = 'Aucun élément', message, icon, action, compact,
}: Props) {
  return (
    <div
      className={compact
        ? 'py-6 text-center'
        : 'flex flex-col items-center justify-center py-12 text-center'}
    >
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-muted text-muted-foreground">
        {icon ?? <Inbox className="h-5 w-5" aria-hidden="true" />}
      </div>
      <p className="text-sm font-medium">{title}</p>
      {message && <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}