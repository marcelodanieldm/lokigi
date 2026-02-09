# Streaming de Datos y Skeleton Screens en Lokigi

## Backend (FastAPI)
- El endpoint `/audit` responde en <500ms con un `audit_id` y lanza el análisis en segundo plano usando `BackgroundTasks`.
- El resultado se cachea en Supabase para evitar repeticiones.
- El endpoint `/audit/result/{audit_id}` permite consultar el estado y resultado.

## Frontend (Next.js)
- Al iniciar la auditoría, se muestra un Skeleton Screen (pantalla de carga animada) mientras se procesan los datos.
- Se hace polling al backend para obtener resultados parciales y se actualiza la UI en tiempo real.
- El usuario nunca ve una pantalla en blanco ni espera sin feedback.

## Ejemplo de flujo visual
1. Usuario inicia auditoría → aparece Skeleton.
2. Backend responde con `audit_id` casi instantáneo.
3. Frontend consulta `/audit/result/{audit_id}` cada 0.5s.
4. Cuando hay resultado, se muestra el Dominance Index y el Competidor Amenaza.

## Código relevante
- Backend: `main.py` (endpoints `/audit` y `/audit/result/{audit_id}`)
- Frontend: `dashboard/premium/page.tsx` (hook de streaming y SkeletonAudit)

## Notas de eficiencia
- Pydantic valida los datos de entrada para máxima velocidad.
- El análisis de IA y Dominance se cachea en Supabase.
- El usuario percibe una app "en tiempo real" aunque el análisis sea costoso.

---

Para ampliar, se puede mostrar resultados parciales (por ejemplo, primero Dominance, luego IA) y animar la transición entre estados.
