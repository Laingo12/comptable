import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/EmptyState';
import { formatAr } from '@/lib/format';
import type { EncaissementJour } from '../api';

interface Props {
  data: EncaissementJour[];
}

export function ChartEncaissementsJour({ data }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Encaissements par jour du mois (cumul)</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <EmptyState compact title="Aucun encaissement sur ce mois" message="Le cumul apparaîtra dès le premier paiement." />
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 8, right: 12, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="jour" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `${Math.round(v / 1000)}k`} />
                <Tooltip formatter={(v: number) => formatAr(v)} labelFormatter={(l) => `Jour ${l}`} />
                <Line
                  type="monotone"
                  dataKey="cumul"
                  name="Cumul encaissé"
                  stroke="hsl(var(--chart-1))"
                  strokeWidth={2}
                  strokeDasharray="0"
                  dot={{ r: 2, fill: 'hsl(var(--chart-1))' }}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}