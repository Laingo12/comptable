import {
  flexRender, getCoreRowModel, useReactTable,
  type ColumnDef,
} from '@tanstack/react-table';
import { useMemo, type ReactNode } from 'react';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { LoadingRows } from '@/components/LoadingRows';


export interface DataTableProps<T> {
  data: T[];
  columns: ColumnDef<T, unknown>[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;

  sort?: string;
  onSortChange?: (sort: string) => void;

  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;

  empty?: ReactNode;
  stickyHeader?: boolean;
  ariaLabel?: string;
}

function toggleSort(current: string | undefined, field: string): string {
  const [f, dir] = (current ?? '').split(':');
  if (f !== field) return `${field}:asc`;
  return `${field}:${dir === 'asc' ? 'desc' : 'asc'}`;
}

export function DataTable<T>({
  data, columns,
  total, page, pageSize, onPageChange,
  sort, onSortChange,
  loading, error, onRetry,
  empty, stickyHeader = true, ariaLabel = 'Tableau',
}: DataTableProps<T>) {
  const [currentField, currentDir] = (sort ?? '').split(':');

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
  });

  const colCount = columns.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const first = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const last = Math.min(page * pageSize, total);

  const headerGroups = useMemo(() => table.getHeaderGroups(), [table]);

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-md border bg-card">
        <Table aria-label={ariaLabel}>
          <TableHeader className={stickyHeader ? 'sticky top-0 z-10 bg-muted/80 backdrop-blur' : undefined}>
            {headerGroups.map((hg) => (
              <TableRow key={hg.id}>
                {hg.headers.map((h) => {
                  const meta = h.column.columnDef.meta as
                    | { sortable?: boolean; sortField?: string; align?: 'left' | 'right' }
                    | undefined;
                  const sortable = !!meta?.sortable && !!onSortChange;
                  const field = meta?.sortField ?? h.column.id;
                  const active = currentField === field;
                  const align = meta?.align === 'right' ? 'text-right' : 'text-left';
                  return (
                    <TableHead key={h.id} className={align}>
                      {sortable ? (
                        <button
                          type="button"
                          onClick={() => onSortChange?.(toggleSort(sort, field))}
                          className="inline-flex items-center gap-1 uppercase tracking-wide hover:text-foreground"
                          aria-sort={active ? (currentDir === 'desc' ? 'descending' : 'ascending') : 'none'}
                        >
                          {flexRender(h.column.columnDef.header, h.getContext())}
                          <span aria-hidden="true" className="text-muted-foreground/60">
                            {active ? (currentDir === 'desc' ? '↓' : '↑') : '↕'}
                          </span>
                        </button>
                      ) : (
                        flexRender(h.column.columnDef.header, h.getContext())
                      )}
                    </TableHead>
                  );
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {error ? (
              <TableRow>
                <TableCell colSpan={colCount}>
                  <ErrorState
                    title="Impossible de charger les données"
                    message={error.message}
                    onRetry={onRetry}
                    compact
                  />
                </TableCell>
              </TableRow>
            ) : loading ? (
              <LoadingRows rows={6} cols={colCount} />
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell colSpan={colCount}>
                  {empty ?? <EmptyState compact />}
                </TableCell>
              </TableRow>
            ) : (
              table.getRowModel().rows.map((r) => (
                <TableRow key={r.id}>
                  {r.getVisibleCells().map((c) => (
                    <TableCell key={c.id}>
                      {flexRender(c.column.columnDef.cell, c.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="tabular text-xs text-muted-foreground">
          {total === 0 ? 'Aucun résultat' : `${first}–${last} sur ${total}`}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline" size="sm"
            disabled={page <= 1 || loading}
            onClick={() => onPageChange(page - 1)}
          >
            Précédent
          </Button>
          <span className="tabular flex items-center px-2 text-xs text-muted-foreground">
            Page {page} / {totalPages}
          </span>
          <Button
            variant="outline" size="sm"
            disabled={page >= totalPages || loading}
            onClick={() => onPageChange(page + 1)}
          >
            Suivant
          </Button>
        </div>
      </div>
    </div>
  );
}