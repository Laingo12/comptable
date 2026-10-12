import {
  Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/EmptyState';
import { MoneyCell } from '@/components/MoneyCell';
import { formatAr } from '@/lib/format';
import type { ComparatifLigne } from '../api';

interface Props {
  data: ComparatifLigne[];
}

export function ComparatifCharges({ data }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Charges : réel vs prévisionnel</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <EmptyState compact title="Aucune charge cataloguée" />
        ) : (
          <>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 8, right: 12, left: 8, bottom: 0 }}>
                  <defs>
                    {/* Motif hachuré pour le prévisionnel (distinction hors couleur). */}
                    <pattern id="pat-prev" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
                      <rect width="8" height="8" fill="hsl(var(--chart-1))" opacity="0.15" />
                      <line x1="0" y1="0" x2="0" y2="8" stroke="hsl(var(--chart-1))" strokeWidth="2" />
                    </pattern>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="libelle"
                    tick={{ fontSize: 11 }}
                    interval={0}
                    angle={-15}
                    height={48}
                    textAnchor="end"
                  />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `${Math.round(v / 1000)}k`} />
                  <Tooltip formatter={(v: number) => formatAr(v)} />
                  <Legend />
                  <Bar dataKey="previsionnel" name="Prévisionnel" fill="url(#pat-prev)" stroke="hsl(var(--chart-1))" />
                  <Bar dataKey="reel" name="Réel" fill="hsl(var(--chart-2))" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th className="px-2 py-1 text-left">Libellé</th>
                    <th className="px-2 py-1 text-right">Prévisionnel</th>
                    <th className="px-2 py-1 text-right">Réel</th>
                    <th className="px-2 py-1 text-right">Écart</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((d) => (
                    <tr key={d.libelle} className="border-b">
                      <td className="px-2 py-1">{d.libelle}</td>
                      <td className="px-2 py-1 text-right"><MoneyCell value={d.previsionnel} /></td>
                      <td className="px-2 py-1 text-right"><MoneyCell value={d.reel} /></td>
                      <td className="px-2 py-1 text-right">
                        <span className={d.ecart > 0 ? 'text-danger-dark tabular' : 'text-success-dark tabular'}>
                          {d.ecart > 0 ? '+' : ''}{formatAr(d.ecart)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}