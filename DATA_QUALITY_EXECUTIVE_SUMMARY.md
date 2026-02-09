# 🛡️ Módulo "El Guardián de Integridad" - Resumen Ejecutivo

## 🎯 ¿Qué Hace Este Módulo?

**Problema que resuelve:**
Los negocios locales pierden clientes porque su información (nombre, teléfono, dirección) es inconsistente entre Google Maps, Facebook, Instagram y su sitio web. El cliente busca en Google, encuentra un teléfono, pero en Facebook aparece otro número diferente → **Cliente perdido.**

**Solución:**
Este módulo analiza automáticamente la consistencia de datos NAP (Name, Address, Phone) en todas las plataformas y genera un **Score de Integridad de Datos** (0-100%).

Si el score es **< 90%** → Recomienda automáticamente el **"Servicio de Limpieza de Datos" por $99**.

---

## 📊 Las 5 Dimensiones de Calidad Evaluadas

### 1. **Consistencia de Nombre** (20% del score)
¿El nombre del negocio es el mismo en Google, Facebook, Instagram y Web?

**Ejemplo de problema:**
- Google: "Café del Sol"
- Facebook: "Cafe del Sol Especialidades"
- Instagram: "CafeDelSol"
→ **Score: 75% (inconsistente)**

---

### 2. **Consistencia de Teléfono** (25% del score - LA MÁS IMPORTANTE)
¿El número de teléfono es idéntico en todas las plataformas?

**Normaliza números:**
- `+54 11 1234-5678` → `541112345678` (solo dígitos)
- Compara dígito por dígito (match exacto)

**Ejemplo crítico:**
- Google: `+54 11 1234-5678`
- Facebook: `+54 11 8765-4321` ❌
→ **Score: 50% (crítico) → Alerta roja**

---

### 3. **Consistencia de Dirección** (20% del score)
¿La dirección es similar en todas las plataformas?

**Tolera variaciones menores:**
- "Av. Libertador 1234" vs "Libertador 1234" → OK (90%)
- "Calle A 123" vs "Calle B 456" → MAL (30%)

---

### 4. **Exactitud de Ubicación** (20% del score)
¿El pin de Google Maps coincide con las coordenadas reales de la dirección?

**Usa fórmula de Haversine para calcular distancia:**
- ≤ 10m: Perfecto (100 puntos)
- ≤ 50m: Bueno (85 puntos)
- **> 50m: ⚠️ ALERTA "Pérdida de Clientes Físicos"**
- > 200m: Crítico (20 puntos)

**Ejemplo:**
- Pin en Maps: (-34.5833, -58.4011)
- Dirección real: (-34.5845, -58.4025)
- **Distancia: 135 metros → Score: 70% + Alerta crítica**

---

### 5. **Completitud de Información** (15% del score)
¿Tiene todos los campos vitales completos en Google Maps?

**Campos evaluados:**
- ✅ Horario de atención
- ✅ Descripción del negocio
- ✅ Sitio web
- ✅ Menú/catálogo
- ✅ Accesibilidad
- ✅ Atributos
- ✅ Servicios

**Ejemplo:**
- 3 de 7 campos completos → **Score: 43%**

---

## 🔢 Cálculo del Score Global

```python
Score Global = (
    Nombre × 20% +
    Teléfono × 25% +
    Dirección × 20% +
    Ubicación × 20% +
    Completitud × 15%
)
```

---

## 🚨 Sistema de Alertas Automáticas

### Alertas Críticas (Prioridad 1)
- Score global < 60%
- Teléfono inconsistente (< 80%)
- Ubicación con desfase > 50 metros

### Alertas de Advertencia (Prioridad 2)
- Score global 60-75%
- Campos vitales faltantes (< 70%)

---

## 💎 Oportunidad de Venta: Servicio de Limpieza $99

### Trigger Automático
```python
if overall_score < 90%:
    recommend_cleanup_service = True
```

### Pitch automático generado:
> **🚨 Alerta de Calidad de Datos**  
> Tu información tiene un score de **63%**. Los clientes no pueden encontrarte correctamente.  
>   
> **Problemas detectados:**  
> - 📞 Teléfono inconsistente entre Google y Facebook  
> - 📍 Pin de Maps está a 96 metros de tu dirección real  
> - 📋 Faltan 6 campos vitales en Google Maps  
>   
> **💎 Servicio de Limpieza de Datos: $99**  
> Corregimos todas las inconsistencias en 24 horas garantizadas.  

---

## 🎯 Ejemplo Real de Evaluación

### Input: Pizzería con datos inconsistentes

```json
{
  "google_maps": {
    "name": "Pizzería Napolitana",
    "phone": "+5491145678901",
    "address": "Corrientes 3456, CABA"
  },
  "facebook": {
    "name": "Pizzeria Napolitana - Corrientes",
    "phone": "+5491145678902",  // ❌ Diferente
    "address": "Corrientes 3456"
  },
  "website": {
    "name": "Napolitana Pizza",
    "phone": "+5491145678901"
  }
}
```

### Output: Score de Integridad 63.87%

```json
{
  "overall_score": 63.87,
  "dimensions": {
    "name_consistency": 75.91,    // ⚠️ Nombres diferentes
    "phone_consistency": 66.67,   // 🚨 Facebook tiene otro número
    "address_consistency": 79.37,
    "location_accuracy": 70.0,    // 🚨 Pin a 96m de la dirección
    "completeness": 14.29         // 🚨 Faltan 6 campos
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
      "message": "⚠️ Pérdida de Clientes Físicos: El pin está a 96m de la dirección real"
    }
  ],
  "recommendations": [
    "💎 ACCIÓN URGENTE: Score 63.87% (requiere limpieza profesional). Contrata el Servicio de Limpieza de Datos ($99).",
    "📞 Corrige el teléfono en Facebook: debe ser +5491145678901",
    "🗺️ Reposiciona el pin de Google Maps 96 metros hacia la dirección correcta.",
    "📋 Completa estos campos: Descripción, Sitio web, Menú, Accesibilidad, Atributos, Servicios."
  ],
  "requires_cleanup_service": true
}
```

---

## 🚀 Endpoints API Implementados

### 1. Evaluar Calidad de Datos
```http
POST /api/data-quality/evaluate
Authorization: Bearer <jwt_token>
```

### 2. Obtener Reporte
```http
GET /api/data-quality/report/{lead_id}
Authorization: Bearer <jwt_token>
```

### 3. Candidatos para Servicio de Limpieza
```http
GET /api/data-quality/cleanup-candidates
Authorization: Bearer <jwt_token>
```
→ Retorna lista de negocios con score < 90% ordenados de peor a mejor

---

## 📈 Casos de Uso Comerciales

### 1. **Upsell Automático Post-Diagnóstico**
Después del diagnóstico gratuito (Lokigi Score), evaluar calidad NAP:
- Si score < 90% → Mostrar CTA del servicio de limpieza $99
- Conversión estimada: **15-20%** de leads con problemas críticos

---

### 2. **Dashboard de Priorización de Ventas**
En el Admin Dashboard, mostrar tabla de candidatos:

| Negocio | Score | Alertas Críticas | CTA |
|---------|-------|------------------|-----|
| Peluquería Bella | 58% | 3 | 🔥 Contactar ahora |
| Pizzería Napolitana | 63% | 2 | ⚠️ Follow-up |
| Café del Sol | 82% | 1 | 📞 Oportunidad |

→ Priorizar contacto con scores más bajos

---

### 3. **Validación Post-Servicio**
Después de completar el servicio de limpieza, re-evaluar:
- **Antes:** Score 63%
- **Después:** Score 95%
- **Mejora:** +32%

→ Generar reporte de impacto para el cliente

---

## ✅ Tests Automatizados

**6 tests implementados:**
1. ✅ Evaluación con datos perfectos (score > 90%)
2. ✅ Evaluación con datos inconsistentes (requiere servicio)
3. ✅ Normalización de teléfonos
4. ✅ Cálculo de distancia Haversine
5. ✅ Similitud de strings
6. ✅ Generación de alertas críticas

**Ejecutar tests:**
```bash
python test_data_quality.py
```

**Resultado esperado:**
```
🎉 TODOS LOS TESTS PASARON EXITOSAMENTE
```

---

## 📦 Archivos del Módulo

### Backend:
- ✅ `data_quality_service.py` - Motor de evaluación (NAPEvaluator class)
- ✅ `api_data_quality.py` - 5 endpoints REST
- ✅ `models.py` - DataQualityEvaluation model (nueva tabla)
- ✅ `schemas.py` - 7 Pydantic schemas
- ✅ `migrate_data_quality.py` - Script de migración de BD
- ✅ `test_data_quality.py` - 6 tests automatizados
- ✅ `main.py` - Registro del router

### Documentación:
- ✅ `DATA_QUALITY_GUARDIAN.md` - Documentación técnica completa
- ✅ `DATA_QUALITY_EXECUTIVE_SUMMARY.md` - Este resumen ejecutivo

---

## 🎯 KPIs del Módulo

### Métricas de Adopción:
- **Evaluaciones realizadas:** N° de leads evaluados
- **Tasa de recomendación:** % de evaluaciones con score < 90%
- **Conversión a servicio:** % de recomendaciones que compraron el servicio $99

### Métricas de Impacto:
- **Score promedio antes del servicio:** Ejemplo: 65%
- **Score promedio después del servicio:** Ejemplo: 93%
- **Mejora promedio:** Ejemplo: +28 puntos

---

## 🚀 Próximos Pasos (Roadmap)

### Fase 2: Automatización
- [ ] Scraping automático de Facebook/Instagram/Website
- [ ] Evaluación periódica cada 30 días
- [ ] Alertas por email si score cae < 80%

### Fase 3: Integraciones
- [ ] Google Places API (verificar datos en tiempo real)
- [ ] Facebook Graph API
- [ ] Instagram Basic Display API

### Fase 4: Dashboard Frontend
- [ ] Visualización de score por dimensión (radar chart)
- [ ] Mapa con pin actual vs pin correcto
- [ ] Timeline de mejoras de score

---

## 💼 Impacto Comercial Estimado

### Por cada 100 leads:
- **Evaluaciones generadas:** 100
- **Leads con score < 90%:** ~40 (40%)
- **Conversión a servicio $99:** ~8 (20% de los 40)
- **Revenue generado:** **$792**

### Métricas anuales (1,000 leads/año):
- **Evaluaciones:** 1,000
- **Servicios vendidos:** ~80
- **Revenue anual:** **$7,920**

---

## ✨ Innovación Técnica

### Algoritmos implementados:
1. **Haversine Distance Formula** - Distancia entre coordenadas GPS
2. **SequenceMatcher (difflib)** - Similitud de strings
3. **Weighted Score Calculation** - Score ponderado multi-dimensional
4. **Automated Alert System** - Sistema de alertas por umbrales

### Patrones de diseño:
- ✅ Single Responsibility Principle (NAPEvaluator class)
- ✅ RESTful API design
- ✅ Pydantic schemas para validación
- ✅ SQLAlchemy ORM para persistencia
- ✅ Dependency Injection (FastAPI)

---

## 📞 Contacto y Soporte

**Equipo de Desarrollo:** Lokigi Team  
**Versión:** 1.0.0  
**Última actualización:** Diciembre 2024

**Documentación técnica completa:** `DATA_QUALITY_GUARDIAN.md`

---

**🎉 El Guardián de Integridad está listo para proteger la información de tus clientes y generar revenue con el servicio de limpieza de datos.**
