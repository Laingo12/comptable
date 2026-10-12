import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { FormField } from '@/components/FormField';
import {
  familleFormSchema,
  toFamillePayload,
  type FamilleFormValues,
  type FamilleFormOutput,
} from '../schemas';
import type { FamilleRead } from '../api';

interface Props {
  initial?: FamilleRead | null;
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (values: FamilleFormOutput) => void | Promise<void>;
  onCancel: () => void;
}

export function FamilleForm({
  initial = null, submitting, fieldErrors, onSubmit, onCancel,
}: Props) {
  const isEdit = initial !== null;

  const {
    register, handleSubmit, setError, formState: { errors },
  } = useForm<FamilleFormValues>({
    resolver: zodResolver(familleFormSchema),
    defaultValues: {
      nom: initial?.nom ?? '',
      contact_principal: initial?.contact_principal ?? '',
      telephone: initial?.telephone ?? '',
      email: initial?.email ?? '',
      adresse: initial?.adresse ?? '',
      notes: initial?.notes ?? '',
    },
  });

  useEffect(() => {
    if (!fieldErrors) return;
    for (const [field, message] of Object.entries(fieldErrors)) {
      if (field in familleFormSchema.shape) {
        setError(field as keyof FamilleFormValues, { type: 'server', message });
      }
    }
  }, [fieldErrors, setError]);

  const submit = handleSubmit(async (values) => {
    await onSubmit(toFamillePayload(values));
  });

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Nom de la famille" htmlFor="nom" error={errors.nom?.message} required>
          <Input id="nom" autoComplete="off" autoFocus {...register('nom')} />
        </FormField>

        <FormField label="Contact principal" htmlFor="contact_principal" error={errors.contact_principal?.message}>
          <Input id="contact_principal" autoComplete="off" {...register('contact_principal')} />
        </FormField>

        <FormField
          label="Téléphone"
          htmlFor="telephone"
          hint="Utilisé pour contacter la famille, pas pour la fratrie."
          error={errors.telephone?.message}
        >
          <Input id="telephone" autoComplete="tel" {...register('telephone')} />
        </FormField>

        <FormField label="Email" htmlFor="email" error={errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...register('email')} />
        </FormField>

        <FormField label="Adresse" htmlFor="adresse" error={errors.adresse?.message} className="sm:col-span-2">
          <Input id="adresse" autoComplete="street-address" {...register('adresse')} />
        </FormField>

        <FormField label="Notes" htmlFor="notes" error={errors.notes?.message} className="sm:col-span-2">
          <Input id="notes" autoComplete="off" {...register('notes')} />
        </FormField>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Annuler
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Enregistrement…' : isEdit ? 'Enregistrer' : 'Créer la famille'}
        </Button>
      </div>
    </form>
  );
}