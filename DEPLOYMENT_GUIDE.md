# 🚀 DEPLOYMENT GUIDE - Lokigi Score Algorithm

## Última actualización: Diciembre 22, 2024

---

## 📋 PRE-REQUISITOS

### Backend
- Python 3.8+
- FastAPI instalado
- SQLAlchemy configurado
- Base de datos PostgreSQL/SQLite

### Frontend
- Node.js 18+
- Next.js 13+
- React 18+
- Tailwind CSS

---

## 🔧 INSTALACIÓN

### 1. Backend Setup

```bash
# Navegar al directorio raíz
cd lokigi

# Instalar dependencias (si no están instaladas)
pip install -r requirements.txt

# No se requieren dependencias adicionales para el algoritmo
# El algoritmo usa solo la biblioteca estándar de Python
```

### 2. Frontend Setup

```bash
# Navegar al frontend
cd frontend

# Instalar dependencias de shadcn/ui (si no están instaladas)
npm install @radix-ui/react-label @radix-ui/react-select
npm install lucide-react class-variance-authority clsx tailwind-merge

# Verificar que Tailwind CSS esté configurado
# (Ya debería estar si el proyecto Next.js fue creado correctamente)
```

### 3. Verificar Archivos

Asegúrate de que existen estos archivos:

**Backend:**
- ✅ `lokigi_score_algorithm.py` - Algoritmo core
- ✅ `api_lokigi_score.py` - API endpoints
- ✅ `main.py` - Incluye el router de lokigi_score
- ✅ `test_lokigi_score.py` - Suite de tests

**Frontend:**
- ✅ `frontend/src/components/LokigiScoreManualInput.tsx` - Componente principal
- ✅ `frontend/src/app/dashboard/lokigi-score/page.tsx` - Página
- ✅ `frontend/src/components/ui/*.tsx` - Componentes UI
- ✅ `frontend/src/components/dashboard/DashboardSidebar.tsx` - Sidebar actualizado

**Documentación:**
- ✅ `LOKIGI_SCORE_ALGORITHM.md` - Documentación técnica
- ✅ `LOKIGI_SCORE_QUICKSTART.md` - Guía rápida
- ✅ `LOKIGI_SCORE_SUMMARY.md` - Resumen ejecutivo

---

## ▶️ EJECUCIÓN

### Paso 1: Iniciar Backend

```bash
# Terminal 1 - Backend
cd lokigi
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verificar que el servidor esté corriendo:
- API Docs: http://localhost:8000/docs
- Endpoints disponibles:
  - POST /api/lokigi-score/analyze-manual
  - POST /api/lokigi-score/quick-analyze
  - GET /api/lokigi-score/search-volumes/{country_code}

### Paso 2: Iniciar Frontend

```bash
# Terminal 2 - Frontend
cd frontend
npm run dev
```

Verificar que el frontend esté corriendo:
- Frontend: http://localhost:3000
- Lokigi Score: http://localhost:3000/dashboard/lokigi-score

### Paso 3: Ejecutar Tests

```bash
# Terminal 3 - Tests
cd lokigi
python test_lokigi_score.py
```

Deberías ver:
- ✅ Caso 1: Argentina - Score bajo (~29 pts)
- ✅ Caso 2: Brasil - Score medio (~68 pts)
- ✅ Caso 3: USA - Score alto (~83 pts)
- ✅ Comparación de resultados

---

## 🧪 TESTING

### Test Unitario del Algoritmo

```python
from lokigi_score_algorithm import quick_analyze_from_text

# Test simple
result = quick_analyze_from_text(
    business_name="Test Business",
    address="123 Test St",
    phone="+1 234 567 8900",
    rating="4.5",
    reviews="100 reviews",
    claimed_text="Owner of this business",
    category="Restaurant",
    photos_count="50",
    last_photo="1 week ago",
    country_code="US",
    city="New York"
)

assert result.total_score > 0
assert result.total_score <= 100
assert result.lucro_cesante_mensual >= 0
print("✅ Test passed!")
```

### Test de API con cURL

```bash
# Test del endpoint quick-analyze (sin auth)
curl -X POST "http://localhost:8000/api/lokigi-score/quick-analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Test Restaurant",
    "address": "123 Main St, New York",
    "phone": "+1 212 555 0123",
    "rating": "4.5",
    "reviews": "150 reseñas",
    "claimed_text": "Owner of this business",
    "primary_category": "Restaurant",
    "photo_count": "45",
    "last_photo_date": "1 week ago",
    "country_code": "US",
    "city": "New York"
  }'
```

### Test de Frontend

1. Abrir: http://localhost:3000/dashboard/lokigi-score
2. Completar el formulario con datos de prueba
3. Click en "Calcular Lokigi Score"
4. Verificar que aparecen:
   - Score total
   - Scores por dimensión
   - Lucro cesante
   - Problemas críticos
   - Recomendaciones

---

## 🔐 AUTENTICACIÓN

### Endpoint Público (quick-analyze)
- No requiere autenticación
- Ideal para demos o landing page

### Endpoint Autenticado (analyze-manual)
- Requiere Bearer token
- Se integra con el sistema de auth existente
- Guarda el análisis en la base de datos

```javascript
// Frontend - Con autenticación
const response = await fetch('http://localhost:8000/api/lokigi-score/analyze-manual', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify(data)
});
```

---

## 📊 MONITOREO

### Métricas a Monitorear

1. **Performance**
   - Tiempo de respuesta del algoritmo (<100ms esperado)
   - Tiempo de respuesta de la API (<200ms esperado)

2. **Uso**
   - Cantidad de análisis por día
   - Países más analizados
   - Categorías más comunes

3. **Calidad**
   - Distribución de scores (¿la mayoría está baja?)
   - Lucro cesante promedio por país
   - Problemas críticos más frecuentes

### Logging Recomendado

```python
# En api_lokigi_score.py
import logging

logger = logging.getLogger(__name__)

@router.post("/analyze-manual")
async def analyze_manual_data(...):
    logger.info(f"Analyzing business: {data.business_name} in {data.country_code}")
    
    result = quick_analyze_from_text(...)
    
    logger.info(f"Score: {result.total_score}, Lucro: ${result.lucro_cesante_mensual}/mes")
    
    return result
```

---

## 🐛 TROUBLESHOOTING

### Problema: "Module not found: lokigi_score_algorithm"

**Solución:**
```bash
# Asegúrate de estar en el directorio correcto
cd lokigi
python -c "import lokigi_score_algorithm; print('OK')"
```

### Problema: Frontend no conecta con API

**Solución:**
1. Verificar que el backend esté corriendo en puerto 8000
2. Verificar CORS en `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Problema: Componentes UI no se encuentran

**Solución:**
```bash
# Instalar dependencias faltantes
cd frontend
npm install @radix-ui/react-label @radix-ui/react-select
npm install lucide-react
```

### Problema: Errores de tipo en TypeScript

**Solución:**
```bash
# Verificar tsconfig.json
cd frontend
npx tsc --noEmit
```

---

## 🌍 CONFIGURACIÓN POR PAÍS

### Agregar un Nuevo País

1. **Editar `lokigi_score_algorithm.py`:**

```python
class Country(Enum):
    ARGENTINA = "AR"
    BRASIL = "BR"
    EEUU = "US"
    MEXICO = "MX"  # NUEVO

# Agregar volúmenes de búsqueda
SEARCH_VOLUMES = {
    # ... otros países ...
    Country.MEXICO: {
        "restaurante": 25000,
        "pizzeria": 15000,
        "cafe": 10000,
        # ... más categorías
        "default": 8000
    }
}

# Agregar valor del cliente
AVERAGE_CUSTOMER_VALUE = {
    # ... otros países ...
    Country.MEXICO: 28  # USD
}
```

2. **Actualizar el frontend:**

```tsx
// En LokigiScoreManualInput.tsx
<SelectContent>
  <SelectItem value="AR">🇦🇷 Argentina</SelectItem>
  <SelectItem value="BR">🇧🇷 Brasil</SelectItem>
  <SelectItem value="US">🇺🇸 Estados Unidos</SelectItem>
  <SelectItem value="MX">🇲🇽 México</SelectItem>
</SelectContent>
```

---

## 📈 OPTIMIZACIÓN

### Performance Tips

1. **Cachear volúmenes de búsqueda:**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_search_volume(country: Country, category: str) -> int:
    # ...
```

2. **Batch processing:**
```python
def analyze_multiple(businesses: List[ManualScrapedData]) -> List[LokigiScoreResult]:
    return [calculator.calculate_lokigi_score(b) for b in businesses]
```

3. **Async API:**
```python
@router.post("/analyze-manual")
async def analyze_manual_data(...):
    # El algoritmo es síncrono pero la API es async
    # Considerar usar asyncio.to_thread() para operaciones pesadas
```

---

## 🔄 ACTUALIZACIONES FUTURAS

### Roadmap de Features

**Q1 2025:**
- [ ] Chrome Extension para scraping automático
- [ ] Más países (México, Colombia)
- [ ] Más categorías de negocios

**Q2 2025:**
- [ ] Machine Learning para predicción de mejora
- [ ] Análisis de competidores automático
- [ ] Dashboard de tendencias

**Q3 2025:**
- [ ] Integración con Puppeteer
- [ ] OCR para screenshots
- [ ] API pública

---

## 📞 SOPORTE

### Recursos

- **Documentación técnica:** `LOKIGI_SCORE_ALGORITHM.md`
- **Guía rápida:** `LOKIGI_SCORE_QUICKSTART.md`
- **Resumen ejecutivo:** `LOKIGI_SCORE_SUMMARY.md`
- **Tests:** `python test_lokigi_score.py`

### Contacto

Para preguntas o issues:
1. Revisar la documentación
2. Ejecutar los tests
3. Verificar logs del backend
4. Contactar al equipo de desarrollo

---

## ✅ CHECKLIST DE DEPLOYMENT

### Pre-deployment
- [ ] Tests pasan correctamente
- [ ] Frontend compila sin errores
- [ ] Backend responde en todos los endpoints
- [ ] Documentación actualizada

### Deployment
- [ ] Backend deployed y corriendo
- [ ] Frontend deployed y accesible
- [ ] Variables de entorno configuradas
- [ ] CORS configurado correctamente

### Post-deployment
- [ ] Verificar endpoints en producción
- [ ] Verificar frontend en producción
- [ ] Capacitar a Workers
- [ ] Monitorear métricas

---

## 🎉 CONCLUSIÓN

El **Lokigi Score Algorithm** está listo para producción.

**Status:** ✅ **READY TO DEPLOY**

**Próximo paso:** 
1. Ejecutar tests finales
2. Capacitar Workers en el uso del sistema
3. Empezar a analizar negocios reales

---

**Última verificación:** Diciembre 22, 2024  
**Versión:** 1.0.0  
**Estado:** Production Ready ✅
