# Lokigi Public API: White-Label & Integraciones

## Ecosistema
- **Lokigi Directo:** Para dueños de negocio pequeño.
- **Lokigi Partners:** Para afiliados y freelancers.
- **Lokigi Enterprise:** Para agencias y corporativos (multi-tenancy, white-label, dominios custom).

## Integraciones soportadas
- Zapier, Make.com, HubSpot, CRMs y apps externas.
- Respuesta JSON ultra-ligera para webhooks y automatizaciones.

## Esquema de respuesta (Data Minification)
```json
{
  "lokigi_score": 87.2,
  "lost_revenue": 1200.0,
  "top_3_actions": ["Optimizar Google My Business", "Actualizar fotos", "Mejorar reseñas"],
  "meta": {
    "currency": "EUR",
    "lang": "es"
  }
}
```

## Rate Limiting Intelligence
- Tier 1: 60 req/min
- Tier 2: 300 req/min
- Enterprise: 2000 req/min
- El algoritmo ajusta límites dinámicamente según la API Key.

## Usage Analytics & Cache
- Se loguea el uso por API Key y se predicen picos para cachear resultados en Supabase.
- Reduce llamadas a APIs externas hasta un 70% en picos.

## Internacionalización
- Todos los endpoints incluyen metadatos de moneda e idioma.

## Ejemplo de uso
```bash
curl -H "x-api-key: t2-123456" "https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR"
```

## Extensión
- Soporta créditos de auditoría y webhooks para integración con apps externas.
- Preparado para facturación por uso y modelos B2B/B2B2C.
