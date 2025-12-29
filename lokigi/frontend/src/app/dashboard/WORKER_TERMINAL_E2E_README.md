# WORKER_TERMINAL_E2E_README.md

# End-to-End Testing: Worker Terminal

**Ubicación:** frontend/src/app/dashboard/worker_terminal.e2e.spec.ts

## Objetivo
Validar el flujo completo de la vista Worker Terminal:
- Carga de tareas
- Aprobación (Optimistic UI)
- Regeneración de propuesta (llamada backend)
- Animaciones y feedback visual

## Herramientas
- [Playwright](https://playwright.dev/) (E2E testing)

## Ejecución
1. Instala Playwright:
   ```bash
   npm install -D @playwright/test
   npx playwright install
   ```
2. Corre el test:
   ```bash
   npx playwright test frontend/src/app/dashboard/worker_terminal.e2e.spec.ts
   ```

## Cobertura
- Verifica que se muestran las tareas iniciales.
- Al aprobar, la tarea desaparece con animación.
- Al regenerar, la propuesta de IA cambia.

---

**Autor:** QA Automation, Lokigi
**Fecha:** 2025-12-29
