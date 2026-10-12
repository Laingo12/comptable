// Access token gardé en mémoire uniquement (jamais localStorage).
// Refresh token : voir apiClient.ts (sessionStorage + cookie httpOnly si dispo).
let accessToken: string | null = null;
const listeners = new Set<(t: string | null) => void>();

export function setAccessToken(token: string | null): void {
  accessToken = token;
  for (const l of listeners) l(token);
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function onAccessTokenChange(cb: (t: string | null) => void): () => void {
  listeners.add(cb);
  return () => { listeners.delete(cb); };
}

// Refresh token : sessionStorage (durée de l'onglet, non persistant).
// ATTENTION : la sessionStorage est exposée au JS de la page (XSS). C'est un
// compromis documenté tant que le backend n'émet pas le refresh en cookie
// httpOnly. Voir "Limitations" dans le README.
const RT_KEY = 'smartkids.refresh_token';

export function setRefreshToken(token: string | null): void {
  if (token) sessionStorage.setItem(RT_KEY, token);
  else sessionStorage.removeItem(RT_KEY);
}

export function getRefreshToken(): string | null {
  return sessionStorage.getItem(RT_KEY);
}