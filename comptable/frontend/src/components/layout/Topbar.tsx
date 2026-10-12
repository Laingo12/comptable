import { useQuery } from '@tanstack/react-query';
import { Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { UserMenu } from './UserMenu';
import { referentielsApi, type AnneeScolaireRead } from '@/features/referentiels/api';

interface Props {
  onToggleCollapse: () => void;
  onOpenMobile: () => void;
  collapsed: boolean;
}

export function Topbar({ onToggleCollapse, onOpenMobile, collapsed }: Props) {
  const anneeQuery = useQuery<AnneeScolaireRead>({
    queryKey: ['referentiels', 'annee-active'],
    queryFn: referentielsApi.anneeActive,
    staleTime: 30 * 60_000,
  });

  const label = anneeQuery.isLoading
    ? '…'
    : anneeQuery.isError || !anneeQuery.data
      ? 'Année non disponible'
      : `Année ${anneeQuery.data.libelle}`;

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-3 md:px-4">
      <div className="flex items-center gap-2">
        <Button
          variant="ghost" size="icon" className="md:hidden"
          onClick={onOpenMobile} aria-label="Ouvrir la navigation"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <Button
          variant="ghost" size="icon" className="hidden md:inline-flex"
          onClick={onToggleCollapse}
          aria-label={collapsed ? 'Déplier la navigation' : 'Replier la navigation'}
          aria-expanded={!collapsed}
        >
          {collapsed
            ? <PanelLeftOpen className="h-5 w-5" />
            : <PanelLeftClose className="h-5 w-5" />}
        </Button>
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <UserMenu />
    </header>
  );
}