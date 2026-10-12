import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { BookOpen, FileBarChart, Pencil, Plus, UserCircle2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { MoneyCell } from '@/components/MoneyCell';
import { formatDate } from '@/lib/format';
import { useAuth } from '@/features/auth/useAuth';
import { inscriptionsApi } from '@/features/inscriptions/api';
import { referentielsApi } from '@/features/referentiels/api';
import { elevesApi } from '../api';

export function EleveDetailPage() {
  const { id } = useParams<{ id: string }>();
  const eleveId = Number(id);
  const navigate = useNavigate();
  const { can } = useAuth();

  const query = useQuery({
    queryKey: ['eleves', eleveId],
    queryFn: () => elevesApi.byId(eleveId),
    enabled: Number.isFinite(eleveId) && eleveId > 0,
  });

  const inscriptionsQuery = useQuery({
    queryKey: ['inscriptions', 'par-eleve', eleveId],
    queryFn: () => inscriptionsApi.list({ eleve_id: eleveId, page: 1, page_size: 1 }),
    enabled: Number.isFinite(eleveId) && eleveId > 0,
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
    return (
      <ErrorState
        title="Élève introuvable"
        message="Cet élève n'existe pas ou a été supprimé."
        onRetry={() => navigate('/eleves')}
      />
    );
  }

  const e = query.data;
  const inscription = inscriptionsQuery.data?.items[0] ?? null;
  const niveau = inscription
    ? niveauxQuery.data?.find((n) => n.id === inscription.niveau_id)
    : null;

  return (
    <div>
      <PageHeader
        title={`${e.nom} ${e.prenoms}`}
        subtitle={`Matricule ${e.matricule}`}
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Élèves', to: '/eleves' },
          { label: `${e.nom} ${e.prenoms}` },
        ]}
        actions={
          <div className="flex flex-wrap gap-2">
            {inscription !== null && can('paiements', 'create') && (
              <Button asChild>
                <Link to={`/paiements/nouveau?inscription_id=${inscription.id}`}>
                  <Plus className="h-4 w-4" /> Nouveau paiement
                </Link>
              </Button>
            )}
            {inscription !== null && (
              <Button asChild variant="outline">
                <Link to={`/eleves/${e.id}/situation`}>
                  <FileBarChart className="h-4 w-4" /> Situation écolage
                </Link>
              </Button>
            )}
            {inscription === null && can('inscriptions', 'create') && (
              <Button asChild>
                <Link to={`/eleves/${e.id}/inscrire`}>Inscrire</Link>
              </Button>
            )}
            {can('eleves', 'update') && (
              <Button asChild variant="outline">
                <Link to={`/eleves/${e.id}/modifier`}>
                  <Pencil className="h-4 w-4" /> Modifier
                </Link>
              </Button>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserCircle2 className="h-4 w-4" /> Informations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-muted-foreground">Matricule</dt>
              <dd className="tabular font-mono text-xs">{e.matricule}</dd>

              <dt className="text-muted-foreground">Nom complet</dt>
              <dd>{e.nom} {e.prenoms}</dd>

              <dt className="text-muted-foreground">Sexe</dt>
              <dd>{e.sexe === 'M' ? 'Masculin' : e.sexe === 'F' ? 'Féminin' : '—'}</dd>

              <dt className="text-muted-foreground">Date de naissance</dt>
              <dd>{formatDate(e.date_naissance)}</dd>

              <dt className="text-muted-foreground">Famille</dt>
              <dd>
                {e.famille_id
                  ? <Link to={`/familles/${e.famille_id}`} className="hover:text-primary hover:underline">
                      <Badge variant="secondary" className="tabular">#{e.famille_id}</Badge>
                    </Link>
                  : '—'}
              </dd>

              <dt className="text-muted-foreground">Créé le</dt>
              <dd>{formatDate(e.created_at)}</dd>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-4 w-4" /> Inscription de l'année
            </CardTitle>
          </CardHeader>
          <CardContent>
            {inscriptionsQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Chargement…</p>
            ) : inscription === null ? (
              <div className="text-sm">
                <p className="mb-3 text-muted-foreground">
                  Aucune inscription pour cette année.
                </p>
                {can('inscriptions', 'create') && (
                  <Button asChild>
                    <Link to={`/eleves/${e.id}/inscrire`}>Créer l'inscription</Link>
                  </Button>
                )}
              </div>
            ) : (
              <dl className="grid grid-cols-2 gap-y-2 text-sm">
                <dt className="text-muted-foreground">Niveau</dt>
                <dd>
                  {niveau?.libelle ?? `#${inscription.niveau_id}`}{' '}
                  <Link to={`/inscriptions/${inscription.id}`} className="ml-1 text-xs text-primary underline">
                    voir
                  </Link>
                </dd>

                <dt className="text-muted-foreground">Écolage mensuel</dt>
                <dd><MoneyCell value={inscription.ecolage_mensuel} align={false} /></dd>

                <dt className="text-muted-foreground">Remise fratrie</dt>
                <dd>{inscription.remise_pct} %</dd>

                <dt className="text-muted-foreground">Droit d'inscription dû</dt>
                <dd><MoneyCell value={inscription.droit_inscription_du} align={false} /></dd>

                <dt className="text-muted-foreground">Frais généraux dus</dt>
                <dd><MoneyCell value={inscription.frais_generaux_du} align={false} /></dd>

                <dt className="text-muted-foreground">Statut</dt>
                <dd>{inscription.statut}</dd>
              </dl>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}