# QA Automation: Validador de Flujos de Tiempo

## Objetivo
Garantizar que los mensajes de seguimiento se envíen en el momento correcto y que no se envíen descuentos a usuarios que ya pagaron. Incluye pruebas de stress para el Exit Intent Popup.

## Pruebas Incluidas

### 1. Time-Travel Testing
- Simula el paso del tiempo para verificar que los impactos T+1h (PDF) y T+24h (cupón) se disparen correctamente.
- Usa un fake Supabase client y monkeypatch para simular el entorno y el envío de mensajes.

### 2. Negative Testing
- Si un usuario compra a la hora 2, el cupón de la hora 24 debe ser cancelado y no enviado.
- Simula la cancelación por webhook de Stripe.

### 3. Stress Test de Modales (Playwright + Lighthouse)
- Valida que el Exit Intent Popup solo aparezca una vez por sesión.
- Prueba en resoluciones móviles (iPhone, Android).
- Corre Lighthouse y asegura score > 95 (no degrada la performance ni UX).

## Ejecución

### Pytest (backend)
```bash
pytest tests/test_retargeting_timeflows.py
```

### Playwright (frontend)
```bash
npx playwright test frontend/src/app/components/ExitIntentUX.spec.ts
# (Crear test E2E para el modal y Lighthouse)
```

## Notas
- El fake Supabase client permite simular la cola y el procesamiento de mensajes sin afectar producción.
- Los tests pueden extenderse para otros flujos de retargeting y modales.

---
Última actualización: 2025-12-29
