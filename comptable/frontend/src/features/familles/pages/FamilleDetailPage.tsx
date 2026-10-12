import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { Pencil, Users2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/format';
import { useAuth } from '@/features/auth/useAuth';
import { elevesApi } from '@/features/eleves/api';
import { famillesApi } from '../api';

export function FamilleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const familleId = Number(id);
  const navigate = useNavigate();
  const { can } = useAuth();

  const query = useQuery({
    queryKey: ['familles', familleId],
    queryFn: () => famillesApi.byId(familleId),
    enabled: Number.isFinite(familleId) && familleId > 0,
  });

  const elevesQuery = useQuery({
    queryKey: ['eleves', 'par-famille', familleId],
    queryFn: () => elevesApi.list({ page: 1, page_size: 200, famille_id: familleId, sort: 'nom:asc' }),
    enabled: Number.isFinite(familleId) && familleId > 0,
  });

  if (query.isLoading) {
    return <div className="text-sm text-muted-foreground">Chargement…</div>;
  }
  if (query.isError || !query.data) {
    return <ErrorState title="Famille introuvable" onRetry={() => navigate('/familles')} />;
  }

  const f = query.data;

  return (
    <div>
      <PageHeader
        title={f.nom}
        subtitle={`Famille #${f.id}`}
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Familles', to: '/familles' },
          { label: f.nom },
        ]}
        actions={
          can('familles', 'update') && (
            <Button asChild variant="outline">
              <Link to={`/familles/${f.id}/modifier`}>
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
              <Users2 className="h-4 w-4" /> Coordonnées
            </CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-muted-foreground">Nom</dt>
              <dd>{f.nom}</dd>

              <dt className="text-muted-foreground">Contact principal</dt>
              <dd>{f.contact_principal ?? '—'}</dd>

              <dt className="text-muted-foreground">Téléphone</dt>
              <dd className="tabular">{f.telephone ?? '—'}</dd>

              <dt className="text-muted-foreground">Email</dt>
              <dd>{f.email ?? '—'}</dd>

              <dt className="text-muted-foreground">Adresse</dt>
              <dd>{f.adresse ?? '—'}</dd>

              <dt className="text-muted-foreground">Notes</dt>
              <dd>{f.notes ?? '—'}</dd>

              <dt className="text-muted-foreground">Créée le</dt>
              <dd>{formatDate(f.created_at)}</dd>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Élèves rattachés</CardTitle>
          </CardHeader>
          <CardContent>
            {elevesQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Chargement…</p>
            ) : elevesQuery.isError ? (
              <p className="text-sm text-danger">Impossible de charger les élèves.</p>
            ) : (elevesQuery.data?.items.length ?? 0) === 0 ? (
              <p className="text-sm text-muted-foreground">
                Aucun élève rattaché. Rattachez-en depuis la fiche d'un élève.
              </p>
            ) : (
              <ul className="divide-y">
                {elevesQuery.data!.items.map((e) => (
                  <li key={e.id} className="flex items-center justify-between py-2 text-sm">
                    <Link to={`/eleves/${e.id}`} className="hover:text-primary hover:underline">
                      {e.nom} <span className="text-muted-foreground">{e.prenoms}</span>
                    </Link>
                    <Badge variant="secondary" className="tabular font-mono text-[10px]">
                      {e.matricule}
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}