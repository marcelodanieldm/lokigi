# 📊 Business Intelligence Dashboard - Admin Analytics

## Overview
Panel de análisis avanzado para administradores y analistas de datos con KPIs estratégicos del negocio Lokigi.

---

## 🎯 Métricas Implementadas

### 1. **Métricas de Conversión**
Analiza el embudo de ventas completo desde lead hasta conversión.

**KPIs Principales:**
- **Total Leads**: Usuarios que ingresaron a Lokigi
- **Diagnósticos Entregados**: Leads que recibieron análisis gratuito
- **Conversión Global**: % de diagnósticos que resultan en compra

**Tasas de Conversión por Producto:**
- **E-book ($9)**: % diagnóstico → compra e-book
- **Servicio ($99)**: % diagnóstico → contratación servicio
- **Suscripción ($29/mes)**: % diagnóstico → suscripción premium

**Visualización:**
- Gráfico de barras: Compras por producto
- Progress bars: Tasas de conversión individuales

**Decisiones que soporta:**
- ¿Qué producto tiene mejor conversión?
- ¿Es efectivo el diagnóstico gratuito como lead magnet?
- ¿Cuántos leads se necesitan para X ventas?

---

### 2. **Desempeño por Región (ROI)**
Identifica qué países generan mejor retorno de inversión.

**Métricas por País:**
- **Leads**: Total de usuarios por país (detectado por IP)
- **Órdenes**: Compras realizadas
- **Revenue**: Ingresos generados
- **Conversión**: % de leads que compran
- **AOV** (Average Order Value): Ticket promedio
- **ROI Score**: Métrica combinada (revenue/leads * conversion_rate)

**Países tracked:**
- 🇧🇷 Brasil
- 🇦🇷 Argentina  
- 🇲🇽 México
- 🇺🇸 Estados Unidos
- 🇨🇴 Colombia
- 🇨🇱 Chile
- 🇵🇪 Perú
- 🇪🇸 España

**Visualización:**
- Tabla ordenada por ROI Score (mejor primero)
- Badge "TOP" para el país con mejor performance

**Decisiones que soporta:**
- ¿En qué país invertir en marketing?
- ¿Qué región tiene usuarios más valiosos?
- ¿Necesitamos adaptar precios por región?

---

### 3. **Lifetime Value (LTV) - Suscripciones**
Analiza la retención y valor de los suscriptores de $29/mes.

**KPIs Principales:**
- **Suscripciones Activas**: Usuarios pagando actualmente
- **Suscripciones Canceladas**: Usuarios que cancelaron
- **Duración Promedio**: Cuántos meses permanecen suscritos
- **LTV Estimado**: Valor total por suscriptor ($29 × meses promedio)
- **Tasa de Churn**: % de cancelaciones

**Visualización:**
- Pie chart: Distribución activas vs canceladas
- Progress bar: Tasa de churn con código de colores:
  - 🟢 Verde: <10% (excelente)
  - 🟡 Amarillo: 10-20% (moderado)
  - 🔴 Rojo: >20% (alerta)
- Insight automático según churn rate

**Decisiones que soporta:**
- ¿Es rentable el modelo de suscripción?
- ¿Cuándo recuperamos la inversión en adquisición?
- ¿Necesitamos programas de retención?

**Cálculo LTV:**
```
LTV = $29/mes × Duración Promedio (meses)

Ejemplo:
- Duración promedio: 4.5 meses
- LTV = $29 × 4.5 = $130.50 por suscriptor
```

---

### 4. **Eficiencia Operativa**
Mide la velocidad y efectividad del equipo Worker en órdenes de $99.

**KPIs Principales:**
- **Total Órdenes de Servicio**: Pedidos de $99
- **Tiempo Promedio de Completitud**: Horas para finalizar orden
- **Más Rápida**: Mejor tiempo registrado
- **Más Lenta**: Peor tiempo registrado
- **Tasa de Completitud**: % de órdenes finalizadas

**Estado de Órdenes:**
- ✅ Completadas
- 🔄 En Proceso
- ⏸️ Pendientes

**Visualización:**
- Pie chart: Distribución de estados
- Métricas comparativas: Rápida vs Lenta
- Insight automático según tiempo promedio:
  - 🚀 <24h: Excelente velocidad
  - ⚠️ 24-48h: Adecuado, puede mejorar
  - 🚨 >48h: Revisar cuellos de botella

**Decisiones que soporta:**
- ¿El equipo está cumpliendo SLA de 15min por orden?
- ¿Hay cuellos de botella en el workflow?
- ¿Necesitamos contratar más Workers?

**Meta ideal:**
- Tiempo promedio: **<1 día**
- Tasa de completitud: **>90%**

---

## 🕐 Filtros de Período

Análisis disponible en 4 rangos de tiempo:

- **7D**: Últimos 7 días (análisis semanal)
- **30D**: Últimos 30 días (análisis mensual) - **DEFAULT**
- **90D**: Últimos 90 días (análisis trimestral)
- **ALL**: Todo el tiempo (histórico completo)

**Uso recomendado:**
- **7D**: Monitoreo diario, detección de anomalías
- **30D**: Revisiones mensuales, reportes ejecutivos
- **90D**: Análisis de tendencias, planificación trimestral
- **ALL**: Benchmarks históricos, análisis de crecimiento

---

## 📈 Visualizaciones

### Tecnología: Recharts
Biblioteca de gráficos React responsive e interactiva.

**Gráficos implementados:**

1. **Bar Chart**: Compras por producto
2. **Pie Chart**: 
   - Suscripciones activas vs canceladas
   - Estado de órdenes
3. **Progress Bars**: Tasas de conversión y churn
4. **Tabla**: Desempeño regional con sorting

**Características:**
- Responsive (adaptable a mobile)
- Tooltips interactivos
- Tema dark cyber (#00ff41 neon green)
- Animaciones suaves

---

## 🎨 UI/UX

**Theme:** Dark Cyber
- Background: `#0a0a0a`
- Primary: `#00ff41` (neon green)
- Secondary: `#00cc33`
- Danger: `#ff6b6b`
- Warning: `#ffa500`

**Cards de Métricas:**
- Border neon para KPIs principales
- Iconos Lucide React
- Valores grandes y legibles
- Subtextos contextuales

**Insights Automáticos:**
- 💡 Emoji de insight
- Código de colores según performance
- Recomendaciones accionables

---

## 🔐 Seguridad

**Control de Acceso:**
- Solo usuarios con role `SUPERUSER` pueden acceder
- Protegido por `<AuthGuard requiredRole="superuser">`
- Requiere autenticación JWT válida

**Endpoints protegidos:**
```http
GET /api/dashboard/analytics/business-intelligence?time_range=30d
Authorization: Bearer <jwt_token>
```

---

## 💡 Cómo Usar el Dashboard

### Para Analistas de Datos:

1. **Revisión Diaria (7D):**
   - Verificar conversion rate está >5%
   - Confirmar LTV trend positivo
   - Revisar tiempo promedio de órdenes <24h

2. **Revisión Semanal (30D):**
   - Comparar métricas vs semana anterior
   - Identificar top 3 países por ROI
   - Analizar churn rate de suscripciones

3. **Revisión Mensual (90D):**
   - Reportes ejecutivos con tendencias
   - Identificar estacionalidad
   - Planificar presupuesto de marketing por región

### Para Founders (Daniel):

**Preguntas que responde el dashboard:**

✅ **¿Dónde invertir marketing?**
→ Región con mejor ROI Score

✅ **¿Qué producto promocionar?**
→ Producto con mejor conversion rate

✅ **¿Es rentable el modelo de suscripción?**
→ LTV > Costo de adquisición (CAC)

✅ **¿El equipo es eficiente?**
→ Tiempo promedio < 24h

✅ **¿Dónde está el cuello de botella?**
→ Órdenes pendientes vs en proceso

---

## 🚀 Próximos Pasos

### Métricas Adicionales (Roadmap):

- [ ] **CAC** (Customer Acquisition Cost): Costo de adquirir cada cliente
- [ ] **Payback Period**: Cuánto tarda en recuperarse inversión
- [ ] **Revenue Cohorts**: Análisis por cohortes mensuales
- [ ] **MRR/ARR**: Monthly/Annual Recurring Revenue
- [ ] **Lead Source Analysis**: De dónde vienen los mejores leads
- [ ] **Time to Conversion**: Tiempo desde lead hasta compra
- [ ] **Product Mix Analysis**: Combinaciones de productos más comprados

### Integraciones:

- [ ] Export a CSV/Excel
- [ ] Envío automático de reportes por email
- [ ] Alertas cuando métricas caen bajo umbral
- [ ] Integración con Google Analytics
- [ ] Webhooks para Slack notifications

---

## 📊 Ejemplo de Análisis Completo

**Escenario:** Revisión mensual (30D)

### Resultados:
```
1. CONVERSIÓN
   - 1,250 leads
   - 800 diagnósticos entregados (64%)
   - Conversión global: 12.5%
   → Insight: Buen funnel, optimizar post-diagnóstico

2. REGIÓN
   - 🇧🇷 Brasil: ROI Score 450 (TOP)
   - 🇦🇷 Argentina: ROI Score 320
   - 🇲🇽 México: ROI Score 280
   → Decisión: Invertir 50% budget en Brasil

3. LTV
   - 45 suscripciones activas
   - Duración promedio: 3.8 meses
   - LTV: $110.20
   - Churn: 8% (verde)
   → Insight: Excelente retención

4. EFICIENCIA
   - 85 órdenes $99
   - Tiempo promedio: 18.5 horas
   - Completitud: 92%
   → Insight: Equipo cumpliendo SLA
```

### Acciones Recomendadas:
1. ✅ Aumentar ads en Brasil (mejor ROI)
2. ✅ Mantener estrategia de suscripciones (churn bajo)
3. ✅ Replicar workflow actual (eficiencia alta)
4. ⚠️ Investigar por qué 36% abandona pre-diagnóstico

---

## 🔧 Endpoints API

### Business Intelligence Completo
```http
GET /api/dashboard/analytics/business-intelligence
Query Params:
  - time_range: "7d" | "30d" | "90d" | "all"

Response:
{
  "time_range": "30d",
  "conversion_metrics": { ... },
  "region_performance": [ ... ],
  "subscription_ltv": { ... },
  "operational_efficiency": { ... }
}
```

### Analytics Básico (Legacy)
```http
GET /api/dashboard/analytics
Query Params:
  - time_range: "7d" | "30d" | "all"

Response:
{
  "total_leads": 1250,
  "total_orders": 100,
  "total_revenue": 8500.00,
  "conversion_rate": 12.5,
  "leads_by_country": [ ... ]
}
```

---

## 📚 Referencias

**Documentación técnica:**
- [Recharts Docs](https://recharts.org/)
- [Lucide Icons](https://lucide.dev/)
- FastAPI Schemas: `api_dashboard.py` líneas 690-890

**Acceso:**
- URL: `/dashboard/analytics`
- Role: `SUPERUSER`
- Componente: `frontend/src/app/dashboard/analytics/page.tsx`

---

**Desarrollado por Lokigi Team**  
Dashboard de Business Intelligence v2.0  
Última actualización: Diciembre 2024
