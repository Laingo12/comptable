import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export function ForbiddenPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-6xl font-bold text-destructive">403</h1>
      <p className="text-muted-foreground">Accès refusé</p>
      <Button asChild><Link to="/">Retour à l'accueil</Link></Button>
    </div>
  );
}