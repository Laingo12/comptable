import {
  Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/EmptyState';
import { formatAr } from '@/lib/format';
import type { EncaissementParMode } from '../api';

interface Props {
  data: EncaissementParMode[];
}

// Palette extraite du logo (via tokens CSS --chart-N).
const COLORS = [
  'hsl(var(--chart-1))',   // violet
  'hsl(var(--chart-2))',   // cyan
  'hsl(var(--chart-3))',   // vert
  'hsl(var(--chart-4))',   // gris moyen
  'hsl(var(--chart-5))',   // gris clair
];

export function ChartCaParMode({ data }: Props) {
  const rows = data
    .filter((d) => d.total > 0)
    .map((d) => ({ mode: d.mode_code ?? 'Non précisé', total: d.total }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Répartition par mode de paiement</CardTitle>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <EmptyState compact title="Aucun encaissement" />
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows} margin={{ top: 8, right: 12, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="mode" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `${Math.round(v / 1000)}k`} />
                <Tooltip formatter={(v: number) => formatAr(v)} />
                <Legend />
                <Bar dataKey="total" name="Montant encaissé" radius={[4, 4, 0, 0]}>
                  {rows.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}