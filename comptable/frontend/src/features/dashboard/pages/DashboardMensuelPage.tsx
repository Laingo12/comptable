import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  AlertCircle, Banknote, Coins, HandCoins, TrendingUp, Wallet,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { MoneyCell } from '@/components/MoneyCell';
import { StatusBadge } from '@/components/StatusBadge';
import { formatPercent } from '@/lib/format';
import { referentielsApi } from '@/features/referentiels/api';
import { dashboardApi } from '../api';
import { KpiCard } from '../components/KpiCard';
import { MoisSelect } from '../components/MoisSelect';
import { ChartEncaissementsJour } from '../components/ChartEncaissementsJour';
import { ChartCaParMode } from '../components/ChartCaParMode';
import { ComparatifCharges } from '../components/ComparatifCharges';

export function DashboardMensuelPage() {
  const [sp, setSp] = useSearchParams();

  const moisQuery = useQuery({
    queryKey: ['referentiels', 'mois-scolaires'],
    queryFn: () => referentielsApi.moisScolaires(),
    staleTime: 10 * 60_000,
  });

  const moisScolaires = useMemo(
    () => (moisQuery.data ?? []).filter((m) => m.est_scolaire),
    [moisQuery.data],
  );

  const moisId = useMemo(() => {
    const fromUrl = sp.get('mois_id');
    if (fromUrl && /^\d+$/.test(fromUrl)) return Number(fromUrl);
    return moisScolaires[0]?.id ?? 0;
  }, [sp, moisScolaires]);

  const query = useQuery({
    queryKey: ['dashboard', 'mensuel', moisId],
    queryFn: () => dashboardApi.mensuel(moisId),
    enabled: moisId > 0,
  });

  const onMoisChange = (id: number) => {
    const next = new URLSearchParams(sp);
    next.set('mois_id', String(id));
    setSp(next, { replace: true });
  };

  return (
    <div>
      <PageHeader
        title="Tableau de bord mensuel"
        subtitle={query.data ? `${query.data.mois_libelle} — ${query.data.mois_code}` : undefined}
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Tableau de bord' }]}
        actions={<MoisSelect value={moisId} onChange={onMoisChange} />}
      />

      {query.isLoading && (
        <p className="text-sm text-muted-foreground">Chargement…</p>
      )}

      {query.isError && (
        <ErrorState
          title="Dashboard indisponible"
          message="Impossible de charger les données du mois sélectionné."
          onRetry={() => query.refetch()}
        />
      )}

      {query.data && (
        <div className="space-y-6">
          {/* --- CA --- */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="CA encaissé (brut)"
              value={<MoneyCell value={query.data.ca_total_brut} align={false} />}
              icon={<Coins className="h-4 w-4" />}
            />
            <KpiCard
              label="CA retenu (part Jessy)"
              value={<MoneyCell value={query.data.ca_retenu} align={false} />}
              tone="info"
              hint={
                <>
                  dont écolages <MoneyCell value={query.data.ca_ecolage} align={false} /> ·
                  droits <MoneyCell value={query.data.ca_inscription} align={false} /> ·
                  FG <MoneyCell value={query.data.ca_frais_generaux} align={false} />
                </>
              }
            />
            <KpiCard
              label="Charges du mois"
              value={<MoneyCell value={query.data.charges} align={false} />}
              tone="danger"
              icon={<Wallet className="h-4 w-4" />}
            />
            <KpiCard
              label="Salaires du mois"
              value={<MoneyCell value={query.data.salaires.brut_total} align={false} />}
              tone="danger"
              icon={<Banknote className="h-4 w-4" />}
            />
          </div>

          {/* --- Résultat + Trésorerie --- */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="Résultat avant prélèvements"
              value={<MoneyCell value={query.data.resultat_avant_prelevements} align={false} />}
              tone={query.data.resultat_avant_prelevements >= 0 ? 'success' : 'danger'}
            />
            <KpiCard
              label="Prélèvements du mois"
              value={<MoneyCell value={query.data.prelevements_mois} align={false} />}
              tone="info"
              icon={<HandCoins className="h-4 w-4" />}
            />
            <KpiCard
              label="Résultat après prélèvements"
              value={<MoneyCell value={query.data.resultat_apres_prelevements} align={false} />}
              tone={query.data.resultat_apres_prelevements >= 0 ? 'success' : 'danger'}
            />
            <KpiCard
              label="Trésorerie fin de mois"
              value={<MoneyCell value={query.data.tresorerie_fin} align={false} />}
              hint={
                <>
                  début : <MoneyCell value={query.data.tresorerie_debut} align={false} />
                </>
              }
              icon={<TrendingUp className="h-4 w-4" />}
            />
          </div>

          {/* --- Recouvrement --- */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="Écolage attendu"
              value={<MoneyCell value={query.data.ecolage_attendu} align={false} />}
            />
            <KpiCard
              label="Écolage reçu"
              value={<MoneyCell value={query.data.ecolage_recu} align={false} />}
              tone="success"
            />
            <KpiCard
              label="Reste dû"
              value={<MoneyCell value={query.data.ecolage_reste_du} align={false} />}
              tone={query.data.ecolage_reste_du > 0 ? 'danger' : 'success'}
            />
            <KpiCard
              label="Taux de recouvrement"
              value={formatPercent(query.data.taux_recouvrement)}
              tone={query.data.taux_recouvrement >= 80 ? 'success' : 'warning'}
            />
          </div>

          {/* --- Compteurs --- */}
          <Card>
            <CardHeader>
              <CardTitle>Situation par statut (mois concerné)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <div className="flex items-center gap-2">
                  <StatusBadge status="PAYE" />
                  <span className="tabular font-medium">{query.data.compteurs.payes}</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status="PARTIEL" />
                  <span className="tabular font-medium">{query.data.compteurs.partiels}</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status="IMPAYE" />
                  <span className="tabular font-medium">{query.data.compteurs.impayes}</span>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status="RETARD" />
                  <span className="tabular font-medium">{query.data.compteurs.en_retard}</span>
                </div>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                Avances reçues ce mois : <MoneyCell value={query.data.avances} align={false} /> ·
                Retards régularisés : <MoneyCell value={query.data.retards_regularises} align={false} />
              </p>
            </CardContent>
          </Card>

          {/* --- Priorités Jessy / salaires --- */}
          <Card>
            <CardHeader>
              <CardTitle>Priorité des sorties (Jessy puis salaires)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <KpiCard
                  label="Jessy (le 10)"
                  value={<MoneyCell value={query.data.jessy_prioritaire_10} align={false} />}
                  hint="Montant prélevé au titre du mois"
                />
                <KpiCard
                  label="70 % des salaires (le 25)"
                  value={<MoneyCell value={query.data.salaires.du_70} align={false} />}
                  hint={
                    <>
                      disponible : <MoneyCell value={query.data.salaires.disponible_pour_70} align={false} />
                    </>
                  }
                />
                <KpiCard
                  label="% payable le 25"
                  value={formatPercent(query.data.salaires.pct_payable_25)}
                  tone={query.data.salaires.pct_payable_25 >= 100 ? 'success' : 'warning'}
                />
                <KpiCard
                  label="Somme manquante"
                  value={<MoneyCell value={query.data.salaires.somme_manquante_25} align={false} />}
                  tone={query.data.salaires.somme_manquante_25 > 0 ? 'danger' : 'success'}
                  icon={<AlertCircle className="h-4 w-4" />}
                />
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <KpiCard
                  label="30 % des salaires (le 10 suivant)"
                  value={<MoneyCell value={query.data.salaires.du_30} align={false} />}
                />
                <KpiCard
                  label="Payé 70 %"
                  value={<MoneyCell value={query.data.salaires.paye_70} align={false} />}
                />
                <KpiCard
                  label="Payé 30 %"
                  value={<MoneyCell value={query.data.salaires.paye_30} align={false} />}
                />
              </div>
            </CardContent>
          </Card>

          {/* --- Graphiques --- */}
          <ChartEncaissementsJour data={query.data.par_jour} />

          <div className="grid gap-3 lg:grid-cols-2">
            <ChartCaParMode data={query.data.par_mode} />
            <ComparatifCharges data={query.data.comparatif} />
          </div>
        </div>
      )}
    </div>
  );
}