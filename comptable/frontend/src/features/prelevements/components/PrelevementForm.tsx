import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { FormField } from '@/components/FormField';
import { referentielsApi } from '@/features/referentiels/api';
import { associesApi } from '@/features/associes/api';
import {
  prelevementFormSchema,
  toPrelevementPayload,
  type PrelevementFormValues,
  type PrelevementCreatePayload,
} from '../schemas';

interface Props {
  associeId?: number;
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (payload: PrelevementCreatePayload) => void | Promise<void>;
  onCancel: () => void;
}

export function PrelevementForm({
  associeId, submitting, fieldErrors, onSubmit, onCancel,
}: Props) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const associesQuery = useQuery({
    queryKey: ['associes'],
    queryFn: associesApi.list,
    staleTime: 5 * 60_000,
  });

  const modesQuery = useQuery({
    queryKey: ['referentiels', 'modes-paiement'],
    queryFn: referentielsApi.modesPaiement,
    staleTime: 10 * 60_000,
  });

  const {
    register, handleSubmit, setError,
    formState: { errors },
  } = useForm<PrelevementFormValues>({
    resolver: zodResolver(prelevementFormSchema),
    defaultValues: {
      associe_id: associeId ?? 0,
      type: 'RETRAIT',
      montant: 0,
      date_prelevement: today,
      destinataire: '',
      motif: '',
      mode_paiement_id: 0,
      reference: '',
    },
  });

  useEffect(() => {
    if (!fieldErrors) return;
    for (const [field, message] of Object.entries(fieldErrors)) {
      if (field in prelevementFormSchema.shape) {
        setError(field as keyof PrelevementFormValues, { type: 'server', message });
      }
    }
  }, [fieldErrors, setError]);

  const submit = handleSubmit(async (values) => {
    await onSubmit(toPrelevementPayload(values));
  });

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Associé"
          htmlFor="associe_id"
          error={errors.associe_id?.message}
          required
        >
          <Select id="associe_id" {...register('associe_id')} autoFocus disabled={!!associeId}>
            <option value={0}>— Choisir —</option>
            {associesQuery.data?.map((a) => (
              <option key={a.id} value={a.id}>{a.nom}</option>
            ))}
          </Select>
        </FormField>

        <FormField label="Type" htmlFor="type" error={errors.type?.message} required>
          <Select id="type" {...register('type')}>
            <option value="RETRAIT">Retrait</option>
            <option value="VERSEMENT_FIXE">Versement fixe</option>
            <option value="SUPPLEMENT">Supplément</option>
          </Select>
        </FormField>

        <FormField
          label="Montant (Ariary)"
          htmlFor="montant"
          hint="Entier, sans décimale."
          error={errors.montant?.message}
          required
        >
          <Input id="montant" type="number" min={1} step={1} {...register('montant')} />
        </FormField>

        <FormField
          label="Date du prélèvement"
          htmlFor="date_prelevement"
          error={errors.date_prelevement?.message}
          required
        >
          <Input id="date_prelevement" type="date" {...register('date_prelevement')} />
        </FormField>

        <FormField
          label="Destinataire"
          htmlFor="destinataire"
          hint="Qui a reçu l'argent (texte libre)."
          error={errors.destinataire?.message}
        >
          <Input id="destinataire" autoComplete="off" {...register('destinataire')} />
        </FormField>

        <FormField label="Motif" htmlFor="motif" error={errors.motif?.message}>
          <Input id="motif" autoComplete="off" {...register('motif')} />
        </FormField>

        <FormField
          label="Mode de paiement"
          htmlFor="mode_paiement_id"
          error={errors.mode_paiement_id?.message}
        >
          <Select id="mode_paiement_id" {...register('mode_paiement_id')}>
            <option value={0}>—</option>
            {modesQuery.data?.map((m) => (
              <option key={m.id} value={m.id}>{m.libelle}</option>
            ))}
          </Select>
        </FormField>

        <FormField label="Référence" htmlFor="reference" error={errors.reference?.message}>
          <Input id="reference" autoComplete="off" {...register('reference')} />
        </FormField>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Annuler
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Enregistrement…' : 'Enregistrer le prélèvement'}
        </Button>
      </div>
    </form>
  );
}