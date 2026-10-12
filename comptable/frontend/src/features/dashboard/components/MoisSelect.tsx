import { useQuery } from '@tanstack/react-query';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { referentielsApi } from '@/features/referentiels/api';

interface Props {
  value: number;
  onChange: (id: number) => void;
}

export function MoisSelect({ value, onChange }: Props) {
  const query = useQuery({
    queryKey: ['referentiels', 'mois-scolaires'],
    queryFn: () => referentielsApi.moisScolaires(),
    staleTime: 10 * 60_000,
  });

  const mois = (query.data ?? []).filter((m) => m.est_scolaire);

  return (
    <div className="min-w-[220px]">
      <Label htmlFor="dash-mois">Mois</Label>
      <Select
        id="dash-mois"
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        disabled={mois.length === 0}
      >
        {mois.map((m) => (
          <option key={m.id} value={m.id}>{m.libelle}</option>
        ))}
      </Select>
    </div>
  );
}