import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { FormField } from '@/components/FormField';
import { MoneyCell } from '@/components/MoneyCell';
import { formatAr } from '@/lib/format';
import { referentielsApi } from '@/features/referentiels/api';
import {
  paiementSalaireSchema,
  toPaiementSalairePayload,
  type PaiementSalaireValues,
  type PaiementSalairePayload,
} from '../schemas';
import type { SalaireMensuelRead, PaiementSalaireRead } from '../api';

interface Props {
  salaire: SalaireMensuelRead;
  /** Payés déjà enregistrés pour ce salaire (net d'annulations). */
  paiementsExistants: PaiementSalaireRead[];
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (payload: PaiementSalairePayload) => void | Promise<void>;
  onCancel: () => void;
}

export function PaiementSalaireForm({
  salaire,
  paiementsExistants,
  submitting,
  fieldErrors,
  onSubmit,
  onCancel,
}: Props) {
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const modesQuery = useQuery({
    queryKey: ['referentiels', 'modes-paiement'],
    queryFn: referentielsApi.modesPaiement,
    staleTime: 10 * 60_000,
  });

  // Calcule les montants déjà payés par type et le reste.
  const analyse = useMemo(() => {
    const paye70 = paiementsExistants
      .filter((p) => p.type_part === 'AVANCE_70' && p.parent_paiement_salaire_id === null)
      .reduce((s, p) => s + p.montant, 0);
    const paye30 = paiementsExistants
      .filter((p) => p.type_part === 'SOLDE_30' && p.parent_paiement_salaire_id === null)
      .reduce((s, p) => s + p.montant, 0);
    const brut = salaire.montant_brut;
    const du70 = Math.round((brut * 70) / 100);
    const du30 = brut - du70;
    return {
      paye70, paye30,
      du70, du30,
      reste70: Math.max(0, du70 - paye70),
      reste30: Math.max(0, du30 - paye30),
    };
  }, [salaire, paiementsExistants]);

  const {
    register, handleSubmit, watch, setValue, setError,
    formState: { errors },
  } = useForm<PaiementSalaireValues>({
    resolver: zodResolver(paiementSalaireSchema),
    defaultValues: {
      salaire_mensuel_id: salaire.id,
      type_part: analyse.reste70 > 0 ? 'AVANCE_70' : 'SOLDE_30',
      montant: analyse.reste70 > 0 ? analyse.reste70 : analyse.reste30,
      date_paiement: today,
      mode_paiement_id: 0,
      reference: '',
      observation: '',
    },
  });

  // Quand le type change, on propose le montant du au titre de ce type.
  const currentPart = watch('type_part');
  useEffect(() => {
    if (currentPart === 'AVANCE_70') {
      setValue('montant', analyse.reste70);
    } else {
      setValue('montant', analyse.reste30);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPart]);

  useEffect(() => {
    if (!fieldErrors) return;
    for (const [field, message] of Object.entries(fieldErrors)) {
      if (field in paiementSalaireSchema.shape) {
        setError(field as keyof PaiementSalaireValues, { type: 'server', message });
      }
    }
  }, [fieldErrors, setError]);

  const submit = handleSubmit(async (values) => {
    await onSubmit(toPaiementSalairePayload(values));
  });

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <input type="hidden" {...register('salaire_mensuel_id')} />

      <div className="rounded-md border bg-muted/40 p-3 text-sm space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Salaire brut</span>
          <MoneyCell value={salaire.montant_brut} align={false} />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Avance 70 % — payé / dû</span>
          <span className="tabular">
            {formatAr(analyse.paye70)} / {formatAr(analyse.du70)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Solde 30 % — payé / dû</span>
          <span className="tabular">
            {formatAr(analyse.paye30)} / {formatAr(analyse.du30)}
          </span>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Part"
          htmlFor="type_part"
          error={errors.type_part?.message}
          required
        >
          <Select id="type_part" {...register('type_part')}>
            <option value="AVANCE_70">
              Avance 70 % (reste {formatAr(analyse.reste70)})
            </option>
            <option value="SOLDE_30">
              Solde 30 % (reste {formatAr(analyse.reste30)})
            </option>
          </Select>
        </FormField>

        <FormField
          label="Montant (Ariary)"
          htmlFor="montant"
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