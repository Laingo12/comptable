import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { Users2, Plus } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';
import { useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/PageHeader';
import { DataTable } from '@/components/DataTable';
import { EmptyState } from '@/components/EmptyState';
import { useAuth } from '@/features/auth/useAuth';
import { famillesApi, type FamilleRead } from '../api';
import { familleListFiltersSchema, type FamilleListFilters } from '../schemas';

function readFilters(sp: URLSearchParams): FamilleListFilters {
  const parsed = familleListFiltersSchema.safeParse({
    q: sp.get('q') ?? undefined,
    sort: sp.get('sort') ?? undefined,
    page: sp.get('page') ?? 1,
    page_size: sp.get('page_size') ?? 20,
  });
  return parsed.success ? parsed.data : { page: 1, page_size: 20 };
}

export function FamillesListPage() {
  const [sp, setSp] = useSearchParams();
  const filters = readFilters(sp);
  const { can } = useAuth();

  const query = useQuery({
    queryKey: ['familles', filters],
    queryFn: () => famillesApi.list(filters),
    placeholderData: keepPreviousData,
  });

  const updateFilters = (patch: Partial<FamilleListFilters>) => {
    const next = new URLSearchParams(sp);
    for (const [k, v] of Object.entries(patch)) {
      if (v === undefined || v === null || v === '') next.delete(k);
      else next.set(k, String(v));
    }
    setSp(next, { replace: true });
  };

  const columns = useMemo<ColumnDef<FamilleRead, unknown>[]>(() => [
    {
      accessorKey: 'nom',
      header: 'Nom',
      meta: { sortable: true, sortField: 'nom' },
      cell: ({ row }) => (
        <Link to={`/familles/${row.original.id}`} className="font-medium hover:text-primary hover:underline">
          {row.original.nom}
        </Link>
      ),
    },
    {
      accessorKey: 'contact_principal',
      header: 'Contact',
      cell: ({ row }) => row.original.contact_principal ?? '—',
    },
    {
      accessorKey: 'telephone',
      header: 'Téléphone',
      cell: ({ row }) => (
        <span className="tabular">{row.original.telephone ?? '—'}</span>
      ),
    },
    {
      accessorKey: 'email',
      header: 'Email',
      cell: ({ row }) => row.original.email ?? '—',
    },
  ], []);

  return (
    <div>
      <PageHeader
        title="Familles"
        subtitle={
          query.data
            ? `${query.data.total} famille${query.data.total > 1 ? 's' : ''}`
            : undefined
        }
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Familles' }]}
        actions={
          can('familles', 'create') && (
            <Button asChild>
              <Link to="/familles/nouvelle">
                <Plus className="h-4 w-4" /> Nouvelle famille
              </Link>
            </Button>
          )
        }
      />

      <Card className="mb-4">
        <CardContent className="pt-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <Label htmlFor="f-q">Recherche</Label>
              <Input
                id="f-q"
                placeholder="Nom ou téléphone"
                defaultValue={filters.q ?? ''}
                onChange={(e) => updateFilters({ q: e.target.value || undefined, page: 1 })}
              />
            </div>
            <div>
              <Label htmlFor="f-sort">Tri</Label>
              <select
                id="f-sort"
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={filters.sort ?? 'nom:asc'}
                onChange={(e) => updateFilters({ sort: e.target.value, page: 1 })}
              >
                <option value="nom:asc">Nom (A→Z)</option>
                <option value="nom:desc">Nom (Z→A)</option>
                <option value="created_at:desc">Plus récentes</option>
                <option value="created_at:asc">Plus anciennes</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <DataTable<FamilleRead>
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
            icon={<Users2 className="h-5 w-5" />}
            title="Aucune famille"
            message="Ajoutez une famille pour rattacher des élèves."
          />
        }
        ariaLabel="Liste des familles"
      />
    </div>
  );
}