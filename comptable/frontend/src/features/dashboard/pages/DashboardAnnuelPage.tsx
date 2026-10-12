import { useQuery } from '@tanstack/react-query';
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts';
import { Users, Wallet } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { MoneyCell } from '@/components/MoneyCell';
import { formatAr } from '@/lib/format';
import { dashboardApi } from '../api';
import { KpiCard } from '../components/KpiCard';

export function DashboardAnnuelPage() {
  const query = useQuery({
    queryKey: ['dashboard', 'annuel'],
    queryFn: () => dashboardApi.annuel(),
  });

  return (
    <div>
      <PageHeader
        title="Tableau de bord annuel"
        subtitle={query.data ? `Année scolaire ${query.data.libelle}` : undefined}
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Tableau de bord annuel' }]}
      />

      {query.isLoading && (
        <p className="text-sm text-muted-foreground">Chargement…</p>
      )}

      {query.isError && (
        <ErrorState
          title="Dashboard indisponible"
          onRetry={() => query.refetch()}
        />
      )}

      {query.data && (
        <div className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="Effectif actif"
              value={query.data.effectif}
              icon={<Users className="h-4 w-4" />}
            />
            <KpiCard
              label="CA encaissé (brut)"
              value={<MoneyCell value={query.data.ca_total_brut} align={false} />}
            />
            <KpiCard
              label="CA retenu (part Jessy)"
              value={<MoneyCell value={query.data.ca_retenu} align={false} />}
              tone="info"
            />
            <KpiCard
              label="Versé aux associés"
              value={<MoneyCell value={query.data.verse_associes} align={false} />}
              icon={<Wallet className="h-4 w-4" />}
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="Retards à recouvrer"
              value={<MoneyCell value={query.data.retards_a_recouvrer} align={false} />}
              tone={query.data.retards_a_recouvrer > 0 ? 'danger' : 'success'}
            />
            <KpiCard
              label="Avances perçues"
              value={<MoneyCell value={query.data.avances_percues} align={false} />}
              tone="info"
            />
            <KpiCard
              label="FG restants dus"
              value={<MoneyCell value={query.data.fg_restants_dus} align={false} />}
              tone={query.data.fg_restants_dus > 0 ? 'warning' : 'success'}
            />
            <KpiCard
              label="Droits d'inscription restants dus"
              value={<MoneyCell value={query.data.droits_inscription_restants_dus} align={false} />}
              tone={query.data.droits_inscription_restants_dus > 0 ? 'warning' : 'success'}
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <KpiCard
              label="Trésorerie actuelle"
              value={<MoneyCell value={query.data.tresorerie_actuelle} align={false} />}
              tone={query.data.tresorerie_actuelle >= 0 ? 'success' : 'danger'}
            />
            <KpiCard
              label="Somme manquante cumulée"
              value={<MoneyCell value={query.data.somme_manquante_cumulee} align={false} />}
              tone={query.data.somme_manquante_cumulee > 0 ? 'danger' : 'success'}
            />
          </div>

          {/* Graphique en barres : CA retenu vs charges vs salaires vs prélèvements */}
          <Card>
            <CardHeader>
              <CardTitle>Vue comparative par mois</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={query.data.mois} margin={{ top: 8, right: 12, left: 8, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="mois_libelle" tick={{ fontSize: 11 }} interval={0} angle={-15} height={48} textAnchor="end" />
                    <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `${Math.round(v / 1000)}k`} />
                    <Tooltip formatter={(v: number) => formatAr(v)} />
                    <Legend />
                    <Bar dataKey="ca_retenu" fill="hsl(var(--primary))" name="CA retenu" />
                    <Bar dataKey="charges" fill="hsl(var(--destructive))" name="Charges" />
                    <Bar dataKey="salaires" fill="hsl(var(--warning))" name="Salaires" />
                    <Bar dataKey="prelevements" fill="hsl(var(--info))" name="Prélèvements" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Graphique en ligne : trésorerie fin de mois */}
          <Card>
            <CardHeader>
              <CardTitle>Trésorerie en fin de mois</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={query.data.mois} margin={{ top: 8, right: 12, left: 8, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="mois_libelle" tick={{ fontSize: 11 }} interval={0} angle={-15} height={48} textAnchor="end" />
                    <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `${Math.round(v / 1000)}k`} />
                    <Tooltip formatter={(v: number) => formatAr(v)} />
                    <Line
                      type="monotone"
                      dataKey="tresorerie_fin"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Tableau détaillé */}
          <Card>
            <CardHeader>
              <CardTitle>Détail mensuel</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b text-xs uppercase tracking-wide text-muted-foreground">
                    <tr>
                      <th className="px-2 py-2 text-left">Mois</th>
                      <th className="px-2 py-2 text-right">CA retenu</th>
                      <th className="px-2 py-2 text-right">Charges</th>
                      <th className="px-2 py-2 text-right">Salaires</th>
                      <th className="px-2 py-2 text-right">Prélèvements</th>
                      <th className="px-2 py-2 text-right">Résultat</th>
                      <th className="px-2 py-2 text-right">Trésorerie fin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {query.data.mois.map((m) => (
                      <tr key={m.mois_code} className="border-b hover:bg-muted/40">
                        <td className="px-2 py-2 font-medium">{m.mois_libelle}</td>
                        <td className="px-2 py-2 text-right"><MoneyCell value={m.ca_retenu} /></td>
                        <td className="px-2 py-2 text-right"><MoneyCell value={m.charges} /></td>
                        <td className="px-2 py-2 text-right"><MoneyCell value={m.salaires} /></td>
                        <td className="px-2 py-2 text-right"><MoneyCell value={m.prelevements} /></td>
                        <td className="px-2 py-2 text-right"><MoneyCell value={m.resultat_apres_prelevements} /></td>
                        <td className="px-2 py-2 text-right"><MoneyCell value={m.tresorerie_fin} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}