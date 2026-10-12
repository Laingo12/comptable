import { useEffect, useState } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import type { EleveListFilters } from '../schemas';

interface Props {
  filters: EleveListFilters;
  onChange: (next: Partial<EleveListFilters>) => void;
}

export function ElevesFilters({ filters, onChange }: Props) {
  const [search, setSearch] = useState(filters.q ?? '');

  // Debounce 300 ms — pas de requête à chaque frappe.
  useEffect(() => {
    const t = window.setTimeout(() => {
      const current = filters.q ?? '';
      if (search !== current) onChange({ q: search || undefined, page: 1 });
    }, 300);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <Label htmlFor="f-q">Recherche</Label>
        <Input
          id="f-q"
          placeholder="Nom, prénoms ou matricule"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <div>
        <Label htmlFor="f-sort">Tri</Label>
        <Select
          id="f-sort"
          value={filters.sort ?? 'nom:asc'}
          onChange={(e) => onChange({ sort: e.target.value, page: 1 })}
        >
          <option value="nom:asc">Nom (A→Z)</option>
          <option value="nom:desc">Nom (Z→A)</option>
          <option value="matricule:asc">Matricule (A→Z)</option>
          <option value="created_at:desc">Plus récents</option>
          <option value="created_at:asc">Plus anciens</option>
        </Select>
      </div>
    </div>
  );
}