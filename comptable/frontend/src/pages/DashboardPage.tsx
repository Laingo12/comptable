import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/features/auth/useAuth';

export function DashboardPage() {
  const { user } = useAuth();
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Tableau de bord</h1>
      <Card>
        <CardHeader><CardTitle>Bienvenue</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Connecté en tant que <strong>{user?.full_name}</strong> ({user?.role}).
          Les indicateurs seront ajoutés à l'étape 3.
        </CardContent>
      </Card>
    </div>
  );
}