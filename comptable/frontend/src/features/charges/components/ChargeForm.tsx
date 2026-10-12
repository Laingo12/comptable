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
  chargeFormSchema,
  toChargePayload,
  type ChargeFormValues,
  type ChargeCreatePayload,
} from '../schemas';

interface Props {
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (payload: ChargeCreatePayload) => void | Promise<void>;
  onCancel: () => void;
}

export function ChargeForm({ submitting, fieldErrors, onSubmit, onCancel }: Props) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const moisQuery = useQuery({
    queryKey: ['referentiels', 'mois-scolaires'],
    queryFn: () => referentielsApi.moisScolaires(),
    staleTime: 10 * 60_000,
  });

  const modesQuery = useQuery({
    queryKey: ['referentiels', 'modes-paiement'],
    queryFn: referentielsApi.modesPaiement,
    staleTime: 10 * 60_000,
  });

  const catalogueQuery = useQuery({
    queryKey: ['referentiels', 'charges-catalogue'],
    queryFn: referentielsApi.chargesCatalogue,
    staleTime: 10 * 60_000,
  });

  const moisScolaires = useMemo(
    () => (moisQuery.data ?? []).filter((m) => m.est_scolaire),
    [moisQuery.data],
  );

  const {
    register, handleSubmit, watch, setValue, setError,
    formState: { errors },
  } = useForm<ChargeFormValues>({
    resolver: zodResolver(chargeFormSchema),
    defaultValues: {
      mois_id: 0,
      charge_catalogue_id: 0,
      libelle: '',
      categorie: 'VARIABLE',
      montant: 0,
      date_operation: today,
      mode_paiement_id: 0,
      reference: '',
      observation: '',
    },
  });

  // Suggestion : quand on choisit une entrée du catalogue,
  // on pré-remplit le libellé et la catégorie.
  const currentCatalogueId = watch('charge_catalogue_id');
  useEffect(() => {
    if (!currentCatalogueId || currentCatalogueId <= 0) return;
    const entry = catalogueQuery.data?.find((c) => c.id === Number(currentCatalogueId));
    if (!entry) return;
    setValue('libelle', entry.libelle);
    setValue('categorie', entry.categorie as 'FIXE' | 'VARIABLE' | 'AUTRE');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentCatalogueId, catalogueQuery.data]);

  useEffect(() => {
    if (!fieldErrors) return;
    for (const [field, message] of Object.entries(fieldErrors)) {
      if (field in chargeFormSchema.shape) {
        setError(field as keyof ChargeFormValues, { type: 'server', message });
      }
    }
  }, [fieldErrors, setError]);

  const submit = handleSubmit(async (values) => {
    await onSubmit(toChargePayload(values));
  });

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Catalogue"
          htmlFor="charge_catalogue_id"
          hint="Pré-remplit le libellé et la catégorie."
        >
          <Select id="charge_catalogue_id" {...register('charge_catalogue_id')} autoFocus>
            <option value={0}>— Aucun (saisie libre) —</option>
            {catalogueQuery.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.libelle} ({c.categorie})
              </option>
            ))}
          </Select>
        </FormField>

        <FormField
          label="Catégorie"
          htmlFor="categorie"
          error={errors.categorie?.message}
          required
        >
          <Select id="categorie" {...register('categorie')}>
            <option value="FIXE">Fixe</option>
            <option value="VARIABLE">Variable</option>
            <option value="AUTRE">Autre</option>
          </Select>
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
          label="Montant (Ariary)"
          htmlFor="montant"
          hint="Entier, sans décimale."
          error={errors.montant?.message}
          required
        >
          <Input id="montant" type="number" min={1} step={1} {...register('montant')} />
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
          label="Mois concerné (optionnel)"
          htmlFor="mois_id"
          hint="Laisser vide : le mois est dérivé de la date."
          error={errors.mois_id?.message}
        >
          <Select id="mois_id" {...register('mois_id')}>
            <option value={0}>— Automatique —</option>
            {moisScolaires.map((m) => (
              <option key={m.id} value={m.id}>{m.libelle}</option>
            ))}
          </Select>
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
          {submitting ? 'Enregistrement…' : 'Enregistrer la charge'}
        </Button>
      </div>
    </form>
  );
}