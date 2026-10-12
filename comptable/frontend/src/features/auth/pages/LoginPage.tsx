import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { FormField } from '@/components/FormField';
import { useAuth } from '../useAuth';
import { loginSchema, type LoginForm } from '../schemas';
import { toastApiError } from '@/lib/errors';

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [submitting, setSubmitting] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  });

  if (isAuthenticated) return <Navigate to="/" replace />;

  const onSubmit = handleSubmit(async (values) => {
    setSubmitting(true);
    try {
      await login(values);
      toast.success('Connexion réussie');
      const from = (location.state as { from?: string } | null)?.from ?? '/';
      navigate(from, { replace: true });
    } catch (err) {
      toastApiError(err);
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <div
      className="flex min-h-screen items-center justify-center p-4"
      style={{
        background:
          'linear-gradient(180deg, hsl(var(--primary-soft)) 0%, hsl(var(--background)) 55%)',
      }}
    >
      <Card className="w-full max-w-sm border-none shadow-lg">
        <CardContent className="pt-8 pb-8">
          {/* Logo centré, ~200 px de large, marges ≥ 0,5× la hauteur du logo */}
          <div className="mb-8 flex justify-center">
            <img
              src="/brand/logo.png"
              alt="SMART KIDS"
              className="h-auto w-[200px] max-w-full object-contain"
            />
          </div>
          <p className="mb-6 text-center text-sm text-muted-foreground">
            Gestion scolaire — Connexion
          </p>
          <form onSubmit={onSubmit} className="space-y-4" noValidate>
            <FormField label="Identifiant" htmlFor="username" error={errors.username?.message} required>
              <Input id="username" autoComplete="username" autoFocus {...register('username')} />
            </FormField>
            <FormField label="Mot de passe" htmlFor="password" error={errors.password?.message} required>
              <Input id="password" type="password" autoComplete="current-password" {...register('password')} />
            </FormField>
            <Button type="submit" disabled={submitting} className="w-full">
              {submitting ? 'Connexion…' : 'Se connecter'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}