import { useState } from 'react';
import { Plus, Users } from 'lucide-react';
import { PageHeader } from '@/components/PageHeader';
import { MoneyCell } from '@/components/MoneyCell';
import { StatusBadge, type StatusKey } from '@/components/StatusBadge';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { DataTable } from '@/components/DataTable';
import { FormField } from '@/components/FormField';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { ColumnDef } from '@tanstack/react-table';

const STATUSES: StatusKey[] = [
  'PAYE', 'PARTIEL', 'IMPAYE', 'ECHU',
  'AVANCE', 'RETARD', 'ANNULE', 'A_COMPLETER',
];

interface Row { id: number; nom: string; montant: number; status: StatusKey; }

const ROWS: Row[] = [
  { id: 1, nom: 'Rakoto Naina',  montant: 100_000, status: 'PAYE' },
  { id: 2, nom: 'Rasoa Miora',   montant: 55_000,  status: 'PARTIEL' },
  { id: 3, nom: 'Randria Tiana', montant: 0,       status: 'IMPAYE' },
  { id: 4, nom: 'Rabe Hery',     montant: -45_000, status: 'ANNULE' },
  { id: 5, nom: 'Razafy Soa',    montant: 120_000, status: 'AVANCE' },
];

export function DevUiPage() {
  const [open, setOpen] = useState(false);
  const [loading] = useState(false);

  const columns: ColumnDef<Row, unknown>[] = [
    { accessorKey: 'nom', header: 'Nom' },
    {
      accessorKey: 'montant',
      header: 'Montant',
      meta: { align: 'right', sortable: true, sortField: 'montant' },
      cell: ({ row }) => <MoneyCell value={row.original.montant} />,
    },
    {
      accessorKey: 'status',
      header: 'Statut',
      cell: ({ row }) => <StatusBadge status={row.original.status} />,
    },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Design system — développement"
        subtitle="Catalogue des composants. Non exposé en production."
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Dev UI' }]}
        actions={<Button><Plus className="h-4 w-4" /> Nouveau</Button>}
      />

      <Card>
        <CardHeader><CardTitle>StatusBadge</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {STATUSES.map((s) => <StatusBadge key={s} status={s} />)}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>MoneyCell</CardTitle></CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2">
          <div>Positif : <MoneyCell value={1_500_000} /></div>
          <div>Négatif : <MoneyCell value={-75_000} /></div>
          <div>Zéro : <MoneyCell value={0} /></div>
          <div>Non défini : <MoneyCell value={null} /></div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>FormField (hint + erreur)</CardTitle></CardHeader>
        <CardContent className="max-w-md space-y-4">
          <FormField label="Nom" htmlFor="dev-nom" hint="Indiqué sur le bulletin.">
            <Input id="dev-nom" placeholder="Rakoto" />
          </FormField>
          <FormField
            label="Matricule" htmlFor="dev-matricule" required
            error="Ce matricule existe déjà."
          >
            <Input id="dev-matricule" defaultValue="SK-2026-0001" />
          </FormField>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>DataTable</CardTitle></CardHeader>
        <CardContent>
          <DataTable<Row>
            data={ROWS}
            columns={columns}
            total={ROWS.length}
            page={1}
            pageSize={20}
            onPageChange={() => undefined}
            ariaLabel="Tableau de démonstration"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>States</CardTitle></CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <EmptyState
            icon={<Users className="h-5 w-5" />}
            title="Aucun élève"
            message="Ajoutez un élève pour commencer."
          />
          <ErrorState
            message="Le serveur n'a pas répondu."
            onRetry={() => undefined}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>ConfirmDialog</CardTitle></CardHeader>
        <CardContent>
          <Button variant="destructive" onClick={() => setOpen(true)}>
            Ouvrir la boîte de confirmation
          </Button>
          <ConfirmDialog
            open={open}
            title="Annuler le paiement"
            description="Une écriture inverse sera créée. Le paiement d'origine reste immuable."
            confirmLabel="Annuler le paiement"
            loading={loading}
            onCancel={() => setOpen(false)}
            onConfirm={() => { setOpen(false); }}
          />
        </CardContent>
      </Card>
    </div>
  );
}