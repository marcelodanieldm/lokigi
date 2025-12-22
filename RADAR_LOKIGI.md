# 🎯 Radar Lokigi - Sistema de Monitoreo de Competencia ($29/mes)

## 📋 Descripción

**Radar Lokigi** es el producto de suscripción mensual que convierte leads en clientes recurrentes. El sistema monitorea automáticamente a los competidores y genera alertas cuando hay movimientos significativos en el mercado local.

## 💰 Modelo de Negocio

- **Precio**: $29/mes (MRR - Monthly Recurring Revenue)
- **Trial**: 30 días gratis
- **Target**: Negocios locales que ya compraron la auditoría ($99)
- **Valor**: Vigilancia continua + Alertas automáticas + Heatmap mensual

## ✨ Características Principales

### 1. 🔍 Monitoreo Automático de Competidores

- **Re-scraping mensual** de hasta 5 competidores
- Tracking de métricas clave:
  - Rating de Google Maps
  - Número de reseñas
  - Fotos publicadas
  - Score de visibilidad (0-100)
- **Zero-cost scraping**: Uso eficiente de recursos gratuitos

### 2. 📢 Sistema de Alertas Inteligentes

Las alertas se disparan automáticamente cuando:
- ✅ Competidor sube **+5 puntos** en score de visibilidad
- ✅ Competidor recibe **+10 nuevas reseñas**
- ✅ Competidor sube **+0.3** en rating
- ✅ Competidor agrega **+5 fotos nuevas**

Canales de alerta:
- 📧 Email
- 📱 WhatsApp (próximamente)

### 3. 🗺️ Heatmap Dinámico de Visibilidad

- **Actualización mensual** del área de influencia
- Métricas calculadas:
  - Radio de influencia (metros)
  - Densidad de competidores (competidores/km²)
  - Score de dominancia del área (0-100%)
  - Crecimiento/reducción de área vs mes anterior
- Visualización interactiva en dashboard

### 4. 🤖 Automatización Completa

- **Cron job diario**: Revisa todas las suscripciones
- **Procesamiento nocturno**: 2 AM (bajo consumo de servidor)
- **Zero-intervention**: Sistema 100% automático

## 🏗️ Arquitectura Técnica

### Modelos de Base de Datos

```python
RadarSubscription
├── lead_id (FK a Lead)
├── status (active/trial/cancelled)
├── stripe_subscription_id
├── monthly_price ($29)
├── competitors_to_track (array de IDs)
├── monitoring_frequency_days (30)
├── alerts_enabled
└── total_alerts_sent

CompetitorSnapshot
├── competitor_id (FK a Lead)
├── subscription_id (FK a RadarSubscription)
├── rating, reviews_count, photos_count
├── visibility_score (calculado)
├── rating_change, reviews_change, score_change
├── alert_triggered
└── alert_reasons (JSON)

VisibilityHeatmap
├── lead_id
├── center_coordinates [lat, lng]
├── radius_meters
├── competitors_in_area (JSON)
├── area_dominance_score
└── area_growth_percent
```

### Servicios

**CompetitorMonitoringService**
- `monitor_subscription_competitors()`: Escanea competidores
- `create_competitor_snapshot()`: Crea snapshot + detecta cambios
- `generate_alert_for_snapshot()`: Genera alertas automáticas
- `update_visibility_heatmap()`: Actualiza mapa de calor

**RadarService** (existente)
- Lógica de scraping y análisis de competidores

### API Endpoints

```
POST   /api/radar/subscribe              # Crear suscripción
GET    /api/radar/subscription/{lead_id} # Ver suscripción
POST   /api/radar/subscription/{id}/cancel
POST   /api/radar/monitor/{id}           # Monitoreo manual (superuser)
GET    /api/radar/alerts/{lead_id}       # Obtener alertas
POST   /api/radar/alerts/{id}/read       # Marcar alerta como leída
GET    /api/radar/snapshots/{sub_id}     # Ver snapshots de competidores
GET    /api/radar/heatmap/{lead_id}/latest
GET    /api/radar/heatmap/{lead_id}/history
POST   /api/radar/cron/monitor-all       # Endpoint para cron job
```

## 🚀 Setup e Instalación

### 1. Migrar Base de Datos

```bash
python recreate_db.py
# Acepta 's' para recrear con nuevas tablas
```

### 2. Iniciar Servidor

```bash
python main.py
# FastAPI corriendo en http://localhost:8000
```

### 3. Configurar Cron Job

**Linux/Mac (crontab):**
```bash
crontab -e
# Agregar:
0 2 * * * /usr/bin/python3 /path/to/lokigi/radar_cron_job.py >> /path/to/logs/radar.log 2>&1
```

**Windows (Task Scheduler):**
1. Abrir Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `C:\path\to\lokigi\radar_cron_job.py`

### 4. Variables de Entorno

```bash
# .env
STRIPE_SECRET_KEY=sk_test_...
OPENAI_API_KEY=sk-...
```

## 📊 Ejemplo de Uso

### Crear Suscripción

```bash
curl -X POST "http://localhost:8000/api/radar/subscribe" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 123,
    "competitor_ids": [124, 125, 126],
    "alert_email": "cliente@example.com"
  }'
```

### Ver Alertas

```bash
curl "http://localhost:8000/api/radar/alerts/123?unread_only=true"
```

### Obtener Heatmap

```bash
curl "http://localhost:8000/api/radar/heatmap/123/latest"
```

## 📈 Métricas Clave

El dashboard de superuser muestra:
- **MRR (Monthly Recurring Revenue)**: Total de ingresos recurrentes
- **Churn Rate**: % de cancelaciones
- **Active Subscriptions**: Suscripciones activas
- **Trial Subscriptions**: En período de prueba
- **Alerts Sent**: Total de alertas generadas

## 🎯 Roadmap

### Fase 1 (Actual)
- ✅ Sistema de suscripciones
- ✅ Monitoreo automático mensual
- ✅ Alertas por email
- ✅ Heatmap básico

### Fase 2 (Próximo)
- 🔲 Integración con Stripe Subscriptions
- 🔲 Alertas por WhatsApp (Twilio)
- 🔲 Dashboard interactivo de heatmap
- 🔲 Notificaciones push

### Fase 3 (Futuro)
- 🔲 Machine Learning para predicción de tendencias
- 🔲 Recomendaciones automáticas de acciones
- 🔲 Monitoreo de redes sociales
- 🔲 API pública para integraciones

## 💡 Estrategia de Conversión

### Del Lead al Cliente Recurrente

1. **Lead entra** → Formulario + $9 e-book
2. **Auditoría gratis** → Detecta 3 competidores fuertes
3. **Compra servicio** → $99 servicio completo
4. **Upsell Radar** → "¿Quieres vigilar a tu competencia? 30 días gratis"
5. **Trial de 30 días** → Recibe 2-3 alertas en el mes
6. **Conversión a pago** → $29/mes recurrente

### Mensaje de Venta

> "¿Y si tu competidor de la esquina acaba de recibir 20 reseñas nuevas y tú ni te enteraste? Con **Radar Lokigi** vigilamos a tu competencia 24/7 y te avisamos cuando se mueven. **30 días gratis**, después solo $29/mes."

## 🔐 Seguridad

- ✅ Autenticación JWT requerida para endpoints sensibles
- ✅ Rate limiting en endpoints de monitoreo
- ✅ Validación de API key en cron job
- ✅ Datos encriptados en tránsito (HTTPS)

## 📞 Soporte

Para cualquier duda:
- 📧 Email: support@lokigi.com
- 📚 Docs: https://docs.lokigi.com/radar

---

**Construido con ❤️ por el equipo de Lokigi**
