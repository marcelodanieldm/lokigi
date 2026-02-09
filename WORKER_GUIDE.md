# 📘 GUÍA PRÁCTICA PARA WORKERS - Lokigi Score

## Cómo Usar el Sistema de Análisis Manual

---

## 🎯 OBJETIVO

Analizar negocios de Google Maps y calcular su **Lokigi Score** + **Lucro Cesante** sin usar APIs costosas.

**Tiempo por análisis:** 2-3 minutos  
**Costo:** $0

---

## 📋 PASO A PASO

### 1️⃣ Buscar el Negocio en Google Maps

1. Ir a: https://maps.google.com
2. Buscar el nombre del negocio + ubicación
   - Ejemplo: "Pizzería Don Juan Buenos Aires"
3. Abrir el perfil completo del negocio

---

### 2️⃣ Copiar los Datos Visibles

#### A. INFORMACIÓN BÁSICA

**Nombre del Negocio:**
- Copiar exactamente como aparece en Google Maps
- Ejemplo: `Pizzería Don Juan`

**Dirección:**
- Copiar la dirección completa
- Ejemplo: `Av. Corrientes 1234, C1043 CABA, Argentina`

**Teléfono:**
- Copiar con el formato que aparece
- Ejemplo: `+54 11 4444-5555` o `011 4444-5555`

**Sitio Web:**
- Si aparece, copiarlo
- Ejemplo: `www.pizzeriadonjuan.com`

#### B. MÉTRICAS

**Rating:**
- Copiar solo el número
- Ejemplo: `4.5`

**Reseñas:**
- Copiar el texto completo
- Ejemplo: `230 reseñas` o `230 reviews` o `230 avaliações`

#### C. ESTADO DEL NEGOCIO

**¿Está reclamado?**
- Buscar texto como:
  - ✅ "Propietario de esta empresa" (Español)
  - ✅ "Owner of this business" (Inglés)
  - ✅ "Proprietário desta empresa" (Portugués)
- Si NO aparece nada, dejar el campo vacío

**¿Tiene badge de verificado?**
- Buscar una marca azul de verificación ✓
- Marcar checkbox si la tiene

#### D. CATEGORÍAS

**Categoría Principal:**
- La primera categoría que aparece
- Ejemplo: `Pizzería` o `Restaurante` o `Hotel`

**Categorías Adicionales:**
- Las demás categorías, separadas por comas
- Ejemplo: `Restaurante italiano, Delivery, Bar`

#### E. FOTOS

**Cantidad de Fotos:**
- Ver el contador de fotos
- Ejemplo: `45` o `45 fotos`

**Última Foto:**
- Ver cuándo se subió la última foto
- Ejemplos:
  - `hace 1 semana`
  - `hace 2 meses`
  - `1 year ago`
  - `2 anos atrás`

#### F. HORARIOS

**Horario de Atención:**
- Copiar el horario si está visible
- Ejemplo:
  ```
  Lun-Vie: 9:00-18:00
  Sáb: 10:00-14:00
  Dom: Cerrado
  ```

---

### 3️⃣ Ingresar los Datos en el Sistema

1. Ir a: `http://localhost:3000/dashboard/lokigi-score`
2. Completar el formulario con los datos copiados
3. Seleccionar el país correcto:
   - 🇦🇷 Argentina
   - 🇧🇷 Brasil
   - 🇺🇸 Estados Unidos
4. Si existe un lead, ingresar su email (opcional)
5. Click en **"Calcular Lokigi Score"**

---

### 4️⃣ Interpretar los Resultados

#### Score Total

| Score | Interpretación |
|-------|----------------|
| 85-100 | 🌟 **Excelente** - Negocio bien optimizado |
| 70-84 | ✅ **Bueno** - Algunas mejoras pendientes |
| 50-69 | ⚠️ **Regular** - Necesita atención |
| 30-49 | 🔴 **Crítico** - Problemas serios |
| 0-29 | 🚨 **Emergencia** - Pérdida masiva de clientes |

#### Lucro Cesante

**Qué significa:**
- Dinero que el negocio PIERDE cada mes por no estar en la posición #1
- Calculado en USD

**Ejemplos:**
- `$500/mes` → Optimización preventiva
- `$1,500/mes` → Necesita atención
- `$3,000/mes` → Prioridad alta
- `$10,000+/mes` → ¡EMERGENCIA!

#### Posición en Ranking

- **#1-2:** Excelente visibilidad
- **#3-4:** Buena visibilidad
- **#5-6:** Visibilidad media
- **#7-8:** Baja visibilidad
- **#9+:** Prácticamente invisible

---

## 💡 TIPS Y TRUCOS

### Tip 1: Scraping Más Rápido

**Usar atajos de teclado:**
1. Buscar negocio → `Ctrl+L` para ir a la barra de búsqueda
2. Copiar nombre → `Ctrl+C`
3. Cambiar a Lokigi Score → `Alt+Tab`
4. Pegar → `Ctrl+V`
5. Siguiente campo → `Tab`

### Tip 2: Campos Vacíos

Si un campo no tiene información:
- **Teléfono:** Dejar vacío
- **Horarios:** Dejar vacío
- **Reclamado:** Dejar vacío
- **Sitio web:** Dejar vacío

El algoritmo manejará estos casos correctamente.

### Tip 3: Formato de Fechas

El sistema entiende múltiples formatos:
- ✅ "hace 2 semanas"
- ✅ "2 weeks ago"
- ✅ "há 2 semanas"
- ✅ "hace 3 meses"
- ✅ "1 year ago"

### Tip 4: Rating con Decimales

- Usar punto (.) no coma (,)
- ✅ Correcto: `4.5`
- ❌ Incorrecto: `4,5`

---

## 📊 EJEMPLOS REALES

### Ejemplo 1: Negocio Crítico (Score Bajo)

**Datos copiados:**
```
Nombre: Local de Comidas Rápidas
Dirección: Calle 123, Buenos Aires
Teléfono: (vacío)
Rating: 3.1
Reseñas: 7 reseñas
Reclamado: (vacío)
Categoría: Restaurante
Fotos: 3
Última foto: hace 1 año
Horarios: (vacío)
País: Argentina
```

**Resultado esperado:**
- Score: ~30-40 puntos
- Lucro cesante: ~$2,000-3,000/mes
- Problemas críticos: 5-6
- **Diagnóstico:** Negocio en emergencia, necesita intervención inmediata

---

### Ejemplo 2: Negocio Medio (Score Regular)

**Datos copiados:**
```
Nombre: Restaurante Familia Silva
Dirección: Av. Paulista 1000, São Paulo
Teléfono: +55 11 98765-4321
Rating: 4.3
Reseñas: 45 reseñas
Reclamado: Proprietário desta empresa
Categoría: Restaurante
Fotos: 18
Última foto: hace 3 meses
Horarios: Seg-Sex: 11:00-23:00
País: Brasil
```

**Resultado esperado:**
- Score: ~65-75 puntos
- Lucro cesante: ~$1,000-1,500/mes
- Problemas críticos: 2-3
- **Diagnóstico:** Buen negocio con espacio de mejora

---

### Ejemplo 3: Negocio Excelente (Score Alto)

**Datos copiados:**
```
Nombre: Manhattan Premium Coffee
Dirección: Broadway Ave 456, New York, NY 10013
Teléfono: +1 (212) 555-0123
Rating: 4.8
Reseñas: 187 reviews
Reclamado: Owner of this business
Categoría: Coffee Shop
Fotos: 52
Última foto: 1 week ago
Horarios: Mon-Sun: 7:00 AM - 8:00 PM
País: Estados Unidos
```

**Resultado esperado:**
- Score: ~85-95 puntos
- Lucro cesante: ~$200-500/mes
- Problemas críticos: 0-1
- **Diagnóstico:** Excelente optimización, mantener momentum

---

## 🚨 ERRORES COMUNES

### Error 1: "Rating inválido"
**Causa:** Usar coma en lugar de punto  
**Solución:** Cambiar `4,5` por `4.5`

### Error 2: "País no soportado"
**Causa:** Código de país incorrecto  
**Solución:** Usar solo AR, BR o US

### Error 3: Lucro cesante demasiado alto/bajo
**Causa:** Categoría mal ingresada  
**Solución:** Verificar que la categoría esté correctamente escrita

### Error 4: No se guardan los datos en el lead
**Causa:** Email del lead incorrecto  
**Solución:** Verificar que el email existe en la base de datos

---

## ✅ CHECKLIST POR ANÁLISIS

Antes de calcular, verifica que tengas:

- [ ] Nombre del negocio
- [ ] Dirección completa
- [ ] Rating (con punto, no coma)
- [ ] Cantidad de reseñas
- [ ] Categoría principal
- [ ] País seleccionado correctamente
- [ ] (Opcional) Email del lead si existe

---

## 📈 METAS DE PRODUCTIVIDAD

### Por Worker

**Objetivo diario:**
- Mínimo: 10 análisis/día
- Óptimo: 20 análisis/día
- Excelente: 30+ análisis/día

**Tiempo promedio:**
- Principiante: 5 minutos/análisis
- Intermedio: 3 minutos/análisis
- Experto: 2 minutos/análisis

**Calidad:**
- 95%+ de datos correctos
- 0 errores de categoría
- 0 errores de país

---

## 🎓 CAPACITACIÓN

### Para Nuevos Workers

**Día 1:**
1. Leer esta guía completa
2. Practicar con 5 negocios de prueba
3. Comparar resultados con un Worker senior

**Día 2:**
1. Analizar 10 negocios reales
2. Verificar calidad con supervisor
3. Identificar áreas de mejora

**Día 3+:**
1. Objetivo de 20 análisis/día
2. Mantener calidad >95%
3. Optimizar velocidad

---

## 📞 SOPORTE

**¿Tienes dudas?**

1. Revisa esta guía
2. Consulta `LOKIGI_SCORE_QUICKSTART.md`
3. Pregunta a tu supervisor
4. Contacta al equipo técnico

---

## 🎉 CONCLUSIÓN

El sistema de **Lokigi Score** te permite:

✅ Analizar negocios en 2-3 minutos  
✅ Sin costo de APIs  
✅ Con precisión profesional  
✅ Generando valor real para clientes  

**¡Manos a la obra!** 🚀

---

**Última actualización:** Diciembre 22, 2024  
**Versión:** 1.0
