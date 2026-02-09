// WORKER_TERMINAL_README.md

# The Worker's Terminal (Dashboard de Operaciones)

**Ubicación:** frontend/src/app/components/WorkerTerminal.tsx

## Objetivo
Interfaz minimalista y ultra eficiente para el operador de Lokigi. Permite revisar reseñas y propuestas de IA, y actuar con un solo clic.

## Características
- **Minimalismo Extremo:**
  - Lista vertical de tareas.
  - Izquierda: Reseña del cliente (monoespaciada).
  - Derecha: Propuesta de IA (monoespaciada).
- **Acciones de un Clic:**
  - 'Aprobar y Publicar'
  - 'Regenerar con tono más formal'
  - 'Regenerar con tono más amigable'
  - Botones grandes, accesibles y con feedback visual inmediato.
- **Estética:**
  - Dark Mode puro.
  - Acentos verde neón (#39FF14).
  - Fuente monoespaciada (ej: Fira Mono, Menlo, Consolas).
- **Performance:**
  - Sin imágenes pesadas.
  - Micro-interacciones CSS rápidas (hover, active, focus).


## Ejemplo de Uso
```tsx
<WorkerTerminal
  tasks={tasks}
  onApprove={handleApprove}
  onRegenerate={handleRegenerate}
/>
```

## Integración Full Stack
- El frontend llama a `/api/worker/generate-replies` (proxy seguro a backend FastAPI) para regenerar propuestas con Gemini.
- Al aprobar, la tarea desaparece con animación Optimistic UI y se llama `/api/worker/approve`.
- Solo usuarios WORKER/ADMIN pueden acceder al endpoint real.

Ver detalles de backend en `backend/review_response_engine.py` y de la integración en `frontend/src/app/dashboard/worker/page.tsx`.

## Props
- `tasks`: Array de tareas ({ id, review, aiProposal })
- `onApprove(id)`: Acción al aprobar
- `onRegenerate(id, tone)`: Acción al regenerar ('formal' | 'friendly')

---

**Autor:** UX/UI Designer, Lokigi
**Fecha:** 2025-12-29
