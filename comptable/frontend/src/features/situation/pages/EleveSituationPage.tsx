import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { FileText, Info, Receipt } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { MoneyCell } from '@/components/MoneyCell';
import { StatusBadge } from '@/components/StatusBadge';
import { formatAr, formatDate, formatPercent } from '@/lib/format';
import { elevesApi } from '@/features/eleves/api';
import { referentielsApi } from '@/features/referentiels/api';
import { situationApi, downloadReceipt, type MoisSituation } from '../api';
import { QualificatifBadge } from '../components/QualificatifBadge';

function statutToStatusKey(statut: string, enRetard: boolean): 'PAYE' | 'PARTIEL' | 'IMPAYE' | 'RETARD' {
  if (enRetard) return 'RETARD';
  if (statut === 'PAYE') return 'PAYE';
  if (statut === 'PARTIEL') return 'PARTIEL';
  return 'IMPAYE';
}

export function EleveSituationPage() {
  const { id } = useParams<{ id: string }>();
  const eleveId = Number(id);
  const navigate = useNavigate();
  const [busyReceipt, setBusyReceipt] = useState<number | null>(null);

  const eleveQuery = useQuery({
    queryKey: ['eleves', eleveId],
    queryFn: () => elevesApi.byId(eleveId),
    enabled: Number.isFinite(eleveId) && eleveId > 0,
  });

  const situationQuery = useQuery({
    queryKey: ['situation', eleveId],
    queryFn: () => situationApi.byEleve(eleveId),
    enabled: Number.isFinite(eleveId) && eleveId > 0,
  });

  const niveauxQuery = useQuery({
    queryKey: ['referentiels', 'niveaux'],
    queryFn: referentielsApi.niveaux,
    staleTime: 10 * 60_000,
  });

  const onReceipt = async (paiementId: number) => {
    setBusyReceipt(paiementId);
    try {
      await downloadReceipt(paiementId, 'pdf');
    } catch {
      toast.error('Impossible de télécharger le reçu.');
    } finally {
      setBusyReceipt(null);
    }
  };

  if (eleveQuery.isLoading || situationQuery.isLoading) {
    return <div className="text-sm text-muted-foreground">Chargement…</div>;
  }
  if (eleveQuery.isError || !eleveQuery.data) {
    return <ErrorState title="Élève introuvable" onRetry={() => navigate('/eleves')} />;
  }
  if (situationQuery.isError) {
    return (
      <ErrorState
        title="Situation indisponible"
        message="L'élève n'a peut-être aucune inscription pour cette année."
        onRetry={() => situationQuery.refetch()}
      />
    );
  }
  if (!situationQuery.data) return null;

  const e = eleveQuery.data;
  const s = situationQuery.data;
  const niveau = niveauxQuery.data?.find((n) => n.id === s.niveau_id);

  return (
    <div>
      <PageHeader
        title={`Situation écolage — ${e.nom} ${e.prenoms}`}
        subtitle={`${e.matricule} — ${niveau?.libelle ?? `niveau #${s.niveau_id}`}`}
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Élèves', to: '/eleves' },
          { label: `${e.nom} ${e.prenoms}`, to: `/eleves/${e.id}` },
          { label: 'Situation' },
        ]}
        actions={
          <Button asChild variant="outline">
            <Link to={`/eleves/${e.id}`}>
              <FileText className="h-4 w-4" /> Fiche élève
            </Link>
          </Button>
        }
      />

      {/* KPI écolage */}
      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Écolage attendu</p>
            <p className="mt-1 text-xl font-semibold"><MoneyCell value={s.totaux.du} align={false} /></p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Écolage payé</p>
            <p className="mt-1 text-xl font-semibold text-success">
              <MoneyCell value={s.totaux.paye} align={false} />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Reste dû</p>
            <p className={`mt-1 text-xl font-semibold ${s.totaux.reste_du > 0 ? 'text-danger' : ''}`}>
              <MoneyCell value={s.totaux.reste_du} align={false} />
            </p>
          </CardContent>
        </Card>
                <Card>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Taux recouvrement</p>
            <p className="mt-1 text-xl font-semibold">
              {formatPercent(s.totaux.taux_recouvrement)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Droits & FG */}
      <div className="mb-4 grid gap-3 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Droit d'inscription</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-muted-foreground">Dû</dt>
              <dd><MoneyCell value={s.droits_inscription.du} align={false} /></dd>
              <dt className="text-muted-foreground">Payé</dt>
              <dd><MoneyCell value={s.droits_inscription.paye} align={false} /></dd>
              <dt className="text-muted-foreground">Reste</dt>
              <dd><MoneyCell value={s.droits_inscription.reste_du} align={false} /></dd>
              <dt className="text-muted-foreground">Statut</dt>
              <dd>
                <StatusBadge
                  status={
                    s.droits_inscription.statut === 'PAYE' ? 'PAYE'
                      : s.droits_inscription.statut === 'PARTIEL' ? 'PARTIEL'
                      : 'IMPAYE'
                  }
                />
              </dd>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Frais généraux</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-muted-foreground">Dû</dt>
              <dd><MoneyCell value={s.frais_generaux.du} align={false} /></dd>
              <dt className="text-muted-foreground">Payé</dt>
              <dd><MoneyCell value={s.frais_generaux.paye} align={false} /></dd>
              <dt className="text-muted-foreground">Reste</dt>
              <dd><MoneyCell value={s.frais_generaux.reste_du} align={false} /></dd>
              <dt className="text-muted-foreground">Statut</dt>
              <dd>
                <StatusBadge
                  status={
                    s.frais_generaux.statut === 'PAYE' ? 'PAYE'
                      : s.frais_generaux.statut === 'PARTIEL' ? 'PARTIEL'
                      : 'IMPAYE'
                  }
                />
              </dd>
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Détail par mois */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Info className="h-4 w-4" /> Détail mois par mois
            <span className="text-xs font-normal text-muted-foreground">
              (à partir du mois d'entrée)
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th className="px-2 py-2 text-left">Mois</th>
                  <th className="px-2 py-2 text-right">Dû</th>
                  <th className="px-2 py-2 text-right">Payé</th>
                  <th className="px-2 py-2 text-right">Reste</th>
                  <th className="px-2 py-2 text-left">Statut</th>
                  <th className="px-2 py-2 text-left">Limite</th>
                  <th className="px-2 py-2 text-left">Paiements</th>
                </tr>
              </thead>
              <tbody>
                {s.mois.map((m) => (
                  <MoisRow
                    key={m.mois_id}
                    m={m}
                    busyReceipt={busyReceipt}
                    onReceipt={onReceipt}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface MoisRowProps {
  m: MoisSituation;
  busyReceipt: number | null;
  onReceipt: (paiementId: number) => void;
}

function MoisRow({ m, busyReceipt, onReceipt }: MoisRowProps) {
  const statusKey = statutToStatusKey(m.statut, m.en_retard);
  return (
    <tr className="border-b align-top hover:bg-muted/40">
      <td className="px-2 py-2 font-medium">{m.libelle}</td>
      <td className="px-2 py-2 text-right"><MoneyCell value={m.du} /></td>
      <td className="px-2 py-2 text-right"><MoneyCell value={m.paye} /></td>
      <td className="px-2 py-2 text-right"><MoneyCell value={m.reste_du} /></td>
      <td className="px-2 py-2">
        <StatusBadge status={statusKey} />
        {m.echu && !m.en_retard && (
          <Badge variant="secondary" className="ml-1 text-[10px]">échu</Badge>
        )}
      </td>
      <td className="px-2 py-2 text-xs text-muted-foreground">
        {formatDate(m.date_limite_paiement)}
      </td>
      <td className="px-2 py-2">
        {m.paiements.length === 0 ? (
          <span className="text-xs text-muted-foreground">—</span>
        ) : (
          <ul className="space-y-1">
            {m.paiements.map((p) => (
              <li key={p.id} className="flex items-center gap-2 text-xs">
                <span className="tabular text-muted-foreground">
                  {formatDate(p.date_paiement)}
                </span>
                <span className="tabular font-medium">{formatAr(p.montant)}</span>
                <QualificatifBadge value={p.qualificatif} />
                {p.reference && <span className="text-muted-foreground">#{p.reference}</span>}
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 px-2"
                  disabled={busyReceipt === p.id}
                  onClick={() => onReceipt(p.id)}
                  aria-label={`Télécharger le reçu du paiement ${p.id}`}
                >
                  <Receipt className="h-3 w-3" />
                  {busyReceipt === p.id ? '…' : 'Reçu'}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </td>
    </tr>
  );
}