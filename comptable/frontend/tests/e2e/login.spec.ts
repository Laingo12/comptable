import { expect, test } from '@playwright/test';

const ADMIN_USER = process.env.E2E_ADMIN_USER;
const ADMIN_PASS = process.env.E2E_ADMIN_PASSWORD;

test.skip(
  !ADMIN_USER || !ADMIN_PASS,
  'E2E_ADMIN_USER et E2E_ADMIN_PASSWORD doivent être définis dans l’environnement ' +
  '(voir README, section « Tests end-to-end »).',
);

test('parcours : login → dashboard → logout', async ({ page }) => {
  if (!ADMIN_USER || !ADMIN_PASS) return;
  await page.goto('/login');
  await page.getByLabel('Identifiant').fill(ADMIN_USER);
  await page.getByLabel('Mot de passe').fill(ADMIN_PASS);
  await page.getByRole('button', { name: /se connecter/i }).click();

  await expect(page.getByRole('heading', { name: /tableau de bord/i })).toBeVisible();

  await page.getByRole('button', { name: new RegExp(ADMIN_USER, 'i') }).click();
  await page.getByRole('menuitem', { name: /déconnexion/i }).click();

  await expect(page).toHaveURL(/\/login$/);
});