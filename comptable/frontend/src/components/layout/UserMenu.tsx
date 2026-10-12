import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { LogOut, User as UserIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/features/auth/useAuth';

export function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  const initials = user.full_name
    .split(/\s+/)
    .slice(0, 2)
    .map((p: string) => p.charAt(0).toUpperCase())
    .join('');

  const onLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <Button variant="ghost" className="gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
            {initials || <UserIcon className="h-4 w-4" />}
          </span>
          <span className="hidden text-sm sm:inline">{user.full_name}</span>
        </Button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={6}
          className="z-50 min-w-[220px] rounded-md border bg-card p-1 shadow-md"
        >
          <div className="px-3 py-2 text-xs text-muted-foreground">
            <div className="font-medium text-foreground">{user.full_name}</div>
            <div>{user.username} — {user.role}</div>
          </div>
          <DropdownMenu.Separator className="my-1 h-px bg-border" />
          <DropdownMenu.Item
            onSelect={onLogout}
            className="flex cursor-pointer items-center gap-2 rounded-sm px-3 py-2 text-sm outline-none hover:bg-accent focus:bg-accent"
          >
            <LogOut className="h-4 w-4" /> Déconnexion
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}