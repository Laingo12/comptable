import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { parseApiError } from '@/lib/errors';
import { FamilleForm } from '../components/FamilleForm';
import { famillesApi } from '../api';
import type { FamilleFormOutput } from '../schemas';

export function FamilleCreatePage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const mutation = useMutation({
    mutationFn: (values: FamilleFormOutput) => famillesApi.create(values),
    onSuccess: (famille) => {
      toast.success('Famille créée');
      qc.invalidateQueries({ queryKey: ['familles'] });
      navigate(`/familles/${famille.id}`);
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
        title="Nouvelle famille"
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Familles', to: '/familles' },
          { label: 'Nouvelle' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <FamilleForm
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(values) => mutation.mutate(values)}
            onCancel={() => navigate('/familles')}
          />
        </CardContent>
      </Card>
    </div>
  );
}