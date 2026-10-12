import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm shadow-md">
        <CardHeader>
          <CardTitle className="text-center text-primary">SMART KIDS</CardTitle>
          <p className="text-center text-sm text-muted-foreground">
            Gestion scolaire — Connexion
          </p>
        </CardHeader>
        <CardContent>
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