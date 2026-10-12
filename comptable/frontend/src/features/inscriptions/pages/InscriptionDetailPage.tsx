import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { BookOpen, Pencil } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { MoneyCell } from '@/components/MoneyCell';
import { StatusBadge } from '@/components/StatusBadge';
import { useAuth } from '@/features/auth/useAuth';
import { elevesApi } from '@/features/eleves/api';
import { referentielsApi } from '@/features/referentiels/api';
import { inscriptionsApi } from '../api';

export function InscriptionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const inscriptionId = Number(id);
  const navigate = useNavigate();
  const { can } = useAuth();

  const query = useQuery({
    queryKey: ['inscriptions', inscriptionId],
    queryFn: () => inscriptionsApi.byId(inscriptionId),
    enabled: Number.isFinite(inscriptionId) && inscriptionId > 0,
  });

  const eleveQuery = useQuery({
    queryKey: ['eleves', query.data?.eleve_id ?? 0],
    queryFn: () => elevesApi.byId(query.data!.eleve_id),
    enabled: !!query.data?.eleve_id,
  });

  const niveauxQuery = useQuery({
    queryKey: ['referentiels', 'niveaux'],
    queryFn: referentielsApi.niveaux,
    staleTime: 10 * 60_000,
  });

  if (query.isLoading) {
    return <div className="text-sm text-muted-foreground">Chargement…</div>;
  }
  if (query.isError || !query.data) {
    return <ErrorState title="Inscription introuvable" onRetry={() => navigate('/eleves')} />;
  }

  const ins = query.data;
  const niveau = niveauxQuery.data?.find((n) => n.id === ins.niveau_id);

  return (
    <div>
      <PageHeader
        title={`Inscription — ${eleveQuery.data ? `${eleveQuery.data.nom} ${eleveQuery.data.prenoms}` : `élève #${ins.eleve_id}`}`}
        subtitle={`Année #${ins.annee_scolaire_id} — ${niveau?.libelle ?? `niveau #${ins.niveau_id}`}`}
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Élèves', to: '/eleves' },
          { label: eleveQuery.data ? `${eleveQuery.data.nom} ${eleveQuery.data.prenoms}` : `#${ins.eleve_id}`, to: `/eleves/${ins.eleve_id}` },
          { label: 'Inscription' },
        ]}
        actions={
          can('inscriptions', 'update') && (
            <Button asChild variant="outline">
              <Link to={`/inscriptions/${ins.id}/modifier`}>
                <Pencil className="h-4 w-4" /> Modifier
              </Link>
            </Button>
          )
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" /> Détails
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-muted-foreground">Statut</dt>
              <dd>
                <StatusBadge status={ins.statut === 'ACTIF' ? 'PAYE' : 'ANNULE'} />
                {/* Pour l'instant on mappe ACTIF/SORTI sur un badge simple */}
              </dd>

              <dt className="text-muted-foreground">Niveau</dt>
              <dd>{niveau?.libelle ?? `#${ins.niveau_id}`}</dd>

              <dt className="text-muted-foreground">Écolage mensuel</dt>
              <dd><MoneyCell value={ins.ecolage_mensuel} align={false} /></dd>

              <dt className="text-muted-foreground">Remise fratrie</dt>
              <dd>{ins.remise_pct} %</dd>

              <dt className="text-muted-foreground">Droit d'inscription dû</dt>
              <dd><MoneyCell value={ins.droit_inscription_du} align={false} /></dd>

              <dt className="text-muted-foreground">Frais généraux dus</dt>
              <dd><MoneyCell value={ins.frais_generaux_du} align={false} /></dd>

              {ins.date_sortie && (
                <>
                  <dt className="text-muted-foreground">Date de sortie</dt>
                  <dd>{ins.date_sortie}</dd>
                </>
              )}
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Situation écolage</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              La fiche situation (mois, paiements, reçus) sera livrée à l'étape 2.1.d.
            </p>
            <div className="mt-3">
              <Badge variant="outline">À venir</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}