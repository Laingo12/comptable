import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { FormField } from '@/components/FormField';
import { referentielsApi } from '@/features/referentiels/api';
import { inscriptionsApi } from '@/features/inscriptions/api';
import {
  paiementFormSchema,
  toPaiementPayload,
  type PaiementFormValues,
  type PaiementCreatePayload,
} from '../schemas';

interface Props {
  inscriptionId?: number;
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (payload: PaiementCreatePayload) => void | Promise<void>;
  onCancel: () => void;
}

export function PaiementForm({
  inscriptionId, submitting, fieldErrors, onSubmit, onCancel,
}: Props) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const typesQuery = useQuery({
    queryKey: ['referentiels', 'types-paiement'],
    queryFn: referentielsApi.typesPaiement,
    staleTime: 10 * 60_000,
  });

  const modesQuery = useQuery({
    queryKey: ['referentiels', 'modes-paiement'],
    queryFn: referentielsApi.modesPaiement,
    staleTime: 10 * 60_000,
  });

  const moisQuery = useQuery({
    queryKey: ['referentiels', 'mois-scolaires'],
    queryFn: () => referentielsApi.moisScolaires(),
    staleTime: 10 * 60_000,
  });

  const inscriptionQuery = useQuery({
    queryKey: ['inscriptions', inscriptionId ?? 0],
    queryFn: () => inscriptionsApi.byId(inscriptionId!),
    enabled: !!inscriptionId,
  });

  const moisScolaires = useMemo(
    () => (moisQuery.data ?? []).filter((m) => m.est_scolaire),
    [moisQuery.data],
  );

  const {
    register, handleSubmit, watch, setError,
    formState: { errors },
  } = useForm<PaiementFormValues>({
    resolver: zodResolver(paiementFormSchema),
    defaultValues: {
      inscription_id: inscriptionId ?? 0,
      type_paiement_id: 0,
      mois_concerne_id: 0,
      montant: 0,
      date_paiement: today,
      mode_paiement_id: undefined,
      reference: '',
      observation: '',
    },
  });

  useEffect(() => {
    if (!fieldErrors) return;
    for (const [field, message] of Object.entries(fieldErrors)) {
      if (field in paiementFormSchema.shape) {
        setError(field as keyof PaiementFormValues, { type: 'server', message });
      }
    }
  }, [fieldErrors, setError]);

  const currentTypeId = watch('type_paiement_id');
  const currentType = typesQuery.data?.find((t) => t.id === Number(currentTypeId));
  const isEcolage = currentType?.code === 'ECOLAGE';

  const submit = handleSubmit(async (values) => {
    if (isEcolage && (!values.mois_concerne_id || values.mois_concerne_id <= 0)) {
      setError('mois_concerne_id', {
        type: 'manual',
        message: 'Mois obligatoire pour un écolage',
      });
      return;
    }
    await onSubmit(toPaiementPayload(values));
  });

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <input type="hidden" {...register('inscription_id')} />

      {inscriptionId && (
        <div className="rounded-md border bg-muted/40 p-3 text-sm">
          <p className="text-muted-foreground">Inscription</p>
          <p className="font-medium">
            #{inscriptionId}
            {inscriptionQuery.data && (
              <>
                {' '}— écolage mensuel{' '}
                <span className="tabular">
                  {inscriptionQuery.data.ecolage_mensuel.toLocaleString('fr-FR')} Ar
                </span>
              </>
            )}
          </p>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Type de paiement"
          htmlFor="type_paiement_id"
          error={errors.type_paiement_id?.message}
          required
        >
          <Select id="type_paiement_id" {...register('type_paiement_id')} autoFocus>
            <option value={0}>— Choisir —</option>
            {typesQuery.data?.map((t) => (
              <option key={t.id} value={t.id}>{t.libelle}</option>
            ))}
          </Select>
        </FormField>

        {isEcolage && (
          <FormField
            label="Mois concerné"
            htmlFor="mois_concerne_id"
            error={errors.mois_concerne_id?.message}
            required
          >
            <Select id="mois_concerne_id" {...register('mois_concerne_id')}>
              <option value={0}>— Choisir —</option>
              {moisScolaires.map((m) => (
                <option key={m.id} value={m.id}>{m.libelle}</option>
              ))}
            </Select>
          </FormField>
        )}

        <FormField
          label="Montant (Ariary)"
          htmlFor="montant"
          hint="Entier, sans décimale."
          error={errors.montant?.message}
          required
        >
          <Input
            id="montant"
            type="number"
            min={1}
            step={1}
            {...register('montant')}
          />
        </FormField>

        <FormField
          label="Date du paiement"
          htmlFor="date_paiement"
          error={errors.date_paiement?.message}
          required
        >
          <Input id="date_paiement" type="date" {...register('date_paiement')} />
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
          label="Observation"
          htmlFor="observation"
          error={errors.observation?.message}
          className="sm:col-span-2"
        >
          <Input id="observation" autoComplete="off" {...register('observation')} />
        </FormField>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Annuler
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Enregistrement…' : 'Enregistrer le paiement'}
        </Button>
      </div>
    </form>
  );
}