import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { parseApiError } from '@/lib/errors';
import { elevesApi } from '@/features/eleves/api';
import { InscriptionForm } from '../components/InscriptionForm';
import { inscriptionsApi } from '../api';
import type { InscriptionFormValues } from '../schemas';

export function InscriptionCreatePage() {
  const { id } = useParams<{ id: string }>();
  const eleveId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const eleveQuery = useQuery({
    queryKey: ['eleves', eleveId],
    queryFn: () => elevesApi.byId(eleveId),
    enabled: Number.isFinite(eleveId) && eleveId > 0,
  });

  const mutation = useMutation({
    mutationFn: (values: InscriptionFormValues) =>
      inscriptionsApi.create({
        eleve_id: values.eleve_id,
        niveau_id: values.niveau_id,
        mois_entree_id: values.mois_entree_id,
        ecolage_mensuel: values.ecolage_mensuel,
        remise_pct: values.remise_pct,
        droit_inscription_du: values.droit_inscription_du,
        frais_generaux_du: values.frais_generaux_du,
      }),
    onSuccess: (ins) => {
      toast.success('Inscription créée');
      qc.invalidateQueries({ queryKey: ['inscriptions'] });
      qc.invalidateQueries({ queryKey: ['eleves'] });
      navigate(`/inscriptions/${ins.id}`);
    },
    onError: (err) => {
      const parsed = parseApiError(err);
      if (parsed.fields.length > 0) {
        const map: Record<string, string> = {};
        for (const f of parsed.fields) map[f.field] = f.message;
        setFieldErrors(map);
        toast.error('Certains champs sont invalides.');
      } else if (parsed.status === 409) {
        toast.error("Cet élève est déjà inscrit pour l'année.");
      } else {
        toast.error(parsed.message);
      }
    },
  });

  if (eleveQuery.isLoading) {
    return <div className="text-sm text-muted-foreground">Chargement…</div>;
  }
  if (eleveQuery.isError || !eleveQuery.data) {
    return <ErrorState title="Élève introuvable" onRetry={() => navigate('/eleves')} />;
  }

  const eleve = eleveQuery.data;

  return (
    <div>
      <PageHeader
        title="Nouvelle inscription"
        subtitle={`${eleve.nom} ${eleve.prenoms} — ${eleve.matricule}`}
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Élèves', to: '/eleves' },
          { label: `${eleve.nom} ${eleve.prenoms}`, to: `/eleves/${eleve.id}` },
          { label: 'Inscrire' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          {eleve.famille_id === null && (
            <p className="mb-4 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning">
              Cet élève n'est rattaché à aucune famille. La remise fratrie ne sera pas appliquée.{' '}
              <Link to={`/eleves/${eleve.id}/modifier`} className="underline">
                Rattacher une famille
              </Link>
              .
            </p>
          )}
          <InscriptionForm
            eleveId={eleve.id}
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(values) => mutation.mutate(values)}
            onCancel={() => navigate(`/eleves/${eleve.id}`)}
          />
        </CardContent>
      </Card>
    </div>
  );
}