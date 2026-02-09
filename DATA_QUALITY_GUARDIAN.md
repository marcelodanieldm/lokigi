# 🛡️ El Guardián de Integridad - Data Quality & NAP Consistency

## Overview
Módulo de evaluación avanzada de calidad de datos que analiza la consistencia y exactitud de NAP (Name, Address, Phone) en múltiples plataformas digitales.

**Propósito:** Identificar inconsistencias en la información de contacto que causan pérdida de clientes y ventas.

---

## 🎯 Dimensiones de Calidad Evaluadas

### 1. **Consistencia de Nombre** (20% del score)
Compara el nombre del negocio entre plataformas:
- ✅ Google Maps (source of truth)
- 🔵 Facebook Business
- 📸 Instagram Business  
- 🌐 Sitio Web

**Algoritmo:**
- Usa `SequenceMatcher` para calcular similitud de strings
- Score promedio de todas las comparaciones
- Penaliza variaciones significativas del nombre

**Ejemplo de problema:**
```
Google Maps: "Café del Sol"
Facebook: "Cafe del Sol - Especialidades"
Instagram: "CafeDelSol"
Website: "Café & Restaurant del Sol"
→ Score: 75% (inconsistente)
```

---

### 2. **Consistencia de Teléfono** (25% del score)
Verifica que el número de teléfono sea idéntico en todas las plataformas.

**Normalización:**
- Remueve caracteres no numéricos: `+1 (555) 123-4567` → `15551234567`
- Compara dígitos puros (match exacto)

**Scoring:**
- 100%: Todas las plataformas tienen el mismo número
- 0%: Ninguna coincidencia

**⚠️ Alerta Crítica si score < 80%**

**Ejemplo de problema:**
```
Google Maps: +54 11 1234-5678
Facebook: +54 11 8765-4321  ❌ Diferente
Website: No tiene teléfono  ❌
→ Score: 33% (crítico)
```

---

### 3. **Consistencia de Dirección** (20% del score)
Compara direcciones entre plataformas usando similitud de texto.

**Consideraciones:**
- Variaciones menores aceptables (ej: "Street" vs "St.")
- Direcciones parciales penalizan el score
- Instagram generalmente no tiene dirección (no penaliza)

**Ejemplo de problema:**
```
Google Maps: "Av. Libertador 1234, CABA"
Facebook: "Libertador 1234"
Website: "Av. del Libertador 1234, Palermo"
→ Score: 85% (bueno, variaciones menores)
```

---

### 4. **Exactitud de Ubicación** (20% del score)
Verifica si el pin de Google Maps coincide con las coordenadas de la dirección.

**Cálculo:**
- Usa fórmula de Haversine para distancia entre coordenadas
- Umbral crítico: **50 metros**
- Si el desfase > 50m → Genera alerta "Pérdida de Clientes Físicos"

**Scoring:**
- ≤10m: 100 puntos (perfecto)
- ≤25m: 95 puntos (excelente)
- ≤50m: 85 puntos (bueno)
- ≤100m: 70 puntos (aceptable)
- ≤200m: 50 puntos (preocupante)
- >200m: 20 puntos (crítico)

**Ejemplo de problema:**
```
Pin de Maps: (-34.5833, -58.4011)
Dirección geocodificada: (-34.5845, -58.4025)
Distancia: 135 metros
→ Score: 70% + Alerta: "⚠️ Pérdida de Clientes Físicos"
```

---

### 5. **Completitud de Información** (15% del score)
Evalúa campos opcionales pero vitales en Google Maps.

**Campos evaluados:**
- ✅ Horario de atención (`business_hours`)
- ✅ Descripción del negocio (`description`)
- ✅ Sitio web (`website`)
- ✅ Menú o catálogo (`menu_url`)
- ✅ Accesibilidad (`accessibility_wheelchair`)
- ✅ Atributos (`attributes`)
- ✅ Servicios (`services`)

**Scoring:**
- Campos completados / Total de campos × 100

**Ejemplo de problema:**
```
✓ Horario: Presente
✓ Descripción: Presente
✓ Website: Presente
✗ Menú: Faltante
✗ Accesibilidad: Faltante
✗ Atributos: Faltante
✗ Servicios: Faltante
→ Score: 43% (3/7 campos completados)
```

---

## 📊 Score de Integridad de Datos

### Fórmula de Score Global (Ponderado)

```python
Overall Score = (
    name_consistency × 20% +
    phone_consistency × 25% +
    address_consistency × 20% +
    location_accuracy × 20% +
    completeness × 15%
)
```

### Clasificación de Scores

| Score | Etiqueta | Status | Acción |
|-------|----------|--------|--------|
| 95-100 | Excellent | 🟢 | Mantener |
| 90-94 | Good | 🟢 | Mejoras menores |
| 75-89 | Warning | 🟡 | Requiere atención |
| 60-74 | Poor | 🟠 | Servicio recomendado |
| 0-59 | Critical | 🔴 | **Servicio obligatorio** |

### Umbral de Servicio de Limpieza

**Si score < 90% → Recomendar automáticamente "Servicio de Limpieza de Datos" ($99)**

---

## 🚨 Sistema de Alertas

### Tipos de Alertas

**1. Critical (Prioridad 1)**
- Score global < 60%
- Teléfono inconsistente (score < 80%)
- Ubicación con desfase > 50 metros

**2. Warning (Prioridad 2)**
- Score global 60-75%
- Campos vitales faltantes (completitud < 70%)

### Estructura de Alertas

```json
{
  "type": "critical",
  "title": "🚨 Integridad de Datos Crítica",
  "message": "Score: 58%. El negocio está perdiendo clientes por información inconsistente.",
  "priority": 1
}
```

---

## 💡 Sistema de Recomendaciones

### Recomendaciones Automáticas

El sistema genera recomendaciones accionables basadas en problemas detectados:

**Ejemplo de output:**
```
1. 💎 ACCIÓN URGENTE: Score de integridad 58% (requiere limpieza profesional). 
   Contrata el Servicio de Limpieza de Datos ($99) para corregir todas las inconsistencias.

2. ✏️ Unifica el nombre del negocio en todas las plataformas (Google, Facebook, Instagram, Web).

3. 📞 Corrige el teléfono para que sea idéntico en Google Maps, redes sociales y sitio web.

4. 🗺️ Reposiciona el pin de Google Maps para que coincida exactamente con tu dirección física.

5. 📋 Completa estos campos en Google Maps: Horario de atención, Menú, Accesibilidad.
```

---

## 🔧 API Endpoints

### 1. Evaluar Calidad de Datos

```http
POST /api/data-quality/evaluate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "lead_id": 123,
  "google_maps_data": {
    "name": "Café del Sol",
    "phone": "+54 11 1234-5678",
    "address": "Av. Libertador 1234, CABA"
  },
  "google_maps_coordinates": [-34.5833, -58.4011],
  "facebook_data": {
    "name": "Café del Sol",
    "phone": "+54 11 1234-5678",
    "address": "Libertador 1234"
  },
  "instagram_data": {
    "name": "CafeDelSol"
  },
  "website_data": {
    "name": "Café & Restaurant del Sol",
    "phone": "+54 11 1234-5678",
    "address": "Av. del Libertador 1234, Palermo"
  },
  "address_coordinates": [-34.5845, -58.4025],
  "google_maps_extras": {
    "business_hours": "Lun-Vie 8am-10pm",
    "description": "Café especializado",
    "website": "https://cafedelsol.com"
  }
}
```

**Response:**
```json
{
  "lead_id": 123,
  "overall_score": 82.5,
  "name_consistency": {
    "score": 85.0,
    "status": "good",
    "details": {
      "google_maps_name": "Café del Sol",
      "comparisons": [
        {"platform": "Facebook", "similarity": 100},
        {"platform": "Instagram", "similarity": 75},
        {"platform": "Website", "similarity": 80}
      ]
    }
  },
  "phone_consistency": {
    "score": 100.0,
    "status": "excellent"
  },
  "address_consistency": {
    "score": 85.0,
    "status": "good"
  },
  "location_accuracy": {
    "score": 70.0,
    "status": "warning",
    "details": {
      "distance_meters": 135,
      "alert": "⚠️ Pérdida de Clientes Físicos: El pin está a 135m de la dirección real"
    }
  },
  "completeness": {
    "score": 57.0,
    "status": "poor",
    "details": {
      "missing_fields": ["Menú", "Accesibilidad", "Atributos", "Servicios"]
    }
  },
  "alerts": [
    {
      "type": "critical",
      "title": "📍 Ubicación Inexacta",
      "message": "⚠️ Pérdida de Clientes Físicos: El pin está a 135m de la dirección real",
      "priority": 1
    },
    {
      "type": "warning",
      "title": "📋 Información Incompleta",
      "message": "Faltan 4 campos vitales que afectan tu visibilidad en Google.",
      "priority": 2
    }
  ],
  "recommendations": [
    "🗺️ Reposiciona el pin de Google Maps para que coincida exactamente con tu dirección física.",
    "📋 Completa estos campos en Google Maps: Menú, Accesibilidad, Atributos."
  ],
  "requires_cleanup_service": true,
  "platforms_evaluated": ["google_maps", "facebook", "instagram", "website"],
  "evaluated_at": "2024-12-22T15:30:00Z"
}
```

---

### 2. Obtener Reporte Existente

```http
GET /api/data-quality/report/{lead_id}
Authorization: Bearer <jwt_token>
```

**Response:** Mismo formato que `/evaluate`

---

### 3. Resumen de Todas las Evaluaciones

```http
GET /api/data-quality/summary
Authorization: Bearer <jwt_token>
```

**Response:**
```json
[
  {
    "lead_id": 45,
    "business_name": "Peluquería Bella",
    "overall_score": 58.0,
    "requires_cleanup_service": true,
    "critical_alerts_count": 2,
    "evaluated_at": "2024-12-22T10:00:00Z"
  },
  {
    "lead_id": 123,
    "business_name": "Café del Sol",
    "overall_score": 82.5,
    "requires_cleanup_service": true,
    "critical_alerts_count": 1,
    "evaluated_at": "2024-12-22T15:30:00Z"
  }
]
```

**Ordenado por:** Score ascendente (peores primero)

---

### 4. Candidatos para Servicio de Limpieza

```http
GET /api/data-quality/cleanup-candidates
Authorization: Bearer <jwt_token>
```

**Response:** Lista de negocios con `score < 90%` ordenados por score ascendente

---

### 5. Eliminar Evaluación

```http
DELETE /api/data-quality/{lead_id}
Authorization: Bearer <jwt_token>
```

---

## 🗄️ Modelo de Base de Datos

### Tabla: `data_quality_evaluations`

```python
class DataQualityEvaluation(Base):
    id: int
    lead_id: int (FK, UNIQUE)
    
    # Scores
    overall_score: float
    name_consistency_score: float
    phone_consistency_score: float
    address_consistency_score: float
    location_accuracy_score: float
    completeness_score: float
    
    # Datos detallados (JSON)
    evaluation_data: JSON
    alerts: JSON
    recommendations: JSON
    
    # Flags
    requires_cleanup_service: bool
    platforms_evaluated: JSON
    status: str
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
```

---

## 🔐 Seguridad

**Autenticación requerida:** JWT Token

**Roles permitidos:**
- `SUPERUSER`: Acceso total
- `WORKER`: Solo lectura de reportes

**Endpoints protegidos:** Todos los endpoints de `/api/data-quality/*`

---

## 📈 Casos de Uso

### 1. Dashboard de Administración
Mostrar lista de negocios con peor score de integridad para priorizar ventas del servicio de limpieza.

```http
GET /api/data-quality/cleanup-candidates
```

---

### 2. Auditoría Automática Post-Diagnóstico
Después de generar el diagnóstico gratuito, ejecutar evaluación de calidad para detectar inconsistencias.

```http
POST /api/data-quality/evaluate
```

---

### 3. Upsell Inteligente
Si `requires_cleanup_service == true`, mostrar CTA:

> 🚨 **Alerta de Calidad de Datos**  
> Tu información tiene un score de 58%. Los clientes no pueden encontrarte correctamente.  
> 💎 **Servicio de Limpieza de Datos: $99**  
> Corregimos todas las inconsistencias en 24 horas.

---

### 4. Seguimiento de Mejoras
Re-evaluar después del servicio de limpieza para medir impacto:

```python
# Antes del servicio
score_before = 58%

# Después del servicio
score_after = 95%

# Mejora
improvement = +37%
```

---

## 🧪 Ejemplo Completo

### Escenario: Restaurante con Datos Inconsistentes

**Inputs:**
```json
{
  "lead_id": 456,
  "google_maps_data": {
    "name": "Pizzería Napolitana",
    "phone": "+5491145678901",
    "address": "Calle Corrientes 3456, CABA",
    "business_hours": "Lun-Dom 12pm-12am",
    "description": "Auténtica pizza napolitana",
    "website": "https://napolitana.com"
  },
  "google_maps_coordinates": [-34.6037, -58.3816],
  "facebook_data": {
    "name": "Pizzeria Napolitana - Corrientes",
    "phone": "+5491145678902",  // ❌ Número diferente
    "address": "Corrientes 3456"
  },
  "website_data": {
    "name": "Napolitana Pizza",
    "phone": "+5491145678901",
    "address": "Av. Corrientes 3456, Buenos Aires"
  },
  "address_coordinates": [-34.6045, -58.3820]  // 85m de diferencia
}
```

**Output:**
```json
{
  "overall_score": 76.5,
  "name_consistency": {
    "score": 88.0,
    "status": "good"
  },
  "phone_consistency": {
    "score": 66.7,  // ❌ Facebook tiene número diferente
    "status": "poor"
  },
  "address_consistency": {
    "score": 90.0,
    "status": "excellent"
  },
  "location_accuracy": {
    "score": 85.0,  // 85 metros de desfase
    "status": "good",
    "details": {
      "distance_meters": 85,
      "alert": "⚠️ Pérdida de Clientes Físicos: El pin está a 85m de la dirección real"
    }
  },
  "completeness": {
    "score": 71.4,
    "status": "warning",
    "details": {
      "missing_fields": ["Menú", "Accesibilidad"]
    }
  },
  "alerts": [
    {
      "type": "critical",
      "title": "📞 Teléfonos Inconsistentes",
      "message": "El teléfono no coincide entre plataformas. Los clientes no pueden contactarte."
    },
    {
      "type": "critical",
      "title": "📍 Ubicación Inexacta",
      "message": "⚠️ Pérdida de Clientes Físicos: El pin está a 85m de la dirección real"
    }
  ],
  "recommendations": [
    "💎 ACCIÓN URGENTE: Score de integridad 76.5% (requiere limpieza profesional).",
    "📞 Corrige el teléfono en Facebook: debe ser +5491145678901",
    "🗺️ Reposiciona el pin de Google Maps 85 metros hacia la dirección correcta.",
    "📋 Completa estos campos: Menú, Accesibilidad."
  ],
  "requires_cleanup_service": true
}
```

**Decisión comercial:**
- ✅ Ofrecer servicio de limpieza ($99)
- ✅ Prioridad: Corregir teléfono de Facebook
- ✅ Prioridad: Reposicionar pin de Maps

---

## 🚀 Próximos Pasos

### Mejoras Futuras

1. **Integración con APIs:**
   - Google Places API (verificar datos reales)
   - Facebook Graph API (extraer datos automáticamente)
   - Instagram Basic Display API

2. **Scoring Avanzado:**
   - Machine learning para detectar patrones de inconsistencia
   - Análisis de sentiment en reseñas para detectar menciones de "no encontré el lugar"

3. **Automatización:**
   - Scraping automático de Facebook/Instagram/Website
   - Evaluación periódica (cada 30 días)
   - Alertas por email si score cae < 80%

4. **Dashboard Frontend:**
   - Visualización de score por dimensión (radar chart)
   - Mapa con pin actual vs pin correcto
   - Timeline de mejoras de score

---

## 📚 Referencias Técnicas

**Archivos del módulo:**
- `data_quality_service.py` - Motor de evaluación (NAPEvaluator)
- `api_data_quality.py` - API endpoints
- `models.py` - DataQualityEvaluation model
- `schemas.py` - Pydantic schemas
- `migrate_data_quality.py` - Script de migración de BD

**Librerías utilizadas:**
- `difflib.SequenceMatcher` - Similitud de strings
- `math` - Cálculos de Haversine
- `re` - Normalización de teléfonos

**Algoritmos:**
- Haversine distance formula
- Sequence matching (similitud de texto)
- Weighted score calculation

---

**Desarrollado por Lokigi Team**  
Módulo "El Guardián de Integridad" v1.0  
Última actualización: Diciembre 2024
