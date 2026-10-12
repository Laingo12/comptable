import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { FormField } from '@/components/FormField';
import { famillesApi } from '@/features/familles/api';
import { eleveFormSchema, type EleveFormValues, type EleveFormOutput } from '../schemas';
import type { EleveRead } from '../api';

interface Props {
  initial?: EleveRead | null;
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (values: EleveFormOutput) => void | Promise<void>;
  onCancel: () => void;
}

export function EleveForm({
  initial = null, submitting, fieldErrors, onSubmit, onCancel,
}: Props) {
  const isEdit = initial !== null;

  const famillesQuery = useQuery({
    queryKey: ['familles', 'options'],
    queryFn: () => famillesApi.list({ page: 1, page_size: 200, sort: 'nom:asc' }),
    staleTime: 5 * 60_000,
  });

  const {
    register, handleSubmit, setError, formState: { errors },
  } = useForm<EleveFormValues>({
    resolver: zodResolver(eleveFormSchema),
    defaultValues: {
      matricule: initial?.matricule ?? '',
      nom: initial?.nom ?? '',
      prenoms: initial?.prenoms ?? '',
      sexe: (initial?.sexe as 'M' | 'F' | '' | undefined) ?? '',
      date_naissance: initial?.date_naissance ?? '',
      famille_id: initial?.famille_id ?? '',
    },
  });

  // Propage les erreurs 422 renvoyées par le parent.
  useEffect(() => {
    if (!fieldErrors) return;
    for (const [field, message] of Object.entries(fieldErrors)) {
      if (field in eleveFormSchema.shape) {
        setError(field as keyof EleveFormValues, { type: 'server', message });
      }
    }
  }, [fieldErrors, setError]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Matricule"
          htmlFor="matricule"
          hint={isEdit ? 'Non modifiable.' : 'Laissez vide pour générer automatiquement.'}
          error={errors.matricule?.message}
        >
          <Input
            id="matricule"
            autoComplete="off"
            readOnly={isEdit}
            className={isEdit ? 'cursor-not-allowed bg-muted' : undefined}
            {...register('matricule')}
          />
        </FormField>

        <FormField label="Sexe" htmlFor="sexe" error={errors.sexe?.message}>
          <Select id="sexe" {...register('sexe')}>
            <option value="">—</option>
            <option value="M">Masculin</option>
            <option value="F">Féminin</option>
          </Select>
        </FormField>

        <FormField label="Nom" htmlFor="nom" error={errors.nom?.message} required>
          <Input id="nom" autoComplete="family-name" {...register('nom')} />
        </FormField>

        <FormField label="Prénoms" htmlFor="prenoms" error={errors.prenoms?.message} required>
          <Input id="prenoms" autoComplete="given-name" {...register('prenoms')} />
        </FormField>

        <FormField label="Date de naissance" htmlFor="date_naissance" error={errors.date_naissance?.message}>
          <Input id="date_naissance" type="date" {...register('date_naissance')} />
        </FormField>

        <FormField
          label="Famille"
          htmlFor="famille_id"
          hint="Regroupe les frères et sœurs (remise fratrie)."
          error={errors.famille_id?.message}
        >
          <Select id="famille_id" {...register('famille_id')}>
            <option value="">— Aucune —</option>
            {famillesQuery.data?.items.map((f) => (
              <option key={f.id} value={f.id}>{f.nom}</option>
            ))}
          </Select>
        </FormField>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Annuler
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Enregistrement…' : isEdit ? 'Enregistrer' : 'Créer l\'élève'}
        </Button>
      </div>
    </form>
  );
}