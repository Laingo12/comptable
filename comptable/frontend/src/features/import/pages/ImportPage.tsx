import { useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { AlertCircle, FileSpreadsheet, Upload } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/PageHeader';
import { EmptyState } from '@/components/EmptyState';
import { parseApiError } from '@/lib/errors';
import { useAuth } from '@/features/auth/useAuth';
import { ImportReport } from '../components/ImportReport';
import { importApi, type ImportReport as ImportReportType } from '../api';
import { ACCEPTED_EXTENSIONS, MAX_FILE_SIZE, validateFile } from '../schemas';

export function ImportPage() {
  const { can } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dryRun, setDryRun] = useState(true);
  const [report, setReport] = useState<ImportReportType | null>(null);

  const mutation = useMutation({
    mutationFn: ({ f, dry }: { f: File; dry: boolean }) =>
      importApi.importExcel({ file: f, dry_run: dry }),
    onSuccess: (r) => {
      setReport(r);
      const verb = r.dry_run ? 'Simulation terminée' : 'Import terminé';
      toast.success(
        `${verb} : ${r.total_created} créés, ${r.total_skipped} ignorés, ${r.total_errors} erreurs.`,
      );
    },
    onError: (err) => {
      const parsed = parseApiError(err);
      toast.error(parsed.message);
    },
  });

  const onPick = (f: File | null) => {
    if (!f) {
      setFile(null);
      return;
    }
    const error = validateFile(f);
    if (error) {
      toast.error(error);
      return;
    }
    setFile(f);
    setReport(null);
  };

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onPick(e.target.files?.[0] ?? null);
  };

  const onSubmit = () => {
    if (!file) {
      toast.error('Sélectionnez un fichier.');
      return;
    }
    mutation.mutate({ f: file, dry: dryRun });
  };

  const hasPermission = can('parametres', 'create');

  return (
    <div>
      <PageHeader
        title="Import Excel"
        subtitle="Migration initiale depuis le classeur de gestion scolaire"
        breadcrumb={[{ label: 'Accueil', to: '/' }, { label: 'Import Excel' }]}
      />

      {!hasPermission ? (
        <Card>
          <CardContent className="pt-6">
            <EmptyState
              icon={<AlertCircle className="h-5 w-5" />}
              title="Accès restreint"
              message="Seuls les administrateurs peuvent lancer un import."
            />
          </CardContent>
        </Card>
      ) : (
        <>
          <Card className="mb-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-4 w-4" /> Fichier source
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                onClick={() => fileInputRef.current?.click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  onPick(e.dataTransfer.files?.[0] ?? null);
                }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    fileInputRef.current?.click();
                  }
                }}
                className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed border-input bg-muted/30 px-4 py-8 text-center transition-colors hover:border-primary/60 hover:bg-muted/50"
              >
                <FileSpreadsheet className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm font-medium">
                  {file ? file.name : 'Cliquez ou déposez un fichier ici'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Formats acceptés : {ACCEPTED_EXTENSIONS.join(', ')} — max{' '}
                  {Math.round(MAX_FILE_SIZE / 1024 / 1024)} Mo
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_EXTENSIONS.join(',')}
                  onChange={onInputChange}
                  className="hidden"
                  aria-label="Fichier Excel à importer"
                />
              </div>

              {file && (
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border bg-card px-3 py-2 text-sm">
                  <span className="truncate">
                    <strong>{file.name}</strong>{' '}
                    <span className="text-muted-foreground">
                      ({(file.size / 1024).toFixed(0)} Ko)
                    </span>
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setFile(null);
                      setReport(null);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                  >
                    Retirer
                  </Button>
                </div>
              )}

              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={dryRun}
                    onChange={(e) => setDryRun(e.target.checked)}
                  />
                  <Label className="cursor-pointer">
                    Mode simulation (aucune écriture en base)
                  </Label>
                </label>
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={onSubmit}
                  disabled={!file || mutation.isPending}
                >
                  <Upload className="h-4 w-4" />
                  {mutation.isPending
                    ? 'Import en cours…'
                    : dryRun
                      ? 'Simuler l\'import'
                      : "Lancer l'import"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {report && <ImportReport report={report} />}

          {!report && (
            <Card>
              <CardHeader>
                <CardTitle>Feuilles reconnues</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="grid gap-2 text-sm sm:grid-cols-2">
                  {[
                    'SUIVI ECOLAGES',
                    'DROITS & FG',
                    'PERSONNEL',
                    'CHARGES FIXES & VARIABLES',
                    'RETRAITS JESSY',
                    'CAISSE FG',
                    'PARAMETRES',
                  ].map((s) => (
                    <li key={s} className="flex items-center gap-2">
                      <FileSpreadsheet className="h-3.5 w-3.5 text-muted-foreground" />
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
                <p className="mt-3 text-xs text-muted-foreground">
                  Chaque ligne est identifiée par un hash anti-doublon : relancer
                  le même import est sans effet (idempotent). Les lignes sans date
                  sont rattachées à « À compléter », celles hors année à « Hors année ».
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}