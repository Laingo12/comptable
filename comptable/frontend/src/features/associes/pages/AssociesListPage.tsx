import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Plus, Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { PageHeader } from '@/components/PageHeader';
import { EmptyState } from '@/components/EmptyState';
import { FormField } from '@/components/FormField';
import { MoneyCell } from '@/components/MoneyCell';
import { parseApiError } from '@/lib/errors';
import { useAuth } from '@/features/auth/useAuth';
import { associesApi, type AssocieRead } from '../api';
import {
  associeFormSchema,
  toAssociePayload,
  type AssocieFormValues,
} from '../schemas';

export function AssociesListPage() {
  const { can } = useAuth();
  const qc = useQueryClient();
  const [editItem, setEditItem] = useState<AssocieRead | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const query = useQuery({
    queryKey: ['associes'],
    queryFn: associesApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (values: AssocieFormValues) =>
      associesApi.create(toAssociePayload(values)),
    onSuccess: () => {
      toast.success('Associé créé');
      setCreateOpen(false);
      setFieldErrors({});
      qc.invalidateQueries({ queryKey: ['associes'] });
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

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: AssocieFormValues }) =>
      associesApi.update(id, toAssociePayload(values)),
    onSuccess: () => {
      toast.success('Associé enregistré');
      setEditItem(null);
      setFieldErrors({});
      qc.invalidateQueries({ queryKey: ['associes'] });
    },
    onError: (err) => {
      const parsed = parseApiError(err);
      toast.error(parsed.message);
    },
  });

  return (
    <div>
      <PageHeader
        title="Associés"
        subtitle="Bénéficiaires de prélèvements (ex. Jessy)"
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Associés' }]}
        actions={
          can('associes', 'create') && (
            <Button onClick={() => { setFieldErrors({}); setCreateOpen(true); }}>
              <Plus className="h-4 w-4" /> Nouvel associé
            </Button>
          )
        }
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-4 w-4" /> Liste
          </CardTitle>
        </CardHeader>
        <CardContent>
          {query.isLoading ? (
            <p className="text-sm text-muted-foreground">Chargement…</p>
          ) : (query.data?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<Users className="h-5 w-5" />}
              title="Aucun associé"
              message="Créez un associé pour enregistrer les prélèvements."
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nom</TableHead>
                    <TableHead className="text-right">Plafond mensuel</TableHead>
                    <TableHead className="text-right">Versement fixe</TableHead>
                    <TableHead>Début (ordre mois)</TableHead>
                    <TableHead>Actif</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {query.data!.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="font-medium">{a.nom}</TableCell>
                      <TableCell className="text-right">
                        {a.plafond_mensuel !== null
                          ? <MoneyCell value={a.plafond_mensuel} />
                          : '—'}
                      </TableCell>
                      <TableCell className="text-right">
                        {a.versement_fixe_mensuel !== null
                          ? <MoneyCell value={a.versement_fixe_mensuel} />
                          : '—'}
                      </TableCell>
                      <TableCell>
                        {a.versement_fixe_mois_debut_ordre ?? '—'}
                      </TableCell>
                      <TableCell>
                        {a.is_active
                          ? <Badge variant="success" className="text-[10px]">actif</Badge>
                          : <Badge variant="secondary" className="text-[10px]">inactif</Badge>}
                      </TableCell>
                      <TableCell className="text-right">
                        {can('associes', 'update') && (
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => { setFieldErrors({}); setEditItem(a); }}
                          >
                            Éditer
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialog création */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nouvel associé</DialogTitle>
          </DialogHeader>
          <AssocieFormDialog
            submitting={createMutation.isPending}
            fieldErrors={fieldErrors}
            onSubmit={(values) => createMutation.mutate(values)}
            onCancel={() => setCreateOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Dialog édition */}
      <Dialog
        open={editItem !== null}
        onOpenChange={(o) => { if (!o) setEditItem(null); }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Modifier {editItem?.nom}</DialogTitle>
          </DialogHeader>
          {editItem && (
            <AssocieFormDialog
              initial={editItem}
              submitting={updateMutation.isPending}
              fieldErrors={fieldErrors}
              onSubmit={(values) =>
                updateMutation.mutate({ id: editItem.id, values })
              }
              onCancel={() => setEditItem(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// --- Form interne --------------------------------------------------------

interface AssocieFormDialogProps {
  initial?: AssocieRead | null;
  submitting?: boolean;
  fieldErrors?: Record<string, string>;
  onSubmit: (values: AssocieFormValues) => void | Promise<void>;
  onCancel: () => void;
}

function AssocieFormDialog({
  initial = null, submitting, fieldErrors, onSubmit, onCancel,
}: AssocieFormDialogProps) {
  const {
    register, handleSubmit, formState: { errors },
  } = useForm<AssocieFormValues>({
    resolver: zodResolver(associeFormSchema),
    defaultValues: {
      nom: initial?.nom ?? '',
      plafond_mensuel: initial?.plafond_mensuel ?? 0,
      versement_fixe_mensuel: initial?.versement_fixe_mensuel ?? 0,
      versement_fixe_mois_debut_ordre:
        initial?.versement_fixe_mois_debut_ordre ?? 0,
      is_active: initial?.is_active ?? true,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <FormField label="Nom" htmlFor="nom" error={errors.nom?.message} required>
        <Input id="nom" autoComplete="off" autoFocus {...register('nom')} />
      </FormField>

      <div className="grid gap-4 sm:grid-cols-2">
        <FormField
          label="Plafond mensuel (Ar)"
          htmlFor="plafond_mensuel"
          hint="0 = pas de plafond."
          error={errors.plafond_mensuel?.message}
        >
          <Input
            id="plafond_mensuel"
            type="number"
            min={0}
            step={1}
            {...register('plafond_mensuel')}
          />
        </FormField>

        <FormField
          label="Versement fixe mensuel (Ar)"
          htmlFor="versement_fixe_mensuel"
          hint="0 = pas de versement fixe."
          error={errors.versement_fixe_mensuel?.message}
        >
          <Input
            id="versement_fixe_mensuel"
            type="number"
            min={0}
            step={1}
            {...register('versement_fixe_mensuel')}
          />
        </FormField>

        <FormField
          label="Début du versement fixe (ordre mois)"
          htmlFor="versement_fixe_mois_debut_ordre"
          hint="1 = septembre, 2 = octobre, etc."
          error={errors.versement_fixe_mois_debut_ordre?.message}
        >
          <Input
            id="versement_fixe_mois_debut_ordre"
            type="number"
            min={0}
            max={99}
            step={1}
            {...register('versement_fixe_mois_debut_ordre')}
          />
        </FormField>

        <FormField label="Actif" htmlFor="is_active" error={errors.is_active?.message}>
          <label className="flex h-9 items-center gap-2 text-sm">
            <input id="is_active" type="checkbox" {...register('is_active')} />
            Associé actif
          </label>
        </FormField>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
          Annuler
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Enregistrement…' : initial ? 'Enregistrer' : 'Créer'}
        </Button>
      </div>
    </form>
  );
}