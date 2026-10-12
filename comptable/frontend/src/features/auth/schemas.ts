import { z } from 'zod';

export const loginSchema = z.object({
  username: z.string().min(1, 'Identifiant requis').max(100),
  password: z.string().min(1, 'Mot de passe requis').max(200),
});

export type LoginForm = z.infer<typeof loginSchema>;