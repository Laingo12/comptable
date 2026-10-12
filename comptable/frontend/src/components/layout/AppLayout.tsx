import { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

const STORAGE_KEY = 'smartkids.sidebar.collapsed';

export function AppLayout() {
  const [collapsed, setCollapsed] = useState<boolean>(
    () => localStorage.getItem(STORAGE_KEY) === '1',
  );
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, collapsed ? '1' : '0');
  }, [collapsed]);

  return (
    <div className="flex h-screen bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
      >
        Aller au contenu principal
      </a>

      <aside
        className="hidden shrink-0 border-r bg-card transition-[width] duration-200 md:block"
        style={{ width: collapsed ? 64 : 240 }}
      >
        <Sidebar collapsed={collapsed} />
      </aside>

      <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 md:hidden" />
          <Dialog.Content
            className="fixed left-0 top-0 z-50 h-full w-64 border-r bg-card shadow-lg md:hidden"
            aria-label="Navigation"
          >
            <div className="flex items-center justify-end p-2">
              <Dialog.Close asChild>
                <button
                  type="button" aria-label="Fermer la navigation"
                  className="rounded-md p-2 hover:bg-muted"
                >
                  <X className="h-5 w-5" />
                </button>
              </Dialog.Close>
            </div>
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          collapsed={collapsed}
          onToggleCollapse={() => setCollapsed((c) => !c)}
          onOpenMobile={() => setMobileOpen(true)}
        />
        <main
          id="main-content" tabIndex={-1}
          className="flex-1 overflow-y-auto p-4 md:p-6"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}