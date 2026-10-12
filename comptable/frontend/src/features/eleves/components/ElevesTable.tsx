import {
  flexRender, getCoreRowModel, useReactTable, type ColumnDef,
} from '@tanstack/react-table';
import { useMemo } from 'react';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDate } from '@/lib/format';
import type { EleveRead } from '../api';

interface Props {
  data: EleveRead[];
  loading?: boolean;
  sort?: string;
  onSortChange?: (sort: string) => void;
}

function toggleSort(current: string | undefined, field: string): string {
  const [f, dir] = (current ?? '').split(':');
  if (f !== field) return `${field}:asc`;
  return `${field}:${dir === 'asc' ? 'desc' : 'asc'}`;
}

function SortIndicator({ active, dir }: { active: boolean; dir?: string }) {
  if (!active) return <span className="ml-1 text-muted-foreground/50">↕</span>;
  return <span className="ml-1">{dir === 'desc' ? '↓' : '↑'}</span>;
}

export function ElevesTable({ data, loading, sort, onSortChange }: Props) {
  const [currentField, currentDir] = (sort ?? '').split(':');

  const headerFor = (field: string, label: string) => () => (
    <button
      type="button"
      className="uppercase tracking-wide hover:text-foreground"
      onClick={() => onSortChange?.(toggleSort(sort, field))}
    >
      {label}
      <SortIndicator active={currentField === field} dir={currentDir} />
    </button>
  );

  const columns = useMemo<ColumnDef<EleveRead>[]>(() => [
    {
      accessorKey: 'matricule',
      header: headerFor('matricule', 'Matricule'),
      cell: ({ row }) => <span className="font-mono text-xs">{row.original.matricule}</span>,
    },
    {
      accessorKey: 'nom',
      header: headerFor('nom', 'Nom'),
      cell: ({ row }) => (
        <div className="font-medium">
          {row.original.nom} <span className="font-normal">{row.original.prenoms}</span>
        </div>
      ),
    },
    { accessorKey: 'sexe', header: 'Sexe', cell: ({ row }) => row.original.sexe ?? '—' },
    {
      accessorKey: 'date_naissance',
      header: 'Naissance',
      cell: ({ row }) => formatDate(row.original.date_naissance),
    },
    {
      accessorKey: 'famille_id',
      header: 'Famille',
      cell: ({ row }) =>
        row.original.famille_id ? <Badge variant="secondary">#{row.original.famille_id}</Badge> : '—',
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
  ], [sort, onSortChange]);

  const table = useReactTable({
    data, columns, getCoreRowModel: getCoreRowModel(), manualPagination: true,
  });

  if (loading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
      </div>
    );
  }

  const columnCount = columns.length;
  const rows = table.getRowModel().rows;

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map((hg) => (
          <TableRow key={hg.id}>
            {hg.headers.map((h) => (
              <TableHead key={h.id}>{flexRender(h.column.columnDef.header, h.getContext())}</TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {rows.length === 0 ? (
          <TableRow>
            <TableCell colSpan={columnCount} className="py-8 text-center text-muted-foreground">
              Aucun élève
            </TableCell>
          </TableRow>
        ) : (
          rows.map((r) => (
            <TableRow key={r.id}>
              {r.getVisibleCells().map((c) => (
                <TableCell key={c.id}>{flexRender(c.column.columnDef.cell, c.getContext())}</TableCell>
              ))}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );
}