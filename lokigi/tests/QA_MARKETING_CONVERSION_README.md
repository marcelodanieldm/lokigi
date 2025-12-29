# QA Automation: Validador de Conversión para Marketing de Guerrilla

## Objetivo
Asegurar que los links funcionen, los mensajes sean correctos y el funnel de leads se registre.

## Pruebas Implementadas

### 1. Link Integrity
- Verifica que cada link generado lleve exactamente al reporte del negocio correcto.
- Endpoint: `/api/public-audit/{hash}`

### 2. Test de I18n
- Asegura que un negocio en Lisboa reciba el mensaje en Portugués y no en Español.
- Usa el algoritmo de lead scoring y generación de mensaje.

### 3. Funnel Tracking
- Valida que el sistema de analítica interna registre correctamente cuando un lead abre el link y cuánto tiempo se queda leyendo el reporte.
- Endpoints: `/api/track/open`, `/api/track/close`, `/api/track/analytics/{hash}`

## Ejecución

1. Backend Next.js y FastAPI deben estar corriendo en `localhost:3000` y `localhost:8000`.
2. Instala dependencias:
   ```bash
   pip install pytest requests
   ```
3. Ejecuta las pruebas:
   ```bash
   pytest tests/test_marketing_conversion.py
   ```

---

**QA Automation by Lokigi**
