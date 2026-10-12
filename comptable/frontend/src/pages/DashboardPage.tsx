import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { DashboardMensuelPage } from '@/features/dashboard/pages/DashboardMensuelPage';
import { DashboardAnnuelPage } from '@/features/dashboard/pages/DashboardAnnuelPage';

const TABS = [
  { to: '/', label: 'Mensuel' },
  { to: '/dashboard/annuel', label: 'Annuel' },
];

export function DashboardPage() {
  const location = useLocation();
  const isAnnuel = location.pathname.startsWith('/dashboard/annuel');

  return (
    <div>
      <nav className="mb-4 flex gap-1 border-b" aria-label="Vue du tableau de bord">
        {TABS.map((t) => {
          const active = t.to === '/' ? !isAnnuel : isAnnuel;
          return (
            <Link
              key={t.to}
              to={t.to}
              className={cn(
                '-mb-px border-b-2 px-3 py-2 text-sm',
                active
                  ? 'border-primary font-medium text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground',
              )}
              aria-current={active ? 'page' : undefined}
            >
              {t.label}
            </Link>
          );
        })}
      </nav>
      {isAnnuel ? <DashboardAnnuelPage /> : <DashboardMensuelPage />}
    </div>
  );
}