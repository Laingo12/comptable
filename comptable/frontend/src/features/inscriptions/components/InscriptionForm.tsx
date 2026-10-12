import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { FormField } from '@/components/FormField';
import { MoneyCell } from '@/components/MoneyCell';
import { referentielsApi } from '@/features/referentiels/api';
import {
  inscriptionFormSchema,
  type InscriptionFormValues,
} from '../schemas';
import type { InscriptionRead } from '../api';

interface Props {
  eleveId: number;
  initial?: InscriptionRead | null;
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (values: InscriptionFormValues) => void | Promise<void>;
  onCancel: () => void;
}

export function InscriptionForm({
  eleveId, initial = null, submitting, fieldErrors, onSubmit, onCancel,
}: Props) {
  const isEdit = initial !== null;

  const niveauxQuery = useQuery({
    queryKey: ['referentiels', 'niveaux'],
    queryFn: referentielsApi.niveaux,
    staleTime: 10 * 60_000,
  });

  const moisQuery = useQuery({
    queryKey: ['referentiels', 'mois-scolaires'],
    queryFn: () => referentielsApi.moisScolaires(),
    staleTime: 10 * 60_000,
  });

  const grilleQuery = useQuery({
    queryKey: ['referentiels', 'grille-tarifaire'],
    queryFn: () => referentielsApi.grilleTarifaire(),
    staleTime: 10 * 60_000,
  });

  const moisScolaires = useMemo(
    () => (moisQuery.data ?? []).filter((m) => m.est_scolaire),
    [moisQuery.data],
  );

  const {
    register, handleSubmit, setValue, watch, setError,
    formState: { errors },
  } = useForm<InscriptionFormValues>({
    resolver: zodResolver(inscriptionFormSchema),
    defaultValues: {
      eleve_id: eleveId,
      niveau_id: initial?.niveau_id ?? 0,
      mois_entree_id: initial?.mois_entree_id ?? 0,
      ecolage_mensuel: initial?.ecolage_mensuel ?? 0,
      remise_pct: initial?.remise_pct ?? 0,
      droit_inscription_du: initial?.droit_inscription_du ?? 0,
      frais_generaux_du: initial?.frais_generaux_du ?? 0,
    },
  });

  const currentNiveau = watch('niveau_id');

  // Suggestion tarifaire : quand le niveau change (en création), on pré-remplit.
  useEffect(() => {
    if (isEdit) return;
    if (!currentNiveau) return;
    const grille = grilleQuery.data?.find((g) => g.niveau_id === Number(currentNiveau));
    if (!grille) return;
    setValue('ecolage_mensuel', grille.ecolage_mensuel);
    setValue('droit_inscription_du', grille.droit_inscription);
    setValue('frais_generaux_du', grille.frais_generaux);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentNiveau, grilleQuery.data, isEdit]);

  useEffect(() => {
    if (!fieldErrors) return;
    for (const [field, message] of Object.entries(fieldErrors)) {
      if (field in inscriptionFormSchema.shape) {
        setError(field as keyof InscriptionFormValues, { type: 'server', message });
      }
    }
  }, [fieldErrors, setError]);

  const ecolageMensuel = watch('ecolage_mensuel');
  const remisePct = watch('remise_pct');
  const ecolageEffectif = useMemo(() => {
    const base = Number(ecolageMensuel) || 0;
    const pct = Number(remisePct) || 0;
    if (pct <= 0) return base;
    return Math.round((base * (100 - pct)) / 100);
  }, [ecolageMensuel, remisePct]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <input type="hidden" {...register('eleve_id')} />

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Niveau" htmlFor="niveau_id" error={errors.niveau_id?.message} required>
          <Select id="niveau_id" {...register('niveau_id')} disabled={isEdit}>
            <option value={0}>— Choisir —</option>
            {niveauxQuery.data?.map((n) => (
              <option key={n.id} value={n.id}>{n.libelle}</option>
            ))}
          </Select>
        </FormField>

        <FormField
          label="Mois d'entrée"
          htmlFor="mois_entree_id"
          hint="Le dû est calculé à partir de ce mois jusqu'à juin."
          error={errors.mois_entree_id?.message}
          required
        >
          <Select id="mois_entree_id" {...register('mois_entree_id')}>
            <option value={0}>— Choisir —</option>
            {moisScolaires.map((m) => (
              <option key={m.id} value={m.id}>{m.libelle}</option>
            ))}
          </Select>
        </FormField>

        <FormField
          label="Écolage mensuel (avant remise)"
          htmlFor="ecolage_mensuel"
          hint="Suggéré depuis la grille tarifaire, ajustable."
          error={errors.ecolage_mensuel?.message}
          required
        >
          <Input id="ecolage_mensuel" type="number" min={0} step={1} {...register('ecolage_mensuel')} />
        </FormField>

        <FormField
          label="Remise fratrie (%)"
          htmlFor="remise_pct"
          hint="Recalculée automatiquement par le serveur selon la famille."
          error={errors.remise_pct?.message}
        >
          <Input id="remise_pct" type="number" min={0} max={100} step={1} {...register('remise_pct')} />
        </FormField>

        <FormField label="Droit d'inscription dû" htmlFor="droit_inscription_du" error={errors.droit_inscription_du?.message}>
          <Input id="droit_inscription_du" type="number" min={0} step={1} {...register('droit_inscription_du')} />
        </FormField>

        <FormField label="Frais généraux dus" htmlFor="frais_generaux_du" error={errors.frais_generaux_du?.message}>
          <Input id="frais_generaux_du" type="number" min={0} step={1} {...register('frais_generaux_du')} />
        </FormField>
      </div>

      <div className="rounded-md border bg-muted/40 p-3 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Écolage mensuel effectif</span>
          <MoneyCell value={ecolageEffectif} />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Annuler
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Enregistrement…' : isEdit ? 'Enregistrer' : "Créer l'inscription"}
        </Button>
      </div>
    </form>
  );
}