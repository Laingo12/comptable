import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { parseApiError } from '@/lib/errors';
import { PrelevementForm } from '../components/PrelevementForm';
import { prelevementsApi } from '../api';
import type { PrelevementCreatePayload } from '../schemas';

export function PrelevementCreatePage() {
  const navigate = useNavigate();
  const [sp] = useSearchParams();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const associeParam = sp.get('associe_id');
  const associeId = associeParam ? Number(associeParam) : undefined;

  const mutation = useMutation({
    mutationFn: (payload: PrelevementCreatePayload) =>
      prelevementsApi.create(payload),
    onSuccess: () => {
      toast.success('Prélèvement enregistré');
      qc.invalidateQueries({ queryKey: ['prelevements'] });
      navigate('/prelevements');
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

  return (
    <div>
      <PageHeader
        title="Nouveau prélèvement"
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Prélèvements', to: '/prelevements' },
          { label: 'Nouveau' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <PrelevementForm
            associeId={associeId}
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(payload) => mutation.mutate(payload)}
            onCancel={() => navigate('/prelevements')}
          />
        </CardContent>
      </Card>
    </div>
  );
}