import { useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { Ban, PiggyBank, Plus } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/PageHeader';
import { DataTable } from '@/components/DataTable';
import { EmptyState } from '@/components/EmptyState';
import { MoneyCell } from '@/components/MoneyCell';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { formatAr, formatDate } from '@/lib/format';
import { useAuth } from '@/features/auth/useAuth';
import { caisseFgApi, type CaisseFgRead } from '../api';
import { caisseFgListFiltersSchema, type CaisseFgListFilters } from '../schemas';

function readFilters(sp: URLSearchParams): CaisseFgListFilters {
  const parsed = caisseFgListFiltersSchema.safeParse({
    mois_id: sp.get('mois_id') ?? undefined,
    sens: sp.get('sens') ?? undefined,
    date_from: sp.get('date_from') ?? undefined,
    date_to: sp.get('date_to') ?? undefined,
    include_annules: sp.get('include_annules') === 'true',
    sort: sp.get('sort') ?? 'date_operation:desc',
    page: sp.get('page') ?? 1,
    page_size: sp.get('page_size') ?? 20,
  });
  return parsed.success ? parsed.data : { page: 1, page_size: 20, include_annules: false };
}

export function CaisseFgListPage() {
  const [sp, setSp] = useSearchParams();
  const filters = readFilters(sp);
  const { can } = useAuth();
  const [annulerId, setAnnulerId] = useState<number | null>(null);

  const query = useQuery({
    queryKey: ['caisse-fg', filters],
    queryFn: () => caisseFgApi.list(filters),
    placeholderData: keepPreviousData,
  });

  const updateFilters = (patch: Partial<CaisseFgListFilters>) => {
    const next = new URLSearchParams(sp);
    for (const [k, v] of Object.entries(patch)) {
      if (v === undefined || v === null || v === '' || v === false) next.delete(k);
      else next.set(k, String(v));
    }
    setSp(next, { replace: true });
  };

  const columns = useMemo<ColumnDef<CaisseFgRead, unknown>[]>(() => [
    {
      accessorKey: 'date_operation',
      header: 'Date',
      meta: { sortable: true, sortField: 'date_operation' },
      cell: ({ row }) => (
        <span className="tabular">{formatDate(row.original.date_operation)}</span>
      ),
    },
    {
      accessorKey: 'libelle',
      header: 'Libellé',
      cell: ({ row }) => <span className="font-medium">{row.original.libelle}</span>,
    },
    {
      accessorKey: 'sens',
      header: 'Sens',
      cell: ({ row }) => (
        row.original.sens === 'ENTREE'
          ? <Badge variant="success" className="text-[10px]">Entrée</Badge>
          : <Badge variant="destructive" className="text-[10px]">Sortie</Badge>
      ),
    },
    {
      accessorKey: 'montant',
      header: 'Montant',
      meta: { sortable: true, sortField: 'montant', align: 'right' },
      cell: ({ row }) => {
        const isAnnulation = row.original.parent_mouvement_id !== null;
        const sensEffectif: 'ENTREE' | 'SORTIE' = isAnnulation
          ? (row.original.sens === 'ENTREE' ? 'SORTIE' : 'ENTREE')
          : row.original.sens;
        return (
          <span className={sensEffectif === 'ENTREE' ? 'text-success tabular' : 'text-danger tabular'}>
            {sensEffectif === 'ENTREE' ? '+' : '−'}
            {' '}{formatAr(row.original.montant)}
          </span>
        );
      },
    },
    {
      accessorKey: 'reference',
      header: 'Référence',
      cell: ({ row }) => (
        <span className="tabular text-xs">{row.original.reference ?? '—'}</span>
      ),
    },
    {
      id: 'statut',
      header: 'Statut',
      cell: ({ row }) => {
        const c = row.original;
        if (c.parent_mouvement_id !== null) {
          return <Badge variant="secondary" className="text-[10px]">Annulation</Badge>;
        }
        return <Badge variant="outline" className="text-[10px]">Valide</Badge>;
      },
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => {
        const c = row.original;
        const isAnnulation = c.parent_mouvement_id !== null;
        if (isAnnulation || !can('caisse_fg', 'annuler')) return null;
        return (
          <div className="flex justify-end">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setAnnulerId(c.id)}
              aria-label={`Annuler l'opération ${c.id}`}
            >
              <Ban className="h-4 w-4" />
            </Button>
          </div>
        );
      },
    },
  ], [can]);

  return (
    <div>
      <PageHeader
        title="Caisse FG"
        subtitle="Sous-registre de la caisse frais généraux"
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Caisse FG' }]}
        actions={
          can('caisse_fg', 'create') && (
            <Button asChild>
              <Link to="/caisse-fg/nouveau">
                <Plus className="h-4 w-4" /> Nouvelle opération
              </Link>
            </Button>
          )
        }
      />

      <Card className="mb-4">
        <CardContent className="pt-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <Label htmlFor="f-sens">Sens</Label>
              <select
                id="f-sens"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.sens ?? ''}
                onChange={(e) => updateFilters({
                  sens: (e.target.value as 'ENTREE' | 'SORTIE') || undefined,
                  page: 1,
                })}
              >
                <option value="">Tous</option>
                <option value="ENTREE">Entrées</option>
                <option value="SORTIE">Sorties</option>
              </select>
            </div>
            <div>
              <Label htmlFor="f-from">Du</Label>
              <Input
                id="f-from"
                type="date"
                value={filters.date_from ?? ''}
                onChange={(e) => updateFilters({ date_from: e.target.value || undefined, page: 1 })}
              />
            </div>
            <div>
              <Label htmlFor="f-to">Au</Label>
              <Input
                id="f-to"
                type="date"
                value={filters.date_to ?? ''}
                onChange={(e) => updateFilters({ date_to: e.target.value || undefined, page: 1 })}
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.include_annules ?? false}
                  onChange={(e) => updateFilters({
                    include_annules: e.target.checked || undefined,
                    page: 1,
                  })}
                />
                Inclure les annulations
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      <DataTable<CaisseFgRead>
        data={query.data?.items ?? []}
        columns={columns}
        total={query.data?.total ?? 0}
        page={query.data?.page ?? filters.page}
        pageSize={query.data?.page_size ?? filters.page_size}
        onPageChange={(p) => updateFilters({ page: p })}
        sort={filters.sort}
        onSortChange={(s) => updateFilters({ sort: s, page: 1 })}
        loading={query.isLoading}
        error={query.error instanceof Error ? query.error : null}
        onRetry={() => query.refetch()}
        empty={
          <EmptyState
            icon={<PiggyBank className="h-5 w-5" />}
            title="Aucune opération"
            message="Aucune opération ne correspond à ces filtres."
          />
        }
        ariaLabel="Liste des opérations de la caisse FG"
      />

      <ConfirmDialog
        open={annulerId !== null}
        title="Annuler l'opération"
        description="Un mouvement inverse sera créé (sens opposé). L'opération d'origine reste immuable."
        confirmLabel="Annuler l'opération"
        onCancel={() => setAnnulerId(null)}
        onConfirm={async (motif) => {
          if (annulerId === null) return;
          try {
            await caisseFgApi.annuler(annulerId, motif);
            toast.success('Opération annulée');
            setAnnulerId(null);
            await query.refetch();
          } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Erreur');
          }
        }}
      />
    </div>
  );
}