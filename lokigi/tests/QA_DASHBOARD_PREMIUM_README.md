# QA Automation: Validador de Persistencia para Dashboard Premium

## Objetivo
Garantizar que los datos históricos del cliente no se pierdan y que las alertas lleguen a tiempo y en el idioma correcto.

## Pruebas Implementadas

### 1. Test de Persistencia
- Verifica que la gráfica de evolución mensual muestre correctamente los últimos 6 meses sin errores de renderizado ni datos nulos.
- Endpoint: `/api/dashboard/evolution?user_id=...`

### 2. Test de Permisos
- Asegura que un cliente de la versión gratuita ($0) o del servicio único ($99) NO pueda entrar al dashboard de suscripción.
- Solo usuarios premium acceden (HTTP 200), los demás reciben redirección (HTTP 302).

### 3. Simulación de Alerta Multilingüe
- Automatiza una prueba donde un cambio ficticio en la competencia dispara correctamente la notificación en el dashboard en los tres idiomas (ES, PT, EN).
- Endpoint: `/api/alerts/simulate` y `/dashboard/premium?user_id=...&lang=...`

## Ejecución

1. Backend Next.js y API deben estar corriendo en `localhost:3000`.
2. Instala dependencias:
   ```bash
   pip install pytest requests
   ```
3. Ejecuta las pruebas:
   ```bash
   pytest tests/test_dashboard_premium.py
   ```

---

**QA Automation by Lokigi**
