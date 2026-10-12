import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Banknote, Plus, Trash2, Wand2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { PageHeader } from '@/components/PageHeader';
import { EmptyState } from '@/components/EmptyState';
import { MoneyCell } from '@/components/MoneyCell';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { formatAr } from '@/lib/format';
import { parseApiError } from '@/lib/errors';
import { useAuth } from '@/features/auth/useAuth';
import { referentielsApi } from '@/features/referentiels/api';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { salairesApi } from '../api';
import { PaiementSalaireForm } from '../components/PaiementSalaireForm';
import type {
  SalaireMensuelRead,
  PaiementSalaireRead,
  PaiementSalairePayload,
} from '../api';

export function SalairesPage() {
  const [sp, setSp] = useSearchParams();
  const { can } = useAuth();
  const qc = useQueryClient();

  const moisQuery = useQuery({
    queryKey: ['referentiels', 'mois-scolaires'],
    queryFn: () => referentielsApi.moisScolaires(),
    staleTime: 10 * 60_000,
  });

  const moisScolaires = useMemo(
    () => (moisQuery.data ?? []).filter((m) => m.est_scolaire),
    [moisQuery.data],
  );

  const moisId = useMemo(() => {
    const fromUrl = sp.get('mois_id');
    if (fromUrl && /^\d+$/.test(fromUrl)) return Number(fromUrl);
    return moisScolaires[0]?.id ?? 0;
  }, [sp, moisScolaires]);

  const salairesQuery = useQuery({
    queryKey: ['salaires-mensuels', moisId],
    queryFn: () => salairesApi.listSalairesMensuels(moisId),
    enabled: moisId > 0,
  });

  const paiementsQuery = useQuery({
    queryKey: ['paiements-salaires', moisId],
    queryFn: async () => {
      // Récupère tous les paiements pour les salaires du mois courant
      const salaires = salairesQuery.data ?? [];
      const all: PaiementSalaireRead[] = [];
      for (const s of salaires) {
        const page = await salairesApi.listPaiementsSalaires(s.id);
        all.push(...page.items);
      }
      return all;
    },
    enabled: (salairesQuery.data?.length ?? 0) > 0,
  });

  const [showGenerer, setShowGenerer] = useState(false);
  const [paiementPour, setPaiementPour] = useState<SalaireMensuelRead | null>(null);
  const [annulerId, setAnnulerId] = useState<number | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const genererMutation = useMutation({
    mutationFn: () => salairesApi.genererMensuel({ mois_id: moisId }),
    onSuccess: (report) => {
      toast.success(
        `Salaires : ${report.created} créés, ${report.skipped} déjà présents.`,
      );
      setShowGenerer(false);
      qc.invalidateQueries({ queryKey: ['salaires-mensuels', moisId] });
    },
    onError: (err) => {
      const parsed = parseApiError(err);
      toast.error(parsed.message);
    },
  });

  const paiementMutation = useMutation({
    mutationFn: (payload: PaiementSalairePayload) =>
      salairesApi.creerPaiementSalaire(payload),
    onSuccess: () => {
      toast.success('Paiement enregistré');
      setPaiementPour(null);
      setFieldErrors({});
      qc.invalidateQueries({ queryKey: ['paiements-salaires', moisId] });
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

  const onMoisChange = (id: number) => {
    const next = new URLSearchParams(sp);
    next.set('mois_id', String(id));
    setSp(next, { replace: true });
  };

  const setFieldErrorsByField = (map: Record<string, string>) => setFieldErrors(map);

  return (
    <div>
      <PageHeader
        title="Salaires"
        subtitle="Génération mensuelle et paiements 70 % / 30 %"
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Salaires' }]}
        actions={
          can('salaires_mensuels', 'create') && moisId > 0 && (
            <Button onClick={() => setShowGenerer(true)}>
              <Wand2 className="h-4 w-4" /> Générer pour le mois
            </Button>
          )
        }
      />

      <Card className="mb-4">
        <CardContent className="pt-6">
          <div className="grid max-w-sm gap-3">
            <div>
              <Label htmlFor="f-mois">Mois</Label>
              <Select
                id="f-mois"
                value={moisId}
                onChange={(e) => onMoisChange(Number(e.target.value))}
                disabled={moisScolaires.length === 0}
              >
                {moisScolaires.map((m) => (
                  <option key={m.id} value={m.id}>{m.libelle}</option>
                ))}
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Banknote className="h-4 w-4" />
            Salaires du mois
          </CardTitle>
        </CardHeader>
        <CardContent>
          {salairesQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Chargement…</p>
          ) : (salairesQuery.data?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<Banknote className="h-5 w-5" />}
              title="Aucun salaire pour ce mois"
              message="Cliquez sur « Générer pour le mois » pour créer les lignes à partir des employés actifs."
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employé</TableHead>
                    <TableHead className="text-right">Brut</TableHead>
                    <TableHead className="text-right">Avance 70 %</TableHead>
                    <TableHead className="text-right">Solde 30 %</TableHead>
                    <TableHead>Paiements</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {salairesQuery.data!.map((s) => {
                    const paiementsDuSalaire =
                      paiementsQuery.data?.filter(
                        (p) => p.salaire_mensuel_id === s.id,
                      ) ?? [];

                    const paye70 = paiementsDuSalaire
                      .filter((p) => p.type_part === 'AVANCE_70'
                        && p.parent_paiement_salaire_id === null)
                      .reduce((acc, p) => acc + p.montant, 0);
                    const paye30 = paiementsDuSalaire
                      .filter((p) => p.type_part === 'SOLDE_30'
                        && p.parent_paiement_salaire_id === null)
                      .reduce((acc, p) => acc + p.montant, 0);

                    const du70 = Math.round((s.montant_brut * 70) / 100);
                    const du30 = s.montant_brut - du70;

                    const complet70 = paye70 >= du70;
                    const complet30 = paye30 >= du30;

                    return (
                      <TableRow key={s.id}>
                        <TableCell className="font-medium">
                          Employé #{s.employe_id}
                        </TableCell>
                        <TableCell className="text-right">
                          <MoneyCell value={s.montant_brut} />
                        </TableCell>
                        <TableCell className="text-right">
                          <span className="tabular">
                            {formatAr(paye70)} / {formatAr(du70)}
                          </span>
                          {complet70 && (
                            <Badge variant="success" className="ml-2 text-[10px]">OK</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <span className="tabular">
                            {formatAr(paye30)} / {formatAr(du30)}
                          </span>
                          {complet30 && (
                            <Badge variant="success" className="ml-2 text-[10px]">OK</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <ul className="space-y-1 text-xs">
                            {paiementsDuSalaire.map((p) => {
                              const isAnnulation = p.parent_paiement_salaire_id !== null;
                              return (
                                <li key={p.id} className="flex items-center gap-2">
                                  <span className="tabular text-muted-foreground">
                                    {p.date_paiement ?? '—'}
                                  </span>
                                  <span className="tabular font-medium">
                                    {formatAr(p.montant)}
                                  </span>
                                  <Badge
                                    variant={isAnnulation ? 'secondary' : 'outline'}
                                    className="text-[10px]"
                                  >
                                    {p.type_part === 'AVANCE_70' ? '70%' : '30%'}
                                  </Badge>
                                  {isAnnulation && (
                                    <Badge variant="destructive" className="text-[10px]">
                                      Annulation
                                    </Badge>
                                  )}
                                  {!isAnnulation && can('paiements_salaires', 'annuler') && (
                                    <button
                                      type="button"
                                      onClick={() => setAnnulerId(p.id)}
                                      className="text-danger hover:underline"
                                      aria-label={`Annuler le paiement ${p.id}`}
                                    >
                                      <Trash2 className="h-3 w-3" />
                                    </button>
                                  )}
                                </li>
                              );
                            })}
                            {paiementsDuSalaire.length === 0 && (
                              <span className="text-muted-foreground">Aucun</span>
                            )}
                          </ul>
                        </TableCell>
                        <TableCell className="text-right">
                          {can('paiements_salaires', 'create') && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setFieldErrors({});
                                setPaiementPour(s);
                              }}
                              disabled={complet70 && complet30}
                            >
                              <Plus className="h-3 w-3" /> Payer
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialog générer */}
      <Dialog open={showGenerer} onOpenChange={setShowGenerer}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Générer les salaires du mois</DialogTitle>
            <p className="text-sm text-muted-foreground">
              Crée une ligne par employé actif. Idempotent : les lignes déjà
              présentes ne sont pas dupliquées.
            </p>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => setShowGenerer(false)}
              disabled={genererMutation.isPending}
            >
              Annuler
            </Button>
            <Button
              onClick={() => genererMutation.mutate()}
              disabled={genererMutation.isPending || moisId === 0}
            >
              {genererMutation.isPending ? 'Génération…' : 'Générer'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog paiement */}
      <Dialog
        open={paiementPour !== null}
        onOpenChange={(o) => { if (!o) { setPaiementPour(null); setFieldErrors({}); } }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Paiement salaire — employé #{paiementPour?.employe_id}
            </DialogTitle>
          </DialogHeader>
          {paiementPour && (
            <PaiementSalaireForm
              salaire={paiementPour}
              paiementsExistants={
                paiementsQuery.data?.filter(
                  (p) => p.salaire_mensuel_id === paiementPour.id,
                ) ?? []
              }
              submitting={paiementMutation.isPending}
              fieldErrors={fieldErrors}
              onSubmit={(payload) => {
                setFieldErrorsByField({});
                paiementMutation.mutate(payload);
              }}
              onCancel={() => { setPaiementPour(null); setFieldErrors({}); }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog annulation */}
      <ConfirmDialog
        open={annulerId !== null}
        title="Annuler le paiement salaire"
        description="Une écriture inverse sera créée. Le paiement d'origine reste immuable."
        confirmLabel="Annuler le paiement"
        onCancel={() => setAnnulerId(null)}
        onConfirm={async (motif) => {
          if (annulerId === null) return;
          try {
            await salairesApi.annulerPaiementSalaire(annulerId, motif);
            toast.success('Paiement annulé');
            setAnnulerId(null);
            qc.invalidateQueries({ queryKey: ['paiements-salaires', moisId] });
          } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Erreur');
          }
        }}
      />
    </div>
  );
}