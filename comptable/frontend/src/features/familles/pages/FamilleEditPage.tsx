import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { ErrorState } from '@/components/ErrorState';
import { parseApiError } from '@/lib/errors';
import { FamilleForm } from '../components/FamilleForm';
import { famillesApi } from '../api';
import type { FamilleFormOutput } from '../schemas';

export function FamilleEditPage() {
  const { id } = useParams<{ id: string }>();
  const familleId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const query = useQuery({
    queryKey: ['familles', familleId],
    queryFn: () => famillesApi.byId(familleId),
    enabled: Number.isFinite(familleId) && familleId > 0,
  });

  useEffect(() => {
    setFieldErrors({});
  }, [familleId]);

  const mutation = useMutation({
    mutationFn: (values: FamilleFormOutput) => famillesApi.update(familleId, values),
    onSuccess: () => {
      toast.success('Famille enregistrée');
      qc.invalidateQueries({ queryKey: ['familles'] });
      navigate(`/familles/${familleId}`);
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
    return <ErrorState title="Famille introuvable" onRetry={() => navigate('/familles')} />;
  }

  return (
    <div>
      <PageHeader
        title={`Modifier ${query.data.nom}`}
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Familles', to: '/familles' },
          { label: query.data.nom, to: `/familles/${familleId}` },
          { label: 'Modifier' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <FamilleForm
            initial={query.data}
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(values) => mutation.mutate(values)}
            onCancel={() => navigate(`/familles/${familleId}`)}
          />
        </CardContent>
      </Card>
    </div>
  );
}