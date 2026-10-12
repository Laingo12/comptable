import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { parseApiError } from '@/lib/errors';
import { InscriptionForm } from '../components/InscriptionForm';
import { inscriptionsApi } from '../api';
import {
  toInscriptionUpdatePayload,
  type InscriptionFormValues,
} from '../schemas';

export function InscriptionEditPage() {
  const { id } = useParams<{ id: string }>();
  const inscriptionId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const query = useQuery({
    queryKey: ['inscriptions', inscriptionId],
    queryFn: () => inscriptionsApi.byId(inscriptionId),
    enabled: Number.isFinite(inscriptionId) && inscriptionId > 0,
  });

  useEffect(() => { setFieldErrors({}); }, [inscriptionId]);

  const mutation = useMutation({
    mutationFn: (values: InscriptionFormValues) =>
      inscriptionsApi.update(inscriptionId, toInscriptionUpdatePayload(values)),
    onSuccess: () => {
      toast.success('Inscription enregistrée');
      qc.invalidateQueries({ queryKey: ['inscriptions'] });
      navigate(`/inscriptions/${inscriptionId}`);
    },
    onError: (err) => {
      const parsed = parseApiError(err);
      if (parsed.fields.length > 0) {
        const map: Record<string, string> = {};
        for (const f of parsed.fields) map[f.field] = f.message;
        setFieldErrors(map);
        toast.error('Certains champs sont invalides.');
      } else {
        toast.error(parsed.message);
      }
    },
  });

  if (query.isLoading) {
    return <div className="text-sm text-muted-foreground">Chargement…</div>;
  }
  if (query.isError || !query.data) {
    return <ErrorState title="Inscription introuvable" onRetry={() => navigate('/eleves')} />;
  }

  const ins = query.data;

  return (
    <div>
      <PageHeader
        title="Modifier l'inscription"
        subtitle={`Élève #${ins.eleve_id} — Année #${ins.annee_scolaire_id}`}
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Élèves', to: '/eleves' },
          { label: `Élève #${ins.eleve_id}`, to: `/eleves/${ins.eleve_id}` },
          { label: 'Inscription', to: `/inscriptions/${ins.id}` },
          { label: 'Modifier' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <InscriptionForm
            eleveId={ins.eleve_id}
            initial={ins}
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(values) => mutation.mutate(values)}
            onCancel={() => navigate(`/inscriptions/${ins.id}`)}
          />
        </CardContent>
      </Card>
    </div>
  );
}