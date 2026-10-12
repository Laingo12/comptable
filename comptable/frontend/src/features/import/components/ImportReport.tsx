import { AlertTriangle, CheckCircle2, FileSpreadsheet, Info, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { ImportReport as ImportReportType, SheetStat } from '../api';

interface Props {
  report: ImportReportType;
}

function SheetCard({ stat }: { stat: SheetStat }) {
  const hasErrors = stat.errors > 0;
  const isEmpty = stat.total === 0;
  const badgeVariant = hasErrors ? 'destructive' : isEmpty ? 'secondary' : 'success';

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <FileSpreadsheet className="h-4 w-4" />
          <span className="flex-1 truncate">{stat.sheet}</span>
          <Badge variant={badgeVariant} className="text-[10px]">
            {stat.created} créé{stat.created > 1 ? 's' : ''}
            {stat.skipped > 0 && ` · ${stat.skipped} ignoré${stat.skipped > 1 ? 's' : ''}`}
            {stat.errors > 0 && ` · ${stat.errors} erreur${stat.errors > 1 ? 's' : ''}`}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
          <div>
            <p className="text-muted-foreground">Lignes</p>
            <p className="tabular font-medium">{stat.total}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Créées</p>
            <p className="tabular font-medium text-success">{stat.created}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Ignorées (doublon)</p>
            <p className="tabular font-medium text-muted-foreground">{stat.skipped}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Erreurs</p>
            <p className="tabular font-medium text-danger">{stat.errors}</p>
          </div>
        </div>

        {stat.warnings.length > 0 && (
          <details className="mt-3 text-xs">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
              {stat.warnings.length} avertissement{stat.warnings.length > 1 ? 's' : ''}
            </summary>
            <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto pl-4 text-muted-foreground">
              {stat.warnings.map((w, i) => (
                <li key={i} className="list-disc">{w}</li>
              ))}
            </ul>
          </details>
        )}
      </CardContent>
    </Card>
  );
}

export function ImportReport({ report }: Props) {
  const totalOk = report.total_errors === 0;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {totalOk
              ? <CheckCircle2 className="h-4 w-4 text-success" />
              : <AlertTriangle className="h-4 w-4 text-warning" />}
            Rapport d'import — {report.file_name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Mode</p>
              <p className="text-sm font-medium">
                {report.dry_run
                  ? <Badge variant="warning" className="text-[10px]">Simulation</Badge>
                  : <Badge variant="success" className="text-[10px]">Écriture</Badge>}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Créés</p>
              <p className="tabular text-sm font-medium text-success">{report.total_created}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Ignorés</p>
              <p className="tabular text-sm font-medium text-muted-foreground">{report.total_skipped}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Erreurs</p>
              <p className="tabular text-sm font-medium text-danger">{report.total_errors}</p>
            </div>
          </div>

          {report.dry_run && (
            <div className="mt-4 flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-xs text-warning">
              <Info className="h-4 w-4 shrink-0" />
              <p>
                Simulation : aucune donnée n'a été écrite en base.
                Décochez « Simulation » et relancez pour appliquer l'import.
              </p>
            </div>
          )}

          {report.total_errors > 0 && (
            <div className="mt-4 flex items-start gap-2 rounded-md border border-danger/40 bg-danger/10 p-3 text-xs text-danger">
              <XCircle className="h-4 w-4 shrink-0" />
              <p>
                Certaines lignes n'ont pas pu être importées. Consultez le détail
                par feuille ci-dessous pour connaître les causes exactes.
              </p>
            </div>
          )}

          <p className="mt-4 text-xs text-muted-foreground">
            Démarré {report.started_at} — terminé {report.finished_at}.
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-3 md:grid-cols-2">
        {report.sheets.map((s) => <SheetCard key={s.sheet} stat={s} />)}
      </div>
    </div>
  );
}