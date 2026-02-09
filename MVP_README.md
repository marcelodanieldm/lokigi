# Backend MVP - SEO Local Analyzer 🚀

Sistema de análisis SEO Local profesional que transforma datos técnicos en impacto económico.

## ✨ Características Principales

### 🎯 El Consultor de IA
- Analiza negocios locales con tono de consultor experto
- Transforma problemas técnicos en **dinero perdido**
- Compara con 3 competidores simulados a 10km
- Genera análisis FODA completo
- Plan de acción específico y accionable

### 📊 Lógica de Scoring (0-100)
```
Puntos base: 100

Deducciones:
- Rating bajo: hasta -30 puntos
- Pocas reseñas: hasta -25 puntos  
- Sin sitio web: -20 puntos
- No reclamado: -25 puntos (CRÍTICO)
- Fotos antiguas: hasta -15 puntos
```

### 💰 Impacto Económico
Calcula pérdidas mensuales reales:
- Sin web: **-$1,800/mes**
- No reclamado: **-$2,400/mes**
- Rating bajo: **-$1,200/mes**
- Pocas reseñas: **-$900/mes**
- Fotos antiguas: **-$600/mes**

## 🚀 Quick Start

### 1. Instalar dependencias
```bash
pip install fastapi uvicorn openai pydantic requests
```

### 2. Configurar OpenAI (opcional)
```bash
# Si quieres usar IA avanzada
export OPENAI_API_KEY=tu_key_aqui

# Sin OpenAI funciona con análisis basado en reglas
```

### 3. Ejecutar servidor
```bash
python api_mvp.py
```

Servidor corriendo en: `http://localhost:8000`

### 4. Probar el API
```bash
# En otro terminal
python test_api.py
```

## 📡 Endpoints

### POST `/audit/test`
**Endpoint principal de auditoría completa**

**Request:**
```json
{
  "business": {
    "name": "Restaurante Casa Pepe",
    "rating": 3.5,
    "review_count": 23,
    "has_website": false,
    "is_claimed": false,
    "last_photo_date": "2023-03-15",
    "category": "Restaurante",
    "location": "Madrid"
  },
  "include_ai_analysis": true
}
```

**Response:**
```json
{
  "score": 42,
  "critical_fix": "🚨 URGENTE: Tu negocio NO está reclamado...",
  "economic_impact": "💸 ESTÁS PERDIENDO $5,100/mes...",
  "foda": {
    "fortalezas": ["..."],
    "oportunidades": ["..."],
    "debilidades": ["..."],
    "amenazas": ["..."]
  },
  "competitors": [
    {
      "name": "Competidor 1",
      "rating": 4.5,
      "review_count": 234,
      "has_website": true,
      "distance_km": 3.2,
      "estimated_monthly_revenue": "$25k"
    }
  ],
  "detailed_analysis": "Tu negocio tiene un score de 42/100...",
  "action_plan": [
    "PASO 1: Reclama tu negocio HOY...",
    "PASO 2: Crea sitio web esta semana..."
  ]
}
```

### POST `/audit/quick`
**Auditoría rápida (solo score + problema crítico)**

### GET `/audit/example`
**Obtiene ejemplo de request para testing**

### GET `/docs`
**Documentación interactiva Swagger**

## 🏗️ Arquitectura

```
Backend MVP/
├── api_mvp.py              # FastAPI app principal
├── audit_schemas.py        # Modelos Pydantic
├── analyzer_service.py     # Lógica de análisis (El Consultor)
└── test_api.py            # Suite de testing
```

## 🧠 El Consultor de IA

### Sin OpenAI (Análisis basado en reglas)
- Score calculado con lógica matemática
- FODA generado con reglas if/else
- Impacto económico con fórmulas predefinidas
- **Ventaja:** Funciona sin API key, respuesta instantánea

### Con OpenAI (Análisis avanzado)
- Usa GPT-4 para generar FODA contextualizado
- Análisis narrativo personalizado
- Plan de acción más sofisticado
- **Ventaja:** Insights únicos y creativos

## 📊 Ejemplo de Análisis

**Input:**
- Restaurante con rating 3.5
- 23 reseñas
- Sin sitio web
- No reclamado

**Output:**
```
Score: 42/100 🔴 CRÍTICO

Problema Crítico:
🚨 Tu negocio NO está reclamado. Pierdes $2,400/mes.

Impacto Económico:
💸 ESTÁS PERDIENDO $5,100/mes ($61,200/año)

• $2,400/mes por no reclamar
• $1,800/mes sin sitio web  
• $900/mes por pocas reseñas

= 102 clientes/mes que van a competencia

FODA:
✓ Fortalezas: Rating aceptable de 3.5
→ Oportunidades: Lanzar web captura $1,800/mes extra
✗ Debilidades: Solo 23 reseñas, falta prueba social
⚠ Amenazas: Competidores mejor posicionados roban mercado

Plan de Acción:
1. PASO 1 (HOY): Reclama tu negocio en Google
2. PASO 2 (Esta semana): Crea landing page simple
3. PASO 3 (7 días): Pide reseñas a 20 clientes
```

## 🧪 Testing

### Test automático
```bash
python test_api.py
```

### Test manual con curl
```bash
curl -X POST http://localhost:8000/audit/test \
  -H "Content-Type: application/json" \
  -d '{
    "business": {
      "name": "Mi Negocio",
      "rating": 3.8,
      "review_count": 47,
      "has_website": false,
      "is_claimed": false,
      "last_photo_date": "2023-08-15"
    },
    "include_ai_analysis": false
  }'
```

### Test en Swagger UI
1. Abrir `http://localhost:8000/docs`
2. Click en POST `/audit/test`
3. Click "Try it out"
4. Pegar JSON de ejemplo
5. Click "Execute"

## 🎯 Casos de Uso

### 1. Negocio Crítico (Score < 40)
- No reclamado
- Sin web
- Pocas reseñas
- **Acción:** Oferta Plan Express inmediato

### 2. Negocio Mejorable (Score 40-70)
- Tiene presencia básica
- Necesita optimización
- **Acción:** Plan de mejora gradual

### 3. Negocio Bien Posicionado (Score > 70)
- Todo optimizado
- Mantener momentum
- **Acción:** Estrategia de dominación

## 💡 Personalización

### Ajustar lógica de scoring
Edita `_calculate_score()` en [analyzer_service.py](analyzer_service.py):
```python
# Cambiar penalización por no tener web
if not business.has_website:
    score -= 30  # Aumentar de 20 a 30
```

### Ajustar impacto económico
Edita `_calculate_economic_impact()`:
```python
if not business.has_website:
    monthly_loss += 2500  # Aumentar de 1800 a 2500
```

### Personalizar tono del análisis
Modifica los prompts en las funciones `_generate_*_with_ai()`

## 🚀 Próximas Mejoras

- [ ] Integración Google Places API (competencia real)
- [ ] Análisis de palabras clave
- [ ] Tracking histórico de scores
- [ ] Webhooks para notificaciones
- [ ] Dashboard web interactivo
- [ ] Exportación a PDF
- [ ] Comparativas de industria

## 📈 Métricas de Éxito

El MVP está diseñado para:
- ✅ Respuesta en < 2 segundos (sin IA)
- ✅ Respuesta en < 5 segundos (con IA)
- ✅ 100% de cobertura en casos de uso
- ✅ Análisis claro y accionable
- ✅ Impacto económico cuantificado

## 🔧 Stack Tecnológico

- **FastAPI** - Framework web moderno
- **Pydantic** - Validación de datos
- **OpenAI GPT-4** - Análisis con IA (opcional)
- **Python 3.10+** - Lenguaje base

## 📄 Licencia

MIT

---

**Desarrollado con 💪 para dominar el SEO Local**
