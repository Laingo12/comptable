// Miroir client de backend/app/permissions/rbac.py.
//
// ⚠️ Le backend n'expose AUCUN champ `permissions` sur /auth/me (schéma UserRead).
// La matrice ci-dessous est donc LE seul mécanisme d'autorisation côté client.
// Elle doit être synchronisée manuellement avec backend/app/permissions/rbac.py.
//
// Correctif backend recommandé (hors périmètre étape 1) :
// ajouter un champ `permissions: string[]` (format "resource:action") dans
// MeResponse, puis remplacer `hasPermission()` par
// `permissions.includes(`${resource}:${action}`)`.

export type Role = 'ADMIN' | 'COMPTABLE' | 'SAISIE' | 'CAISSE_FG' | 'LECTURE';
export type Action = 'read' | 'create' | 'update' | 'delete' | 'annuler';
export type Resource =
  | 'users' | 'parametres' | 'referentiels' | 'annees'
  | 'familles' | 'eleves' | 'inscriptions' | 'employes' | 'salaires_mensuels'
  | 'paiements' | 'charges' | 'paiements_salaires' | 'associes' | 'prelevements'
  | 'caisse_fg' | 'audit_log' | 'dashboard' | 'rapports' | 'exports';

const ALL_ACTIONS: Action[] = ['read', 'create', 'update', 'delete', 'annuler'];
const ALL_RESOURCES: Resource[] = [
  'users', 'parametres', 'referentiels', 'annees', 'familles', 'eleves',
  'inscriptions', 'employes', 'salaires_mensuels', 'paiements', 'charges',
  'paiements_salaires', 'associes', 'prelevements', 'caisse_fg', 'audit_log',
  'dashboard', 'rapports', 'exports',
];

function key(r: Resource, a: Action): string { return `${r}:${a}`; }

const ADMIN = new Set<string>(ALL_RESOURCES.flatMap((r) => ALL_ACTIONS.map((a) => key(r, a))));

const COMPTABLE = new Set<string>(
  ALL_RESOURCES
    .filter((r) => r !== 'users' && r !== 'parametres')
    .flatMap((r) => ALL_ACTIONS.map((a) => key(r, a))),
);

const SAISIE = new Set<string>([
  key('eleves', 'read'), key('inscriptions', 'read'), key('referentiels', 'read'),
  key('paiements', 'create'), key('paiements', 'read'),
  key('charges', 'create'), key('charges', 'read'),
  key('caisse_fg', 'create'), key('caisse_fg', 'read'),
  key('dashboard', 'read'),
]);

const CAISSE_FG = new Set<string>([
  key('caisse_fg', 'read'), key('caisse_fg', 'create'), key('caisse_fg', 'annuler'),
]);

const LECTURE = new Set<string>(
  ALL_RESOURCES
    .filter((r) => r !== 'users' && r !== 'audit_log')
    .map((r) => key(r, 'read')),
);

const MATRIX: Record<Role, Set<string>> = {
  ADMIN, COMPTABLE, SAISIE, CAISSE_FG, LECTURE,
};

export function hasPermission(role: Role | undefined, resource: Resource, action: Action): boolean {
  if (!role) return false;
  return MATRIX[role].has(key(resource, action));
}