# 🎯 LOKIGI SCORE ALGORITHM

## Algoritmo de Análisis SEO Local para Presupuesto CERO

**Versión:** 1.0  
**Fecha:** Diciembre 2024  
**Creado por:** Equipo Lokigi

---

## 📋 ÍNDICE

1. [Visión General](#visión-general)
2. [Arquitectura del Algoritmo](#arquitectura-del-algoritmo)
3. [Las 5 Dimensiones](#las-5-dimensiones)
4. [Cálculo del Score](#cálculo-del-score)
5. [Lucro Cesante](#lucro-cesante)
6. [Internacionalización](#internacionalización)
7. [Scraping Manual](#scraping-manual)
8. [API y Frontend](#api-y-frontend)
9. [Casos de Uso](#casos-de-uso)

---

## 🎯 VISIÓN GENERAL

### El Problema

Las APIs de Google Places son **costosas** ($17 por cada 1000 requests). Para una startup con presupuesto limitado, esto es insostenible.

### La Solución

**Lokigi Score** es un algoritmo que permite a los Workers copiar y pegar datos directamente desde Google Maps (scraping manual), procesarlos y generar:

- ✅ Score de 0 a 100 (salud SEO Local)
- 💰 Cálculo de lucro cesante (dinero perdido)
- 📊 Posicionamiento estimado en el ranking
- 🚨 Diagnóstico de problemas críticos
- ✅ Plan de acción priorizado

### Ventajas

- ✅ **Costo CERO** - No requiere APIs pagas
- ⚡ **Rápido** - Análisis en <1 segundo
- 🌎 **Internacional** - Soporta Argentina, Brasil y EE.UU.
- 🎯 **Preciso** - Basado en datos reales de Google Maps
- 📊 **Accionable** - Genera recomendaciones específicas

---

## 🏗️ ARQUITECTURA DEL ALGORITMO

```
┌─────────────────────────────────────┐
│   WORKER COPIA DATOS DE GOOGLE MAPS │
│   (Scraping Manual)                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   LOKIGI SCORE ALGORITHM             │
│   ┌─────────────────────────────┐   │
│   │ 1. Parse Manual Data        │   │
│   │ 2. Calculate 5 Dimensions   │   │
│   │ 3. Calculate Total Score    │   │
│   │ 4. Estimate Ranking         │   │
│   │ 5. Calculate Lucro Cesante  │   │
│   │ 6. Generate Recommendations │   │
│   └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   RESULTADO COMPLETO                 │
│   • Score Total: 0-100               │
│   • Scores por Dimensión             │
│   • Lucro Cesante: $/mes             │
│   • Clientes Perdidos                │
│   • Ranking Position                 │
│   • Problemas Críticos               │
│   • Recomendaciones                  │
└─────────────────────────────────────┘
```

---

## 📊 LAS 5 DIMENSIONES

Cada dimensión vale **20 puntos** (total = 100 puntos).

### 1️⃣ NAP (Name, Address, Phone) - 20 puntos

**Qué mide:** Completitud y consistencia de la información de contacto.

**Criterios:**
- ✅ Nombre completo: 4 puntos
- ✅ Dirección completa: 6 puntos
- ✅ Teléfono presente: 4 puntos
- ✅ Teléfono en formato válido: 2 puntos
- ✅ Consistencia general: 4 puntos

**Por qué importa:**
- Google premia perfiles con información completa y consistente
- El 90% de los usuarios verifica dirección y teléfono antes de visitar
- NAP consistente mejora el ranking en búsquedas locales

---

### 2️⃣ RESEÑAS - 20 puntos

**Qué mide:** Calidad y cantidad de reseñas.

**Criterios:**
- ⭐ Rating promedio (0-8 puntos):
  - 4.5+: 8 puntos
  - 4.0-4.4: 6 puntos
  - 3.5-3.9: 4 puntos
  - 3.0-3.4: 2 puntos
  
- 💬 Cantidad de reseñas (0-8 puntos):
  - 100+: 8 puntos
  - 50-99: 6 puntos
  - 25-49: 4 puntos
  - 10-24: 2 puntos
  
- 😊 Sentiment score: 4 puntos

**Por qué importa:**
- El 88% de los usuarios confía en las reseñas como recomendaciones personales
- Negocios con +50 reseñas tienen 270% más clics
- Rating <3.5 espanta al 78% de clientes potenciales

---

### 3️⃣ FOTOS - 20 puntos

**Qué mide:** Cantidad y frescura de las fotos.

**Criterios:**
- 📸 Cantidad de fotos (0-8 puntos):
  - 50+: 8 puntos
  - 25-49: 6 puntos
  - 10-24: 4 puntos
  - 5-9: 2 puntos
  
- 🆕 Frescura de fotos (0-12 puntos):
  - ≤7 días: 12 puntos
  - ≤30 días: 11 puntos
  - ≤90 días: 8 puntos
  - ≤180 días: 6 puntos
  - ≤365 días: 4 puntos
  - >365 días: 1 punto

**Por qué importa:**
- Negocios con fotos recientes obtienen 42% más clics
- Fotos del propietario generan 35% más confianza
- Google Maps prioriza negocios con contenido visual actualizado

---

### 4️⃣ CATEGORÍAS - 20 puntos

**Qué mide:** Relevancia y completitud de las categorías.

**Criterios:**
- 🏷️ Categoría principal definida: 10 puntos
- 🏷️ Categorías adicionales (0-5 puntos):
  - 3+: 5 puntos
  - 2: 3 puntos
  - 1: 2 puntos
- 🎯 Relevancia de categorías: 5 puntos

**Por qué importa:**
- La categoría principal determina en qué búsquedas apareces
- Categorías adicionales amplían tu alcance
- Categorías bien elegidas mejoran CTR en un 25%

---

### 5️⃣ VERIFICACIÓN - 20 puntos

**Qué mide:** Estado de reclamación y verificación del negocio.

**Criterios:**
- ✅ Negocio reclamado: **10 puntos** (MÁS CRÍTICO)
- ✅ Verificado por Google: 5 puntos
- ⏰ Horarios configurados: 5 puntos

**Por qué importa:**
- Negocios NO reclamados pueden ser editados por cualquiera
- Negocio reclamado = 40% más visibilidad
- Google prioriza perfiles verificados en resultados

---

## 🧮 CÁLCULO DEL SCORE

### Fórmula Total

```
LOKIGI SCORE = NAP + RESEÑAS + FOTOS + CATEGORÍAS + VERIFICACIÓN
Score Total = 0 a 100 puntos
```

### Interpretación del Score

| Score | Label | Significado |
|-------|-------|-------------|
| 85-100 | 🌟 Excelente | Top performer, mantén el momentum |
| 70-84 | ✅ Bueno | Sólido, pequeñas optimizaciones pendientes |
| 50-69 | ⚠️ Regular | Necesita mejoras importantes |
| 30-49 | 🔴 Crítico | Problemas serios que alejan clientes |
| 0-29 | 🚨 Emergencia | Pérdida masiva de clientes |

---

## 💰 LUCRO CESANTE

### ¿Qué es el Lucro Cesante?

Es el **dinero que un negocio deja de ganar** por no estar en la posición #1 del ranking de Google Maps.

### Fórmula del Lucro Cesante

```python
# 1. Volumen de búsqueda mensual de la categoría
search_volume = SEARCH_VOLUMES[country][category]

# 2. CTR (Click-Through Rate) por posición
current_ctr = POSITION_CTR[current_position]
potential_ctr = POSITION_CTR[1]  # Posición #1

# 3. Clicks perdidos
clicks_lost = (search_volume * potential_ctr) - (search_volume * current_ctr)

# 4. Conversión a clientes (asumimos 20%)
customers_lost = clicks_lost * 0.20

# 5. Valor económico
lucro_cesante_mensual = customers_lost * average_customer_value[country]
lucro_cesante_anual = lucro_cesante_mensual * 12
```

### CTR por Posición

| Posición | CTR | Significado |
|----------|-----|-------------|
| #1 | 35% | 35% de los buscadores hacen clic |
| #2 | 22% | 22% de los buscadores hacen clic |
| #3 | 15% | 15% de los buscadores hacen clic |
| #4 | 10% | |
| #5 | 8% | |
| #6 | 5% | |
| #7 | 3% | |
| #8 | 2% | |
| #9+ | <1% | Prácticamente invisible |

### Estimación de Posición en Ranking

```python
def estimate_position(score, review_count):
    if score >= 90 and review_count >= 100:
        return 1
    elif score >= 90 and review_count >= 50:
        return 2
    elif score >= 75 and review_count >= 50:
        return 3
    elif score >= 75 and review_count >= 25:
        return 4
    elif score >= 60 and review_count >= 25:
        return 5
    elif score >= 60:
        return 6
    elif score >= 45:
        return 7
    elif score >= 30:
        return 8
    else:
        return 10  # Fuera del top 8
```

---

## 🌎 INTERNACIONALIZACIÓN

### Países Soportados

1. 🇦🇷 **Argentina**
2. 🇧🇷 **Brasil**
3. 🇺🇸 **Estados Unidos**

### Volúmenes de Búsqueda por País

**Argentina (búsquedas/mes):**
- Restaurante: 18,000
- Pizzería: 12,000
- Café: 8,000
- Hotel: 15,000
- Dentista: 7,000
- Default: 5,000

**Brasil (búsquedas/mes):**
- Restaurante: 35,000
- Pizzaria: 22,000
- Café: 15,000
- Hotel: 28,000
- Dentista: 14,000
- Default: 10,000

**Estados Unidos (búsquedas/mes):**
- Restaurant: 90,000
- Pizza: 75,000
- Coffee: 60,000
- Hotel: 85,000
- Dentist: 65,000
- Default: 35,000

### Valor Promedio del Cliente

| País | Valor/Cliente (USD) |
|------|---------------------|
| Argentina | $25 |
| Brasil | $30 |
| Estados Unidos | $75 |

---

## 📋 SCRAPING MANUAL

### Workflow del Worker

1. **Buscar el negocio en Google Maps**
   - Ir a: https://maps.google.com
   - Buscar el negocio del cliente

2. **Copiar datos del perfil**
   - Nombre del negocio
   - Dirección completa
   - Teléfono
   - Rating (ej: "4.5")
   - Reseñas (ej: "230 reseñas")
   - Categoría principal
   - Cantidad de fotos
   - Fecha de última foto (ej: "hace 2 semanas")
   - Horarios de atención

3. **Indicadores de estado**
   - ¿Aparece "Propietario de esta empresa"? → Reclamado
   - ¿Tiene badge de verificado? → Verificado

4. **Pegar en el formulario de Lokigi Score**
   - Ingresar todos los datos copiados
   - Seleccionar país
   - Calcular

5. **Resultado instantáneo**
   - Score total
   - Lucro cesante
   - Problemas críticos
   - Recomendaciones

### Ventajas del Scraping Manual

✅ **Costo cero** - No gastar en APIs  
✅ **Control total** - El Worker verifica la calidad de los datos  
✅ **Flexibilidad** - Funciona con cualquier negocio en cualquier país  
✅ **Precisión** - Datos directos de Google Maps  
✅ **Rápido** - 2-3 minutos por negocio  

---

## 🖥️ API Y FRONTEND

### Endpoints API

#### 1. Análisis Manual (Autenticado)
```
POST /api/lokigi-score/analyze-manual
Authorization: Bearer {token}

Body:
{
  "business_name": "Pizzería Don Juan",
  "address": "Av. Corrientes 1234, Buenos Aires",
  "phone": "+54 11 4444-5555",
  "rating": "4.5",
  "reviews": "230 reseñas",
  "claimed_text": "Propietario de esta empresa",
  "primary_category": "Pizzería",
  "photo_count": "45",
  "last_photo_date": "hace 2 semanas",
  "country_code": "AR",
  "city": "Buenos Aires",
  "lead_email": "cliente@ejemplo.com"
}

Response:
{
  "total_score": 78,
  "score_label": "✅ Bueno",
  "dimension_scores": {
    "NAP": 18,
    "Reseñas": 16,
    "Fotos": 14,
    "Categorías": 15,
    "Verificación": 15
  },
  "lucro_cesante_mensual_usd": 1200.50,
  "lucro_cesante_anual_usd": 14406.00,
  "clientes_perdidos_mes": 48,
  "ranking_position_estimated": 3,
  "ranking_improvement_potential": 2,
  "critical_issues": [...],
  "recommendations": [...]
}
```

#### 2. Análisis Rápido (Sin Auth)
```
POST /api/lokigi-score/quick-analyze

(Mismo body y response que analyze-manual, pero sin guardar en DB)
```

#### 3. Volúmenes de Búsqueda
```
GET /api/lokigi-score/search-volumes/{country_code}

Response:
{
  "country": "AR",
  "search_volumes": {
    "restaurante": 18000,
    "pizzeria": 12000,
    ...
  },
  "average_customer_value_usd": 25
}
```

### Componente Frontend

**Ubicación:** `frontend/src/components/LokigiScoreManualInput.tsx`

**Características:**
- ✅ Formulario con todos los campos necesarios
- ✅ Validación en tiempo real
- ✅ Selector de país con banderas
- ✅ Resultados visuales con colores
- ✅ Desglose de scores por dimensión
- ✅ Cálculo de lucro cesante destacado
- ✅ Lista de problemas críticos
- ✅ Recomendaciones priorizadas

**Página:**
- `http://localhost:3000/dashboard/lokigi-score`

---

## 💼 CASOS DE USO

### Caso 1: Lead Nuevo

**Escenario:** Un cliente potencial solicita auditoría.

**Workflow:**
1. Worker busca el negocio en Google Maps
2. Copia los datos visibles
3. Pega en el formulario de Lokigi Score
4. Ingresa el email del lead
5. Sistema calcula score y guarda en la DB
6. Lead recibe reporte con lucro cesante

**Resultado:** Lead impactado con datos económicos reales.

---

### Caso 2: Análisis de Competencia

**Escenario:** Cliente quiere compararse con 3 competidores.

**Workflow:**
1. Worker analiza el negocio del cliente
2. Worker analiza 3 competidores
3. Compara los 4 Lokigi Scores
4. Identifica ventajas competitivas
5. Genera estrategia de diferenciación

**Resultado:** Cliente entiende dónde está fuerte y dónde debe mejorar.

---

### Caso 3: Seguimiento de Mejoras

**Escenario:** Cliente implementó recomendaciones hace 30 días.

**Workflow:**
1. Worker re-analiza el negocio
2. Compara score actual vs inicial
3. Calcula reducción en lucro cesante
4. Valida mejoras en posicionamiento
5. Genera reporte de progreso

**Resultado:** Cliente ve ROI tangible de las optimizaciones.

---

## 🚀 PRÓXIMOS PASOS

### Mejoras Futuras

1. **Automatización del Scraping**
   - Chrome Extension para copiar datos con un click
   - Integración con Puppeteer para scraping automático

2. **Más Dimensiones**
   - Preguntas y Respuestas
   - Posts de Google
   - Atributos especiales

3. **Más Países**
   - México
   - Colombia
   - España

4. **Machine Learning**
   - Predecir mejora de posición con mayor precisión
   - Detectar tendencias en el mercado local

5. **Dashboard de Monitoreo**
   - Tracking histórico de scores
   - Alertas de cambios importantes
   - Benchmarking automático contra competidores

---

## 📚 CONCLUSIÓN

**Lokigi Score** es un algoritmo de análisis SEO Local optimizado para **presupuesto cero**, que permite:

✅ Medir la salud de un perfil de Google Maps en 5 dimensiones críticas  
✅ Calcular el lucro cesante (dinero perdido) con precisión  
✅ Soportar múltiples países con métricas localizadas  
✅ Funcionar sin APIs costosas mediante scraping manual  
✅ Generar diagnósticos accionables en tiempo real  

**Es la herramienta perfecta para una startup que quiere ofrecer auditorías de alto valor sin quemar capital en infraestructura.**

---

**¿Preguntas?** Contacta al equipo de desarrollo.

**Última actualización:** Diciembre 2024
