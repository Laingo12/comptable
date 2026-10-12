import { execSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';

const url = process.env.OPENAPI_URL ?? 'http://localhost:8000/openapi.json';
mkdirSync('src/types', { recursive: true });
console.log(`[gen:api] génération depuis ${url}`);
execSync(`npx openapi-typescript ${url} -o src/types/api.d.ts`, { stdio: 'inherit' });
console.log('[gen:api] OK — src/types/api.d.ts');