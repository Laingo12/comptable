import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { FormField } from '@/components/FormField';
import { referentielsApi } from '@/features/referentiels/api';
import {
  caisseFgFormSchema,
  toCaisseFgPayload,
  type CaisseFgFormValues,
  type CaisseFgCreatePayload,
} from '../schemas';

interface Props {
  defaultSens?: 'ENTREE' | 'SORTIE';
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (payload: CaisseFgCreatePayload) => void | Promise<void>;
  onCancel: () => void;
}

export function CaisseFgForm({
  defaultSens = 'ENTREE', submitting, fieldErrors, onSubmit, onCancel,
}: Props) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const modesQuery = useQuery({
    queryKey: ['referentiels', 'modes-paiement'],
    queryFn: referentielsApi.modesPaiement,
    staleTime: 10 * 60_000,
  });

  const {
    register, handleSubmit, setError,
    formState: { errors },
  } = useForm<CaisseFgFormValues>({
    resolver: zodResolver(caisseFgFormSchema),
    defaultValues: {
      sens: defaultSens,
      montant: 0,
      libelle: '',
      date_operation: today,
      remarque: '',
      mode_paiement_id: 0,
      reference: '',
    },
  });

  useEffect(() => {
    if (!fieldErrors) return;
    for (const [field, message] of Object.entries(fieldErrors)) {
      if (field in caisseFgFormSchema.shape) {
        setError(field as keyof CaisseFgFormValues, { type: 'server', message });
      }
    }
  }, [fieldErrors, setError]);

  const submit = handleSubmit(async (values) => {
    await onSubmit(toCaisseFgPayload(values));
  });

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Sens" htmlFor="sens" error={errors.sens?.message} required>
          <Select id="sens" {...register('sens')} autoFocus>
            <option value="ENTREE">Entrée (encaissement)</option>
            <option value="SORTIE">Sortie (décaissement)</option>
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
          label="Libellé"
          htmlFor="libelle"
          error={errors.libelle?.message}
          required
          className="sm:col-span-2"
        >
          <Input id="libelle" autoComplete="off" {...register('libelle')} />
        </FormField>

        <FormField
          label="Date de l'opération"
          htmlFor="date_operation"
          error={errors.date_operation?.message}
          required
        >
          <Input id="date_operation" type="date" {...register('date_operation')} />
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

        <FormField
          label="Remarque"
          htmlFor="remarque"
          error={errors.remarque?.message}
        >
          <Input id="remarque" autoComplete="off" {...register('remarque')} />
        </FormField>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Annuler
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Enregistrement…' : "Enregistrer l'opération"}
        </Button>
      </div>
    </form>
  );
}