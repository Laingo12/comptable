import { useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { Ban, Plus, Wallet } from 'lucide-react';
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
import { formatDate } from '@/lib/format';
import { useAuth } from '@/features/auth/useAuth';
import { associesApi } from '@/features/associes/api';
import { prelevementsApi, type PrelevementRead } from '../api';
import {
  prelevementListFiltersSchema,
  type PrelevementListFilters,
} from '../schemas';

function readFilters(sp: URLSearchParams): PrelevementListFilters {
  const parsed = prelevementListFiltersSchema.safeParse({
    associe_id: sp.get('associe_id') ?? undefined,
    mois_id: sp.get('mois_id') ?? undefined,
    type: sp.get('type') ?? undefined,
    date_from: sp.get('date_from') ?? undefined,
    date_to: sp.get('date_to') ?? undefined,
    include_annules: sp.get('include_annules') === 'true',
    sort: sp.get('sort') ?? 'date_prelevement:desc',
    page: sp.get('page') ?? 1,
    page_size: sp.get('page_size') ?? 20,
  });
  return parsed.success ? parsed.data : { page: 1, page_size: 20, include_annules: false };
}

export function PrelevementsListPage() {
  const [sp, setSp] = useSearchParams();
  const filters = readFilters(sp);
  const { can } = useAuth();
  const [annulerId, setAnnulerId] = useState<number | null>(null);

  const query = useQuery({
    queryKey: ['prelevements', filters],
    queryFn: () => prelevementsApi.list(filters),
    placeholderData: keepPreviousData,
  });

  const associesQuery = useQuery({
    queryKey: ['associes'],
    queryFn: associesApi.list,
    staleTime: 5 * 60_000,
  });

  const updateFilters = (patch: Partial<PrelevementListFilters>) => {
    const next = new URLSearchParams(sp);
    for (const [k, v] of Object.entries(patch)) {
      if (v === undefined || v === null || v === '' || v === false) next.delete(k);
      else next.set(k, String(v));
    }
    setSp(next, { replace: true });
  };

  const columns = useMemo<ColumnDef<PrelevementRead, unknown>[]>(() => {
    const associeNom = (id: number) =>
      associesQuery.data?.find((a) => a.id === id)?.nom ?? `#${id}`;

    return [
      {
        accessorKey: 'date_prelevement',
        header: 'Date',
        meta: { sortable: true, sortField: 'date_prelevement' },
        cell: ({ row }) => (
          <span className="tabular">{formatDate(row.original.date_prelevement)}</span>
        ),
      },
      {
        accessorKey: 'associe_id',
        header: 'Associé',
        cell: ({ row }) => associeNom(row.original.associe_id),
      },
      {
        accessorKey: 'type',
        header: 'Type',
        cell: ({ row }) => (
          <Badge variant="outline" className="text-[10px]">
            {row.original.type}
          </Badge>
        ),
      },
      {
        accessorKey: 'montant',
        header: 'Montant',
        meta: { sortable: true, sortField: 'montant', align: 'right' },
        cell: ({ row }) => <MoneyCell value={row.original.montant} />,
      },
      {
        accessorKey: 'destinataire',
        header: 'Destinataire',
        cell: ({ row }) => row.original.destinataire ?? '—',
      },
      {
        accessorKey: 'motif',
        header: 'Motif',
        cell: ({ row }) => (
          <span className="text-xs text-muted-foreground">{row.original.motif ?? '—'}</span>
        ),
      },
      {
        id: 'statut',
        header: 'Statut',
        cell: ({ row }) => {
          const p = row.original;
          if (p.parent_prelevement_id !== null) {
            return <Badge variant="secondary" className="text-[10px]">Annulation</Badge>;
          }
          return <Badge variant="success" className="text-[10px]">Valide</Badge>;
        },
      },
      {
        id: 'actions',
        header: '',
        cell: ({ row }) => {
          const p = row.original;
          const isAnnulation = p.parent_prelevement_id !== null;
          if (isAnnulation || !can('prelevements', 'annuler')) return null;
          return (
            <div className="flex justify-end">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setAnnulerId(p.id)}
                aria-label={`Annuler le prélèvement ${p.id}`}
              >
                <Ban className="h-4 w-4" />
              </Button>
            </div>
          );
        },
      },
    ];
  }, [associesQuery.data, can]);

  return (
    <div>
      <PageHeader
        title="Prélèvements"
        subtitle={
          query.data
            ? `${query.data.total} prélèvement${query.data.total > 1 ? 's' : ''}`
            : undefined
        }
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Prélèvements' }]}
        actions={
          can('prelevements', 'create') && (
            <Button asChild>
              <Link to="/prelevements/nouveau">
                <Plus className="h-4 w-4" /> Nouveau prélèvement
              </Link>
            </Button>
          )
        }
      />

      <Card className="mb-4">
        <CardContent className="pt-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <Label htmlFor="f-associe">Associé</Label>
              <select
                id="f-associe"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.associe_id ?? ''}
                onChange={(e) => updateFilters({
                  associe_id: e.target.value ? Number(e.target.value) : undefined,
                  page: 1,
                })}
              >
                <option value="">Tous</option>
                {associesQuery.data?.map((a) => (
                  <option key={a.id} value={a.id}>{a.nom}</option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="f-type">Type</Label>
              <select
                id="f-type"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.type ?? ''}
                onChange={(e) => updateFilters({
                  type: (e.target.value as PrelevementListFilters['type']) || undefined,
                  page: 1,
                })}
              >
                <option value="">Tous</option>
                <option value="RETRAIT">Retrait</option>
                <option value="VERSEMENT_FIXE">Versement fixe</option>
                <option value="SUPPLEMENT">Supplément</option>
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

      <DataTable<PrelevementRead>
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
            icon={<Wallet className="h-5 w-5" />}
            title="Aucun prélèvement"
            message="Aucun prélèvement ne correspond à ces filtres."
          />
        }
        ariaLabel="Liste des prélèvements"
      />

      <ConfirmDialog
        open={annulerId !== null}
        title="Annuler le prélèvement"
        description="Une écriture inverse sera créée. Le prélèvement d'origine reste immuable."
        confirmLabel="Annuler le prélèvement"
        onCancel={() => setAnnulerId(null)}
        onConfirm={async (motif) => {
          if (annulerId === null) return;
          try {
            await prelevementsApi.annuler(annulerId, motif);
            toast.success('Prélèvement annulé');
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