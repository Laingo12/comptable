import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { parseApiError } from '@/lib/errors';
import { EleveForm } from '../components/EleveForm';
import { elevesApi } from '../api';
import type { EleveFormOutput } from '../schemas';

export function EleveEditPage() {
  const { id } = useParams<{ id: string }>();
  const eleveId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const query = useQuery({
    queryKey: ['eleves', eleveId],
    queryFn: () => elevesApi.byId(eleveId),
    enabled: Number.isFinite(eleveId) && eleveId > 0,
  });

  useEffect(() => {
    setFieldErrors({});
  }, [eleveId]);

  const mutation = useMutation({
    mutationFn: (values: EleveFormOutput) => {
      // Le schéma Pydantic `EleveUpdate` ignore les clés en trop
      // (extra='ignore' par défaut), on peut donc transmettre `values` tel quel.
      return elevesApi.update(eleveId, values);
    },
    onSuccess: () => {
      toast.success('Élève enregistré');
      qc.invalidateQueries({ queryKey: ['eleves'] });
      navigate(`/eleves/${eleveId}`);
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
    return (
      <ErrorState
        title="Élève introuvable"
        onRetry={() => navigate('/eleves')}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title={`Modifier ${query.data.nom} ${query.data.prenoms}`}
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Élèves', to: '/eleves' },
          { label: `${query.data.nom} ${query.data.prenoms}`, to: `/eleves/${eleveId}` },
          { label: 'Modifier' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <EleveForm
            initial={query.data}
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(values) => mutation.mutate(values)}
            onCancel={() => navigate(`/eleves/${eleveId}`)}
          />
        </CardContent>
      </Card>
    </div>
  );
}