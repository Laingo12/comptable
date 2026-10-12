import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { PageHeader } from '@/components/PageHeader';
import { parseApiError } from '@/lib/errors';
import { PaiementForm } from '../components/PaiementForm';
import { paiementsApi } from '../api';
import type { PaiementCreatePayload } from '../schemas';

export function PaiementCreatePage() {
  const navigate = useNavigate();
  const [sp] = useSearchParams();
  const qc = useQueryClient();
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const inscriptionParam = sp.get('inscription_id');
  const inscriptionId = inscriptionParam ? Number(inscriptionParam) : undefined;

  const mutation = useMutation({
    mutationFn: (payload: PaiementCreatePayload) => paiementsApi.create(payload),
    onSuccess: (p) => {
      toast.success('Paiement enregistré');
      qc.invalidateQueries({ queryKey: ['paiements'] });
      qc.invalidateQueries({ queryKey: ['situation'] });
      if (p.inscription_id) {
        navigate(`/inscriptions/${p.inscription_id}`);
      } else {
        navigate('/paiements');
      }
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
        title="Nouveau paiement"
        subtitle={
          inscriptionId
            ? `Inscription #${inscriptionId}`
            : "Sélectionnez l'inscription"
        }
        breadcrumb={[
          { label: 'Accueil', to: '/' },
          { label: 'Paiements', to: '/paiements' },
          { label: 'Nouveau' },
        ]}
      />
      <Card>
        <CardContent className="pt-6">
          <PaiementForm
            inscriptionId={inscriptionId}
            submitting={mutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(payload) => mutation.mutate(payload)}
            onCancel={() => navigate('/paiements')}
          />
        </CardContent>
      </Card>
    </div>
  );
}