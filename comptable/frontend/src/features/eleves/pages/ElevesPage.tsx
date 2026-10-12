import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { Users, Plus } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';
import { useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/PageHeader';
import { DataTable } from '@/components/DataTable';
import { EmptyState } from '@/components/EmptyState';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/format';
import { useAuth } from '@/features/auth/useAuth';
import { elevesApi, type EleveRead } from '../api';
import { ElevesFilters } from '../components/ElevesFilters';
import { eleveListFiltersSchema, type EleveListFilters } from '../schemas';

function readFilters(sp: URLSearchParams): EleveListFilters {
  const parsed = eleveListFiltersSchema.safeParse({
    q: sp.get('q') ?? undefined,
    famille_id: sp.get('famille_id') ?? undefined,
    sort: sp.get('sort') ?? undefined,
    page: sp.get('page') ?? 1,
    page_size: sp.get('page_size') ?? 20,
  });
  return parsed.success ? parsed.data : { page: 1, page_size: 20 };
}

export function ElevesPage() {
  const [sp, setSp] = useSearchParams();
  const filters = readFilters(sp);
  const { can } = useAuth();

  const query = useQuery({
    queryKey: ['eleves', filters],
    queryFn: () => elevesApi.list(filters),
    placeholderData: keepPreviousData,
  });

  const updateFilters = (patch: Partial<EleveListFilters>) => {
    const next = new URLSearchParams(sp);
    for (const [k, v] of Object.entries(patch)) {
      if (v === undefined || v === null || v === '') next.delete(k);
      else next.set(k, String(v));
    }
    setSp(next, { replace: true });
  };

  const columns = useMemo<ColumnDef<EleveRead, unknown>[]>(() => [
    {
      accessorKey: 'matricule',
      header: 'Matricule',
      meta: { sortable: true, sortField: 'matricule' },
      cell: ({ row }) => (
        <span className="tabular font-mono text-xs">{row.original.matricule}</span>
      ),
    },
    {
      accessorKey: 'nom',
      header: 'Nom',
      meta: { sortable: true, sortField: 'nom' },
      cell: ({ row }) => (
        <Link
          to={`/eleves/${row.original.id}`}
          className="font-medium hover:text-primary hover:underline"
        >
          {row.original.nom} <span className="font-normal">{row.original.prenoms}</span>
        </Link>
      ),
    },
    {
      accessorKey: 'sexe',
      header: 'Sexe',
      cell: ({ row }) => row.original.sexe ?? '—',
    },
    {
      accessorKey: 'date_naissance',
      header: 'Naissance',
      cell: ({ row }) => formatDate(row.original.date_naissance),
    },
    {
      accessorKey: 'famille_id',
      header: 'Famille',
      cell: ({ row }) =>
        row.original.famille_id
          ? <Badge variant="secondary" className="tabular">#{row.original.famille_id}</Badge>
          : '—',
    },
  ], []);

  return (
    <div>
      <PageHeader
        title="Élèves"
        subtitle={
          query.data
            ? `${query.data.total} élève${query.data.total > 1 ? 's' : ''}`
            : undefined
        }
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Élèves' }]}
        actions={
          can('eleves', 'create') && (
            <Button asChild>
              <Link to="/eleves/nouveau">
                <Plus className="h-4 w-4" /> Nouvel élève
              </Link>
            </Button>
          )
        }
      />

      <Card className="mb-4">
        <CardContent className="pt-6">
          <ElevesFilters filters={filters} onChange={updateFilters} />
        </CardContent>
      </Card>

      <DataTable<EleveRead>
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
            icon={<Users className="h-5 w-5" />}
            title="Aucun élève"
            message="Aucun élève ne correspond à ces filtres."
          />
        }
        ariaLabel="Liste des élèves"
      />
    </div>
  );
}