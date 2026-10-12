import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { FormField } from '@/components/FormField';

const schema = z.object({
  motif: z
    .string()
    .trim()
    .min(3, 'Motif requis (3 caractères minimum)')
    .max(500, 'Motif trop long (500 caractères max)'),
});

export type ConfirmMotif = z.infer<typeof schema>;

interface Props {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  requireMotif?: boolean;
  onCancel: () => void;
  onConfirm: (motif: string) => void | Promise<void>;
}

export function ConfirmDialog({
  open, title, description,
  confirmLabel = 'Confirmer', cancelLabel = 'Annuler',
  loading = false, requireMotif = true,
  onCancel, onConfirm,
}: Props) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ConfirmMotif>({
    resolver: zodResolver(schema),
    defaultValues: { motif: '' },
  });

  useEffect(() => {
    if (open) reset({ motif: '' });
  }, [open, reset]);

  const submit = handleSubmit(async ({ motif }) => {
    await onConfirm(motif);
  });

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o && !loading) onCancel(); }}>
      <DialogContent role="alertdialog" aria-modal="true">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4" noValidate>
          {requireMotif && (
            <FormField
              label="Motif"
              htmlFor="confirm-motif"
              hint="Obligatoire, il apparaîtra dans le journal d'audit."
              error={errors.motif?.message}
            >
              <Input id="confirm-motif" autoFocus autoComplete="off" {...register('motif')} />
            </FormField>
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
              {cancelLabel}
            </Button>
            <Button type="submit" variant="destructive" disabled={loading}>
              {loading ? 'En cours…' : confirmLabel}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}