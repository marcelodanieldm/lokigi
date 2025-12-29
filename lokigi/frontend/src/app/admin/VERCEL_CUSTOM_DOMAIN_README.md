# Integración de Dominios Personalizados (Vercel API)

## Objetivo
Permitir que cada agencia vincule su propio dominio (CNAME) a su tenant en Lokigi (ej: reportes.miagencia.com).

## Flujo sugerido
1. El admin de la agencia ingresa su dominio personalizado en el panel.
2. El backend valida el dominio y lo registra en la tabla `agencies` (campo `custom_domain`).
3. Se realiza una llamada a la API de Vercel para asociar el dominio al proyecto.
4. El middleware de Next.js y FastAPI detecta el dominio y carga el branding/tenant correspondiente.

## Ejemplo de integración (Node.js)
```js
// POST /api/vercel/add-domain
import fetch from 'node-fetch';

export default async function handler(req, res) {
  const { domain, agencyId } = req.body;
  const vercelToken = process.env.VERCEL_TOKEN;
  const projectId = process.env.VERCEL_PROJECT_ID;
  const response = await fetch(`https://api.vercel.com/v9/projects/${projectId}/domains`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${vercelToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ name: domain })
  });
  const data = await response.json();
  // Actualiza agency.custom_domain en Supabase si éxito
  res.status(200).json(data);
}
```

## Notas
- El dominio debe tener un registro CNAME apuntando a tu proyecto Vercel.
- Usa variables de entorno para los tokens y project_id.
- El backend debe validar que el dominio no esté duplicado.
- El middleware ya soporta detección de dominio custom.
