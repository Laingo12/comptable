import { useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { Ban, Plus, Receipt } from 'lucide-react';
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
import { referentielsApi } from '@/features/referentiels/api';
import { downloadReceipt } from '@/features/situation/api';
import { paiementsApi, type PaiementRead } from '../api';
import { paiementListFiltersSchema, type PaiementListFilters } from '../schemas';

function readFilters(sp: URLSearchParams): PaiementListFilters {
  const parsed = paiementListFiltersSchema.safeParse({
    type_paiement_id: sp.get('type_paiement_id') ?? undefined,
    inscription_id: sp.get('inscription_id') ?? undefined,
    mois_concerne_id: sp.get('mois_concerne_id') ?? undefined,
    date_from: sp.get('date_from') ?? undefined,
    date_to: sp.get('date_to') ?? undefined,
    include_annules: sp.get('include_annules') === 'true',
    sort: sp.get('sort') ?? 'date_paiement:desc',
    page: sp.get('page') ?? 1,
    page_size: sp.get('page_size') ?? 20,
  });
  return parsed.success ? parsed.data : { page: 1, page_size: 20, include_annules: false };
}

export function PaiementsListPage() {
  const [sp, setSp] = useSearchParams();
  const filters = readFilters(sp);
  const { can } = useAuth();

  const [annulerId, setAnnulerId] = useState<number | null>(null);
  const [busyReceipt, setBusyReceipt] = useState<number | null>(null);

  const query = useQuery({
    queryKey: ['paiements', filters],
    queryFn: () => paiementsApi.list(filters),
    placeholderData: keepPreviousData,
  });

  const typesQuery = useQuery({
    queryKey: ['referentiels', 'types-paiement'],
    queryFn: referentielsApi.typesPaiement,
    staleTime: 10 * 60_000,
  });

  const updateFilters = (patch: Partial<PaiementListFilters>) => {
    const next = new URLSearchParams(sp);
    for (const [k, v] of Object.entries(patch)) {
      if (v === undefined || v === null || v === '' || v === false) next.delete(k);
      else next.set(k, String(v));
    }
    setSp(next, { replace: true });
  };

  const onReceipt = async (p: PaiementRead) => {
    setBusyReceipt(p.id);
    try {
      await downloadReceipt(p.id, 'pdf');
    } catch {
      toast.error('Impossible de télécharger le reçu.');
    } finally {
      setBusyReceipt(null);
    }
  };

  const columns = useMemo<ColumnDef<PaiementRead, unknown>[]>(() => {
    // Défini DANS le useMemo pour satisfaire react-hooks/exhaustive-deps
    // (utilise typesQuery.data en closure).
    const typeLibelle = (id: number) =>
      typesQuery.data?.find((t) => t.id === id)?.libelle ?? `#${id}`;

    return [
      {
        accessorKey: 'date_paiement',
        header: 'Date',
        meta: { sortable: true, sortField: 'date_paiement' },
        cell: ({ row }) => (
          <span className="tabular">{formatDate(row.original.date_paiement)}</span>
        ),
      },
      {
        accessorKey: 'inscription_id',
        header: 'Inscription',
        cell: ({ row }) =>
          row.original.inscription_id ? (
            <Link
              to={`/inscriptions/${row.original.inscription_id}`}
              className="text-primary hover:underline"
            >
              #{row.original.inscription_id}
            </Link>
          ) : (
            '—'
          ),
      },
      {
        accessorKey: 'type_paiement_id',
        header: 'Type',
        cell: ({ row }) => typeLibelle(row.original.type_paiement_id),
      },
      {
        accessorKey: 'montant',
        header: 'Montant',
        meta: { sortable: true, sortField: 'montant', align: 'right' },
        cell: ({ row }) => <MoneyCell value={row.original.montant} />,
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
          const p = row.original;
          if (p.parent_paiement_id !== null) {
            return <Badge variant="secondary" className="text-[10px]">Annulation</Badge>;
          }
          if (p.motif_annulation) {
            return <Badge variant="destructive" className="text-[10px]">Annulé</Badge>;
          }
          return <Badge variant="success" className="text-[10px]">Valide</Badge>;
        },
      },
      {
        id: 'actions',
        header: '',
        cell: ({ row }) => {
          const p = row.original;
          const isAnnulation = p.parent_paiement_id !== null;
          const isAnnule = !!p.motif_annulation;
          return (
            <div className="flex justify-end gap-1">
              {!isAnnulation && (
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={busyReceipt === p.id}
                  onClick={() => onReceipt(p)}
                  aria-label={`Télécharger le reçu ${p.id}`}
                >
                  <Receipt className="h-4 w-4" />
                </Button>
              )}
              {!isAnnulation && !isAnnule && can('paiements', 'annuler') && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setAnnulerId(p.id)}
                  aria-label={`Annuler le paiement ${p.id}`}
                >
                  <Ban className="h-4 w-4" />
                </Button>
              )}
            </div>
          );
        },
      },
    ];
  }, [typesQuery.data, busyReceipt, can]);

  return (
    <div>
      <PageHeader
        title="Paiements"
        subtitle={
          query.data
            ? `${query.data.total} paiement${query.data.total > 1 ? 's' : ''}`
            : undefined
        }
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Paiements' }]}
        actions={
          can('paiements', 'create') && (
            <Button asChild>
              <Link to="/paiements/nouveau">
                <Plus className="h-4 w-4" /> Nouveau paiement
              </Link>
            </Button>
          )
        }
      />

      <Card className="mb-4">
        <CardContent className="pt-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <Label htmlFor="f-type">Type</Label>
              <select
                id="f-type"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.type_paiement_id ?? ''}
                onChange={(e) => updateFilters({
                  type_paiement_id: e.target.value ? Number(e.target.value) : undefined,
                  page: 1,
                })}
              >
                <option value="">Tous</option>
                {typesQuery.data?.map((t) => (
                  <option key={t.id} value={t.id}>{t.libelle}</option>
                ))}
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

      <DataTable<PaiementRead>
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
            title="Aucun paiement"
            message="Aucun paiement ne correspond à ces filtres."
          />
        }
        ariaLabel="Liste des paiements"
      />

      <ConfirmDialog
        open={annulerId !== null}
        title="Annuler le paiement"
        description="Une écriture inverse sera créée. Le paiement d'origine reste immuable et traçable."
        confirmLabel="Annuler le paiement"
        onCancel={() => setAnnulerId(null)}
        onConfirm={async (motif) => {
          if (annulerId === null) return;
          try {
            await paiementsApi.annuler(annulerId, motif);
            toast.success('Paiement annulé');
            setAnnulerId(null);
            await query.refetch();
          } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Erreur lors de l\'annulation');
          }
        }}
      />
    </div>
  );
}