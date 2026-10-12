import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Users2, Receipt } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/features/auth/useAuth';
import type { Action, Resource } from '@/lib/permissions';

interface Item {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  resource: Resource;
  action: Action;
}

const ITEMS: Item[] = [
  { to: '/', label: 'Tableau de bord', icon: LayoutDashboard, resource: 'dashboard', action: 'read' },
  { to: '/eleves', label: 'Élèves', icon: Users, resource: 'eleves', action: 'read' },
  { to: '/familles', label: 'Familles', icon: Users2, resource: 'familles', action: 'read' },
  { to: '/paiements', label: 'Paiements', icon: Receipt, resource: 'paiements', action: 'read' },
];

interface Props {
  collapsed?: boolean;
  onNavigate?: () => void;
}

export function Sidebar({ collapsed = false, onNavigate }: Props) {
  const { can } = useAuth();
  const visible = ITEMS.filter((it) => can(it.resource, it.action));

  return (
    <nav className="flex h-full flex-col p-2" aria-label="Navigation principale">
      <div className={cn(
        'flex h-10 items-center px-3 text-sm font-semibold tracking-tight text-primary',
        collapsed && 'justify-center',
      )}>
        {collapsed ? 'SK' : 'SMART KIDS'}
      </div>
      <ul className="mt-2 space-y-1">
        {visible.map((it) => (
          <li key={it.to}>
            <NavLink
              to={it.to}
              end={it.to === '/'}
              onClick={onNavigate}
              title={collapsed ? it.label : undefined}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground',
                  'hover:bg-muted hover:text-foreground',
                  isActive && 'bg-primary/10 text-primary font-medium',
                  collapsed && 'justify-center px-2',
                )
              }
            >
              <it.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              {!collapsed && <span>{it.label}</span>}
              {collapsed && <span className="sr-only">{it.label}</span>}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}