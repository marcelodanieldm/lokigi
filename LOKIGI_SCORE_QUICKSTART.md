# 🚀 Quick Start - Lokigi Score Algorithm

## Instalación y Uso Inmediato

### 1. Ejecutar el Test de Demostración

```bash
# Desde la raíz del proyecto
python test_lokigi_score.py
```

Este script ejecutará 3 casos de prueba:
- 🇦🇷 Pizzería en Argentina (Score bajo)
- 🇧🇷 Restaurante en Brasil (Score medio)
- 🇺🇸 Coffee Shop en USA (Score alto)

### 2. Usar desde Python

```python
from lokigi_score_algorithm import quick_analyze_from_text

# Analizar un negocio
result = quick_analyze_from_text(
    business_name="Pizzería Don Juan",
    address="Av. Corrientes 1234, Buenos Aires",
    phone="+54 11 4444-5555",
    rating="4.5",
    reviews="230 reseñas",
    claimed_text="Propietario de esta empresa",
    category="Pizzería",
    photos_count="45",
    last_photo="hace 2 semanas",
    country_code="AR",
    city="Buenos Aires"
)

# Resultados
print(f"Score: {result.total_score}/100")
print(f"Lucro Cesante: ${result.lucro_cesante_mensual}/mes")
print(f"Posición: #{result.ranking_position_estimated}")
```

### 3. Usar desde la API

#### Iniciar el servidor:
```bash
uvicorn main:app --reload
```

#### Llamar al endpoint:
```bash
curl -X POST "http://localhost:8000/api/lokigi-score/quick-analyze" \
  -H "Content-Type: application/json" \
  -d '{
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
    "city": "Buenos Aires"
  }'
```

### 4. Usar desde el Frontend

1. Iniciar el backend:
```bash
uvicorn main:app --reload
```

2. Iniciar el frontend:
```bash
cd frontend
npm run dev
```

3. Navegar a:
```
http://localhost:3000/dashboard/lokigi-score
```

4. Completar el formulario con datos de Google Maps

---

## 📋 Guía Rápida para Workers

### Paso 1: Buscar el negocio en Google Maps
1. Ir a https://maps.google.com
2. Buscar el negocio del cliente
3. Abrir el perfil completo

### Paso 2: Copiar los datos visibles

**Datos básicos:**
- ✅ Nombre del negocio
- ✅ Dirección completa
- ✅ Teléfono
- ✅ Sitio web (si aparece)

**Métricas:**
- ✅ Rating (ej: "4.5")
- ✅ Cantidad de reseñas (ej: "230 reseñas")

**Estado:**
- ✅ ¿Aparece "Propietario de esta empresa"? → Copiar ese texto
- ✅ ¿Tiene badge verificado? → Marcar checkbox

**Categorías:**
- ✅ Categoría principal
- ✅ Categorías secundarias (separadas por comas)

**Fotos:**
- ✅ Cantidad total de fotos
- ✅ Fecha de la última foto (ej: "hace 2 semanas")

**Horarios:**
- ✅ Horario de atención

### Paso 3: Pegar en Lokigi Score
1. Abrir http://localhost:3000/dashboard/lokigi-score
2. Pegar cada dato en su campo correspondiente
3. Seleccionar el país correcto
4. Click en "Calcular Lokigi Score"

### Paso 4: Resultado Instantáneo
En menos de 1 segundo obtendrás:
- ✅ Score total (0-100)
- 💰 Lucro cesante mensual y anual
- 📍 Posición estimada en el ranking
- 🚨 Problemas críticos
- ✅ Plan de acción priorizado

---

## 🌎 Países Soportados

### Argentina (AR)
- Volumen de búsqueda promedio: Medio
- Valor del cliente: $25 USD
- Categorías soportadas: 10+

### Brasil (BR)
- Volumen de búsqueda promedio: Alto
- Valor del cliente: $30 USD
- Categorías soportadas: 10+

### Estados Unidos (US)
- Volumen de búsqueda promedio: Muy Alto
- Valor del cliente: $75 USD
- Categorías soportadas: 10+

---

## 🎯 Ejemplos de Uso

### Ejemplo 1: Negocio Crítico (Score < 50)

```python
result = quick_analyze_from_text(
    business_name="Local Sin Optimizar",
    address="Calle 123",
    phone="",  # Sin teléfono
    rating="3.0",  # Rating bajo
    reviews="5 reseñas",  # Muy pocas
    claimed_text="",  # NO RECLAMADO
    category="Restaurante",
    photos_count="2",
    last_photo="hace 1 año",
    country_code="AR",
    city="Buenos Aires"
)

# Resultado esperado:
# - Score: ~30-40 puntos
# - Lucro cesante: ~$2,000-3,000/mes
# - Problemas críticos: 5-6
# - Potencial de mejora: 7 posiciones
```

### Ejemplo 2: Negocio Optimizado (Score > 85)

```python
result = quick_analyze_from_text(
    business_name="Negocio Premium",
    address="Av. Principal 1000, Ciudad",
    phone="+54 11 1234-5678",
    rating="4.8",
    reviews="250 reseñas",
    claimed_text="Propietario de esta empresa",
    category="Restaurante",
    photos_count="75",
    last_photo="hace 3 días",
    country_code="AR",
    city="Buenos Aires"
)

# Resultado esperado:
# - Score: ~85-95 puntos
# - Lucro cesante: ~$200-500/mes
# - Problemas críticos: 0-1
# - Potencial de mejora: 1 posición
```

---

## 💡 Tips para Maximizar el Score

### 1. Verificación (20 puntos)
- ✅ Reclamar el negocio en GMB: +10 puntos
- ✅ Verificar con Google: +5 puntos
- ✅ Configurar horarios: +5 puntos

### 2. NAP (20 puntos)
- ✅ Nombre completo: +4 puntos
- ✅ Dirección completa: +6 puntos
- ✅ Teléfono en formato correcto: +6 puntos
- ✅ Consistencia: +4 puntos

### 3. Reseñas (20 puntos)
- ✅ Conseguir 100+ reseñas: +8 puntos
- ✅ Mantener rating 4.5+: +8 puntos
- ✅ Responder reseñas: +4 puntos

### 4. Fotos (20 puntos)
- ✅ Subir 50+ fotos: +8 puntos
- ✅ Actualizar cada semana: +12 puntos

### 5. Categorías (20 puntos)
- ✅ Definir categoría principal: +10 puntos
- ✅ Agregar 3+ secundarias: +5 puntos
- ✅ Elegir categorías relevantes: +5 puntos

---

## 🔧 Troubleshooting

### Error: "País no soportado"
**Solución:** Usar uno de los códigos válidos: AR, BR, US

### Error: "Rating inválido"
**Solución:** El rating debe ser un número entre 0 y 5

### Resultado inesperado en lucro cesante
**Verificar:**
- ¿La categoría está bien escrita?
- ¿El país es correcto?
- ¿Los datos son precisos?

### Frontend no conecta con la API
**Solución:**
1. Verificar que el backend esté corriendo en puerto 8000
2. Verificar CORS en main.py
3. Verificar token de autenticación si es necesario

---

## 📊 Interpretación de Resultados

### Scores por Dimensión

| Dimensión | Excelente | Bueno | Regular | Crítico |
|-----------|-----------|-------|---------|---------|
| NAP | 18-20 | 15-17 | 12-14 | <12 |
| Reseñas | 18-20 | 15-17 | 12-14 | <12 |
| Fotos | 18-20 | 15-17 | 12-14 | <12 |
| Categorías | 18-20 | 15-17 | 12-14 | <12 |
| Verificación | 18-20 | 15-17 | 12-14 | <12 |

### Lucro Cesante

- **< $500/mes:** Optimización preventiva
- **$500-1,500/mes:** Necesita atención
- **$1,500-3,000/mes:** Prioridad alta
- **> $3,000/mes:** Emergencia - pérdidas significativas

### Posición en Ranking

- **#1-2:** Excelente
- **#3-4:** Bueno
- **#5-6:** Regular
- **#7-8:** Crítico
- **#9+:** Invisible

---

## 🚀 Próximos Pasos

1. **Ejecuta el test:** `python test_lokigi_score.py`
2. **Lee la documentación completa:** `LOKIGI_SCORE_ALGORITHM.md`
3. **Prueba la API:** `http://localhost:8000/docs`
4. **Prueba el frontend:** `http://localhost:3000/dashboard/lokigi-score`

---

## 🆘 Soporte

¿Preguntas? Contacta al equipo de desarrollo.

**Documentación completa:** [LOKIGI_SCORE_ALGORITHM.md](./LOKIGI_SCORE_ALGORITHM.md)
