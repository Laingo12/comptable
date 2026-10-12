import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { parseApiError } from '@/lib/errors';
import { EleveForm } from '../components/EleveForm';
import { elevesApi } from '../api';
import type { EleveFormOutput } from '../schemas';

export function EleveCreatePage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const mutation = useMutation({
    mutationFn: (values: EleveFormOutput) => elevesApi.create(values),
    onSuccess: (eleve) => {
      toast.success('Élève créé');
      qc.invalidateQueries({ queryKey: ['eleves'] });
      navigate(`/eleves/${eleve.id}`);
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
        title="Nouvel élève"
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Élèves', to: '/eleves' },
          { label: 'Nouveau' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <EleveForm
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(values) => mutation.mutate(values)}
            onCancel={() => navigate('/eleves')}
          />
        </CardContent>
      </Card>
    </div>
  );
}