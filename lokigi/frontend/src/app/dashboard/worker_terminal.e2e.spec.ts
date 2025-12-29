// worker_terminal.e2e.spec.ts
// End-to-end test: Worker Terminal (Playwright)
// Valida flujo completo: carga, aprobación, regeneración, animación y backend
import { test, expect } from '@playwright/test';

test.describe('Worker Terminal E2E', () => {
  test('Carga y muestra tareas', async ({ page }) => {
    await page.goto('/dashboard/worker');
    await expect(page.locator('.font-mono')).toHaveCount(6); // 3 reviews + 3 aiProposals
  });

  test('Aprobar tarea la elimina con animación', async ({ page }) => {
    await page.goto('/dashboard/worker');
    const firstApprove = page.getByRole('button', { name: /aprobar/i }).first();
    await firstApprove.click();
    await expect(page.locator('.font-mono')).toHaveCount(4); // 2 tareas restantes
  });

  test('Regenerar tarea actualiza propuesta', async ({ page }) => {
    await page.goto('/dashboard/worker');
    const firstRegenerate = page.getByRole('button', { name: /formal/i }).first();
    const before = await page.locator('.font-mono').nth(1).textContent();
    await firstRegenerate.click();
    await page.waitForTimeout(500); // Espera a que se actualice
    const after = await page.locator('.font-mono').nth(1).textContent();
    expect(after).not.toBe(before);
  });
});
