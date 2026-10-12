import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { parseApiError } from '@/lib/errors';
import { CaisseFgForm } from '../components/CaisseFgForm';
import { caisseFgApi } from '../api';
import type { CaisseFgCreatePayload } from '../schemas';

export function CaisseFgCreatePage() {
  const navigate = useNavigate();
  const [sp] = useSearchParams();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const sensParam = sp.get('sens');
  const defaultSens: 'ENTREE' | 'SORTIE' =
    sensParam === 'SORTIE' ? 'SORTIE' : 'ENTREE';

  const mutation = useMutation({
    mutationFn: (payload: CaisseFgCreatePayload) => caisseFgApi.create(payload),
    onSuccess: () => {
      toast.success('Opération enregistrée');
      qc.invalidateQueries({ queryKey: ['caisse-fg'] });
      navigate('/caisse-fg');
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
        title="Nouvelle opération de caisse FG"
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Caisse FG', to: '/caisse-fg' },
          { label: 'Nouvelle' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <CaisseFgForm
            defaultSens={defaultSens}
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(payload) => mutation.mutate(payload)}
            onCancel={() => navigate('/caisse-fg')}
          />
        </CardContent>
      </Card>
    </div>
  );
}