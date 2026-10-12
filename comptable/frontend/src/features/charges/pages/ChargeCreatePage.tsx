import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { parseApiError } from '@/lib/errors';
import { ChargeForm } from '../components/ChargeForm';
import { chargesApi } from '../api';
import type { ChargeCreatePayload } from '../schemas';

export function ChargeCreatePage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const mutation = useMutation({
    mutationFn: (payload: ChargeCreatePayload) => chargesApi.create(payload),
    onSuccess: () => {
      toast.success('Charge enregistrée');
      qc.invalidateQueries({ queryKey: ['charges'] });
      navigate('/charges');
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
        title="Nouvelle charge"
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Charges', to: '/charges' },
          { label: 'Nouvelle' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <ChargeForm
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(payload) => mutation.mutate(payload)}
            onCancel={() => navigate('/charges')}
          />
        </CardContent>
      </Card>
    </div>
  );
}