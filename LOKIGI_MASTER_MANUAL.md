# 📘 LOKIGI MASTER MANUAL
## Manual de Procedimientos Premium para Workers

> **Versión:** 1.0  
> **Última actualización:** Diciembre 2025  
> **Clasificación:** Interno - Uso exclusivo del equipo de Operations

---

## 🎯 MISIÓN DEL WORKER

Tu trabajo es **transformar diagnósticos en resultados tangibles** que generen un impacto medible en la visibilidad online del cliente. Cada servicio Premium ($99) debe cumplir estándares de excelencia que justifiquen la inversión del cliente.

**Meta de eficiencia:** 20 minutos por orden (promedio)  
**Meta de calidad:** Score de mejora > 15 puntos  
**Meta de satisfacción:** 0 quejas de calidad

---

## 📋 SECCIÓN 1: PROTOCOLO DE DIAGNÓSTICO

### 1.1 Lectura del Reporte de "Lucro Cesante"

Cuando recibes una orden asignada, tu **primer paso** es acceder al reporte de auditoría del cliente. Este reporte está diseñado para priorizarte el trabajo.

#### ✅ Cómo leer el Score de Visibilidad:

```
Score 0-30:   🔴 CRÍTICO - Cliente en peligro de invisibilidad
Score 31-60:  🟡 MEDIO - Necesita mejoras sustanciales
Score 61-80:  🟢 BUENO - Optimización fina
Score 81-100: ✅ EXCELENTE - Mantenimiento preventivo
```

#### 📊 Estructura del Reporte:

El reporte JSON contiene:
- `fallos_criticos`: Array de problemas detectados
- `score_visibilidad`: Número del 0-100
- `impacto_economico`: Estimación de pérdidas mensuales

#### 🎯 Priorización de Tareas:

**SIEMPRE trabaja en este orden:**

1. **Fallos Críticos** (impacto_economico > $500/mes)
   - Perfil duplicado
   - Información NAP inconsistente
   - Categoría incorrecta
   - Horarios inexistentes

2. **Mejoras de Alto Impacto** (15-30 min de trabajo)
   - Descripción de negocio vacía o genérica
   - Menos de 5 fotos geolabeled
   - Sin atributos de negocio
   - Productos/servicios sin completar

3. **Optimización Fina** (5-10 min)
   - Mejorar SEO de descripción
   - Agregar preguntas frecuentes
   - Completar campos adicionales

#### 📖 Ejemplo de Lectura:

```json
{
  "fallos_criticos": [
    {
      "titulo": "Perfil Duplicado Detectado",
      "descripcion": "Existen 2 perfiles con el mismo nombre y dirección similar",
      "impacto_economico": "$850/mes en confusión de clientes"
    },
    {
      "titulo": "Descripción Vacía",
      "descripcion": "El campo 'Acerca de' está completamente vacío",
      "impacto_economico": "$320/mes en pérdida de conversión"
    }
  ],
  "score_visibilidad": 42
}
```

**Tu análisis:**
1. Cliente tiene score MEDIO (42) → Necesita trabajo sustancial
2. Prioridad #1: Resolver perfil duplicado ($850/mes)
3. Prioridad #2: Redactar descripción ($320/mes)
4. Tiempo estimado: 20 minutos

---

## 🚨 SECCIÓN 2: TRATAMIENTO DE CASOS DIFÍCILES

### 2.1 Perfil Duplicado Detectado

**Escenario:** Google Maps muestra 2+ perfiles del mismo negocio.

#### 🔍 Diagnóstico:

1. Abre Google Maps
2. Busca el nombre del negocio + ciudad
3. Verifica si aparecen múltiples marcadores en el mismo lugar
4. Comprueba diferencias: dirección, teléfono, horarios

#### ✅ Protocolo de Resolución:

**Paso 1:** Identifica el perfil "Principal"
- El que tiene más reseñas
- El que tiene verificación confirmada
- El que tiene más fotos

**Paso 2:** Documenta el perfil duplicado
- Toma screenshot del perfil duplicado
- Anota el Place ID si es posible
- Registra diferencias en datos NAP

**Paso 3:** Reporta a Google Business Profile
- Accede a Google Business Profile Manager
- Sección "Support" → "Report a problem"
- Selecciona "Duplicate listing"
- Adjunta evidencia (screenshots)
- **IMPORTANTE:** Esto puede tardar 5-7 días

**Paso 4:** Mientras tanto, optimiza el perfil principal
- No esperes resolución de Google
- Continúa con el resto del trabajo
- Marca en el sistema: `duplicate_reported: true`

**Paso 5:** Comunica al cliente (vía nota interna)
```
"Hemos detectado un perfil duplicado que diluye tu visibilidad. 
Hemos reportado el caso a Google (tiempo de resolución: 5-7 días). 
Mientras tanto, hemos optimizado tu perfil principal para 
maximizar tu posicionamiento."
```

#### ⏱️ Tiempo asignado: 5 minutos

---

### 2.2 Negocio Suspendido por Google

**Escenario:** El perfil de Google Maps está marcado como "Suspendido" o "Disabled".

#### 🔍 Razones comunes:

1. Violación de políticas de Google (negocio falso, spam)
2. Actividad sospechosa (cambios masivos en poco tiempo)
3. Reporte de usuarios (negocio cerrado, dirección falsa)
4. Problemas de verificación (no completó verificación postal/telefónica)

#### ✅ Protocolo de Resolución:

**Paso 1:** Identifica la causa
- Accede a Google Business Profile
- Revisa notificaciones/emails de Google
- Lee el motivo de suspensión

**Paso 2:** Clasifica el caso

**Caso A: Suspensión reversible (80% de casos)**
- Negocio legítimo con datos correctos
- Problema técnico o falso positivo
- **Acción:** Apelar la suspensión

**Caso B: Suspensión por violación real (20%)**
- Negocio no cumple políticas
- Datos fraudulentos
- **Acción:** No proceder, reembolsar al cliente

**Paso 3:** Apelación (Caso A)

1. Accede a Google Business Profile Support
2. Completa el formulario de reinstatement
3. Proporciona evidencia:
   - Registro mercantil del negocio
   - Foto de fachada con nombre visible
   - Recibo de servicios a nombre del negocio
   - Licencia comercial (si aplica)

**Paso 4:** Comunicación al cliente

```
"Tu perfil ha sido suspendido por Google. Hemos iniciado 
el proceso de apelación con evidencia sólida. Tiempo estimado 
de resolución: 7-14 días. Te mantendremos informado del progreso. 
Mientras tanto, hemos optimizado tus otros canales digitales 
(Facebook, Instagram) para mantener tu presencia online."
```

**Paso 5:** Trabajo alternativo (mientras se resuelve)

- Optimiza Facebook Business Page
- Optimiza Instagram Business Profile
- Asegura consistencia NAP en directorios (Yelp, TripAdvisor, etc.)

#### ⚠️ IMPORTANTE:
- **NO cobres el servicio completo** si la suspensión no se puede resolver
- Ofrece reembolso parcial (50%) por trabajo en otros canales
- Documenta todo el proceso en el CRM

#### ⏱️ Tiempo asignado: 15 minutos (+ seguimiento externo)

---

### 2.3 Reseña Extremadamente Tóxica o Falsa

**Escenario:** El negocio tiene una reseña de 1 estrella con contenido difamatorio, falso o inapropiado.

#### 🔍 Tipos de reseñas problemáticas:

1. **Reseña falsa:** Usuario nunca fue cliente
2. **Reseña de competidor:** Intento de sabotaje
3. **Reseña ofensiva:** Lenguaje violento, discriminatorio
4. **Reseña spam:** Publicidad de otro negocio

#### ✅ Protocolo de Resolución:

**Paso 1:** Evalúa si viola políticas de Google

Google permite reportar reseñas que:
- Contengan spam o estafas
- Incluyan conflictos de interés (competidores, empleados despedidos)
- Contengan lenguaje ofensivo, vulgar o de odio
- Sean fuera de tema (sobre otro negocio)
- Incluyan información personal privada

**Paso 2:** Reporta la reseña

1. Abre Google Maps
2. Localiza la reseña problemática
3. Click en los 3 puntos (⋮)
4. Selecciona "Reportar reseña"
5. Elige la categoría correcta
6. Proporciona contexto adicional si es posible

**Paso 3:** Respuesta pública estratégica

**IMPORTANTE:** Responde SIEMPRE, incluso a reseñas falsas. Tu respuesta es para futuros clientes, no para el reviewer.

**Plantilla para reseña falsa/competidor:**

```
Hola [Nombre], 

Revisamos nuestros registros y no encontramos ninguna visita 
o interacción con este nombre. Si realmente fuiste cliente, 
por favor contáctanos directamente a [email/teléfono] para 
resolver cualquier inconveniente.

Valoramos el feedback genuino de nuestros clientes y 
trabajamos constantemente para mejorar nuestro servicio.

Saludos,
[Nombre del Negocio]
```

**Plantilla para reseña legítima pero negativa:**

```
Hola [Nombre],

Lamentamos profundamente tu experiencia. Nos tomamos muy 
en serio cada comentario de nuestros clientes. 

Nos gustaría hablar contigo personalmente para entender 
qué salió mal y cómo podemos compensarte. Por favor 
contáctanos a [email/teléfono].

Estamos comprometidos con la excelencia y tu caso nos 
ayudará a mejorar.

Gracias por tu honestidad,
[Nombre del Negocio]
```

**Paso 4:** Dilución estratégica

Si la reseña no se puede eliminar:
1. Solicita reseñas positivas a clientes satisfechos
2. Aumenta volumen de reseñas para diluir el impacto
3. Monitorea si Google eventualmente la remueve

#### ⏱️ Tiempo asignado: 8 minutos

---

## 📸 SECCIÓN 3: ESTÁNDAR DE CONTENIDO VISUAL

### 3.1 Requisitos de Fotografía Premium

**Regla de oro:** CERO fotos de stock. Solo contenido auténtico.

#### ✅ Checklist de Calidad Fotográfica:

**Cantidad mínima:**
- 10 fotos para negocios locales (restaurantes, tiendas, oficinas)
- 15 fotos para negocios turísticos (hoteles, tours)
- 5 fotos para servicios profesionales (abogados, consultores)

**Categorías obligatorias:**

1. **Fachada/Exterior** (2 fotos mínimo)
   - Foto de día con buena iluminación
   - Foto del letrero/logo visible
   - Contexto de ubicación (calle, edificio)

2. **Interior** (3 fotos mínimo)
   - Área principal de atención al cliente
   - Productos/servicios en acción
   - Detalles distintivos del negocio

3. **Equipo/Staff** (2 fotos mínimo)
   - Foto del propietario o personal clave
   - Equipo trabajando (muestra profesionalismo)
   - **Importante:** Con consentimiento firmado

4. **Productos/Servicios** (3 fotos mínimo)
   - Productos bestsellers
   - Servicios en ejecución
   - Resultados finales (antes/después si aplica)

#### 🏷️ Geo-tagging Obligatorio

**Todas las fotos deben incluir:**

1. **Metadatos GPS exactos**
   - Latitud y longitud del negocio
   - Usar herramientas: Exif Editor, Google Photos

2. **Timestamp reciente**
   - No usar fotos con más de 12 meses
   - Excepto: fotos históricas del negocio (identificarlas)

3. **Formato optimizado**
   - Resolución: Mínimo 720p, ideal 1080p
   - Tamaño: Máximo 5MB por foto
   - Formato: JPG o HEIC

#### 🚫 PROHIBIDO:

❌ Fotos de stock (Shutterstock, Unsplash, etc.)  
❌ Fotos de otros negocios (incluso si son similares)  
❌ Capturas de pantalla  
❌ Fotos con marcas de agua de terceros  
❌ Fotos borrosas o pixeladas  
❌ Fotos con información personal visible (documentos, datos de clientes)

#### 🎨 Estándar de Edición:

**Permitido:**
- Ajuste de brillo/contraste (moderado)
- Corrección de color (natural)
- Recorte para encuadre

**NO permitido:**
- Filtros exagerados (estilo Instagram vintage)
- Photoshop de productos que distorsione realidad
- Agregar elementos que no existen

#### 📱 Herramientas Recomendadas:

- **Geo-tagging:** Geotag Photos Pro, Photo Exif Editor
- **Edición básica:** Google Photos, Snapseed, Lightroom Mobile
- **Compresión:** TinyPNG, JPEGmini

#### ⏱️ Tiempo asignado: 5 minutos (subida + geo-tagging)

---

## 🌍 SECCIÓN 4: GUÍA DE ESTILO MULTILINGÜE

### 4.1 Uso del AI Writer de Lokigi

Lokigi integra un motor de redacción que ayuda a crear descripciones naturales en **ES, PT y EN**. Tu trabajo es supervisar y pulir el output.

#### ✅ Protocolo de Redacción:

**Paso 1:** Recopila información del negocio

- Qué hace el negocio (servicios/productos)
- Qué lo hace único (propuesta de valor)
- Target audience (B2B, B2C, turistas, locales)
- Tono deseado (formal, casual, técnico)

**Paso 2:** Genera descripción base con AI Writer

**Prompt template para AI:**

```
Redacta una descripción de Google Business Profile para:

Negocio: [Nombre]
Categoría: [Tipo de negocio]
Ubicación: [Ciudad, País]
Servicios: [Lista de servicios/productos]
Diferenciador: [Qué los hace especiales]
Target: [Tipo de cliente]
Idioma: [ES/PT/EN]
Tono: [Profesional/Casual/Técnico]
Máximo: 750 caracteres

La descripción debe:
- Incluir llamado a la acción
- Mencionar ubicación geográfica
- Resaltar 2-3 beneficios clave
- Usar lenguaje natural (NO traducción literal)
- Incluir palabras clave de búsqueda local
```

**Paso 3:** Revisión y optimización manual

**Checklist de calidad:**

✅ **Naturalidad lingüística**
- Lee en voz alta. ¿Suena como un humano local?
- Evita frases como "Somos una empresa de..." (muy robótico)
- Usa contracciones en inglés: "We're", "You'll", "We've"

✅ **SEO Local**
- Incluye ciudad/barrio: "en el corazón de Palermo"
- Incluye servicios clave: "pizzería artesanal con horno de leña"
- Incluye palabras de búsqueda: "cerca de", "a 5 min de"

✅ **Llamado a la acción**
- "Visítanos", "Reserva tu mesa", "Llama ahora"
- Incluye horarios: "Abierto de lunes a sábado"
- Incluye incentivo: "Primera consulta gratis"

#### 🌐 Particularidades por idioma:

**Español (ES):**
- Usa "tú" (Latinoamérica) o "usted" (formal) según target
- Incluye regionalismos sutiles: "palta" (CL) vs "aguacate" (MX)
- Evita anglicismos innecesarios

**Portugués (PT-BR):**
- Usa "você" (coloquial) para B2C
- Incluye acentuación correcta: "é", "ã", "ç"
- Evita "tu" (Portugal) en negocios de Brasil

**Inglés (EN):**
- Tono casual para servicios locales: "Come grab a coffee!"
- Tono profesional para B2B: "Schedule a consultation today"
- Usa verbos de acción: "Discover", "Experience", "Transform"

#### 📝 Ejemplo de descripción Premium:

**❌ MAL (traducción literal):**
```
We are a company dedicated to the sale of handicraft products. 
We have 10 years of experience. Our products are of high quality. 
Visit us.
```

**✅ BIEN (natural y optimizado):**
```
Discover authentic handmade treasures in the heart of downtown! 
For 10 years, we've been crafting unique pieces that tell a story. 
From hand-woven textiles to artisan ceramics, every item is 
one-of-a-kind. Open Mon-Sat, 10am-7pm. Visit us at [Address] 
or shop online. Your perfect gift awaits! 🎁
```

#### 🎯 Longitud ideal:

- **Español:** 500-750 caracteres
- **Portugués:** 500-700 caracteres  
- **Inglés:** 450-650 caracteres

Google permite hasta 750, pero la legibilidad disminuye después de 600.

#### ⏱️ Tiempo asignado: 7 minutos (generación + revisión + publicación)

---

## ✅ SECCIÓN 5: CHECKLIST DE "CERO ERRORES"

### 5.1 Verificación Final Pre-Entrega

**NUNCA marques una orden como "Completada" sin revisar estos 25 puntos.**

#### 📋 CHECKLIST MASTER:

**A. DATOS NAP (Name, Address, Phone)**

- [ ] Nombre del negocio escrito correctamente (sin typos)
- [ ] Dirección completa y verificada en Google Maps
- [ ] Código postal correcto
- [ ] Teléfono con formato internacional correcto (+52, +54, +55, etc.)
- [ ] Horarios de atención actualizados (incluir días festivos si aplica)
- [ ] Sitio web funcional (verificar que carga)
- [ ] Email de contacto verificado

**B. CONTENIDO VISUAL**

- [ ] Mínimo 10 fotos subidas (5 para servicios profesionales)
- [ ] Todas las fotos tienen geo-tag correcto
- [ ] Fotos con resolución mínima 720p
- [ ] Sin fotos de stock o de terceros
- [ ] Foto de perfil (logo o fachada) configurada
- [ ] Foto de portada configurada (si aplica)

**C. DESCRIPCIÓN Y CONTENIDO**

- [ ] Descripción de negocio completa (500+ caracteres)
- [ ] Idioma correcto según ubicación del negocio
- [ ] Sin errores gramaticales o typos
- [ ] Incluye palabras clave de búsqueda local
- [ ] Incluye llamado a la acción
- [ ] Categoría principal correcta
- [ ] Categorías secundarias agregadas (máx 9)

**D. ATRIBUTOS Y CARACTERÍSTICAS**

- [ ] Atributos de negocio seleccionados (accesibilidad, WiFi, parking, etc.)
- [ ] Métodos de pago actualizados
- [ ] Servicios/Productos listados (mínimo 5)
- [ ] Preguntas frecuentes agregadas (mínimo 3)

**E. CASOS ESPECIALES**

- [ ] Si hubo perfil duplicado: documentado y reportado
- [ ] Si hubo suspensión: proceso de apelación iniciado
- [ ] Si hubo reseñas tóxicas: reportadas y respondidas
- [ ] Si requiere verificación: método de verificación iniciado

**F. REPORTE AL CLIENTE**

- [ ] Screenshot del perfil "Antes" guardado
- [ ] Screenshot del perfil "Después" guardado
- [ ] Score de visibilidad "Antes" documentado
- [ ] Score de visibilidad "Después" calculado
- [ ] Diferencia de score ≥ 15 puntos (meta mínima)
- [ ] Reporte de éxito generado en el sistema

#### 🎯 Validación de Impacto:

**Antes de marcar "Completado", verifica:**

| Métrica | Mínimo Esperado |
|---------|-----------------|
| Score de Mejora | +15 puntos |
| Fotos agregadas | +8 fotos |
| Completitud del perfil | 90%+ |
| Tiempo de trabajo | 15-25 min |

Si **NO cumples** alguna de estas métricas:
1. Revisa qué faltó
2. Completa los items pendientes
3. Recalcula el impacto
4. Solo entonces marca como completado

#### ⏱️ Tiempo asignado: 3 minutos (revisión final)

---

## 📊 SECCIÓN 6: MÉTRICAS DE ÉXITO Y KPIs

### 6.1 Cómo se mide tu desempeño

El sistema de Command Center trackea tu performance en tiempo real. Así es como te evalúan:

#### 🎯 KPIs Principales:

**1. Efficiency Score (0-100)**

Fórmula: `(Speed Score × 0.6) + (Quality Score × 0.4)`

- **Speed Score:** Basado en tiempo de entrega
  - < 15 min = 100 puntos
  - 15-20 min = 90 puntos
  - 20-25 min = 80 puntos
  - 25-30 min = 70 puntos
  - > 30 min = 60 puntos

- **Quality Score:** Basado en score de mejora
  - Mejora > 20 puntos = 100 puntos
  - Mejora 15-20 = 90 puntos
  - Mejora 10-15 = 80 puntos
  - Mejora < 10 = 70 puntos

**2. Completion Rate**

- Órdenes completadas / Órdenes asignadas
- Meta: 95%+ mensual

**3. Average Score Improvement**

- Promedio de mejora de score de visibilidad
- Meta: 18+ puntos

**4. Client Satisfaction**

- Basado en quejas/retrabajos
- Meta: 0 quejas

#### 🏆 Sistema de Rankings:

El dashboard muestra un ranking público de workers. Tu posición determina:

- **Top 3:** Bonos mensuales + Primeras órdenes asignadas
- **Posiciones 4-10:** Performance estándar
- **Bottom 3:** Revisión de proceso + Capacitación adicional

#### 📈 Cómo mejorar tu ranking:

1. **Velocidad:** Usa templates y automatizaciones
2. **Calidad:** Sigue el checklist al 100%
3. **Consistencia:** Mantén mismo nivel en todas las órdenes
4. **Proactividad:** Reporta mejoras en el sistema

---

## 🚀 SECCIÓN 7: HERRAMIENTAS Y RECURSOS

### 7.1 Stack tecnológico del Worker

**Acceso a plataformas:**

1. **Lokigi Dashboard** (dashboard.lokigi.com)
   - Tu panel de órdenes asignadas
   - Upload de fotos y reportes
   - Comunicación con clientes

2. **Google Business Profile Manager**
   - Gestión de perfiles de clientes
   - Acceso delegado via email

3. **AI Writer de Lokigi** (integrado en dashboard)
   - Generación de descripciones
   - Traducción multilingüe
   - Optimización SEO

**Recursos de consulta:**

- [Google Business Profile Guidelines](https://support.google.com/business/answer/3038177)
- [Lokigi Knowledge Base](https://kb.lokigi.com) (interno)
- Canal de Slack: #workers-support

### 7.2 Flujo de trabajo optimizado

**20 minutos cronometrados:**

| Minuto | Actividad |
|--------|-----------|
| 0-2 | Leer reporte de auditoría + Priorizar |
| 2-5 | Acceder a Google Business Profile |
| 5-8 | Actualizar datos NAP + Categorías |
| 8-12 | Subir y geolabelar fotos (10+) |
| 12-17 | Redactar y publicar descripción |
| 17-19 | Agregar atributos, productos, FAQs |
| 19-20 | Checklist final + Marcar completado |

**Uso de templates para velocidad:**

- Descripción base por tipo de negocio
- Respuestas a reseñas por escenario
- Atributos comunes por categoría

---

## 💡 SECCIÓN 8: CASOS DE USO REALES

### Ejemplo 1: Restaurante con score 38

**Cliente:** "La Parrilla del Sur" - Buenos Aires, AR  
**Score inicial:** 38/100  
**Problema principal:** Descripción vacía, solo 2 fotos, sin horarios

**Tu trabajo (18 minutos):**

1. **(Min 0-2)** Lees reporte: fallo crítico = descripción vacía ($320/mes)
2. **(Min 2-5)** Accedes a GBP, verificas datos NAP correctos
3. **(Min 5-8)** Solicitas al cliente 10 fotos vía WhatsApp (fachada, parrilla, platos)
4. **(Min 8-12)** Subes fotos con geo-tag de coordenadas del restaurante
5. **(Min 12-17)** Generas descripción con AI Writer:
   ```
   Auténtica parrilla argentina en el corazón de Palermo. 
   Cortes premium, parrilleros con 20 años de experiencia, 
   y el mejor chimichurri de la zona. Reservá tu mesa para 
   almuerzo o cena. Abierto Mar-Dom, 12pm-11pm. 
   ¡Te esperamos con las brasas encendidas! 🥩
   ```
6. **(Min 17-19)** Agregas atributos: WiFi, Estacionamiento, Accesible, Acepta Tarjetas
7. **(Min 19-20)** Checklist: ✅ Todo OK. Marcas completado.

**Resultado:** Score final 61/100 (+23 puntos) ✅

---

### Ejemplo 2: Consultorio médico con perfil duplicado

**Cliente:** "Dra. Silva - Dermatología" - São Paulo, BR  
**Score inicial:** 51/100  
**Problema principal:** Perfil duplicado + Descripción en inglés (error)

**Tu trabajo (23 minutos):**

1. **(Min 0-3)** Lees reporte: fallo crítico = perfil duplicado ($850/mes)
2. **(Min 3-8)** Identificas 2 perfiles, el principal tiene 42 reseñas, el duplicado 3
3. **(Min 8-10)** Reportas perfil duplicado a Google, documentas con screenshots
4. **(Min 10-14)** Optimizas perfil principal: corriges descripción a portugués brasileño
   ```
   Clínica de dermatologia especializada em tratamentos estéticos 
   e clínicos. Dra. Silva possui 15 anos de experiência em 
   dermatologia oncológica e rejuvenescimento facial. 
   Atendimento humanizado e tecnologia de ponta. 
   Agende sua consulta: (11) 9xxxx-xxxx
   ```
5. **(Min 14-18)** Subes 8 fotos: consultório, equipamentos, Dra. Silva atendendo
6. **(Min 18-21)** Agregas servicios: Botox, Peeling, Tratamento de Acne, etc.
7. **(Min 21-23)** Checklist + Nota interna sobre perfil duplicado reportado

**Resultado:** Score final 68/100 (+17 puntos) + Duplicado en proceso ✅

---

## 🔐 SECCIÓN 9: SEGURIDAD Y CONFIDENCIALIDAD

### 9.1 Manejo de datos sensibles

**NUNCA compartas:**

- Credenciales de acceso de clientes
- Datos financieros (facturación, ventas)
- Información personal de clientes finales (nombres, teléfonos)
- Screenshots con información confidencial

**SIEMPRE:**

- Usa el sistema de Lokigi para comunicación
- Difumina datos sensibles en screenshots
- Cierra sesión de Google Business Profile después de trabajar
- Reporta accesos sospechosos

### 9.2 Política de no competencia

Está **PROHIBIDO**:

- Contactar clientes de Lokigi fuera del sistema
- Ofrecer servicios similares de forma independiente
- Compartir metodología de Lokigi con terceros
- Usar información de clientes para beneficio personal

**Penalización:** Terminación inmediata + Acciones legales

---

## 📞 SECCIÓN 10: SOPORTE Y ESCALAMIENTO

### 10.1 ¿Cuándo pedir ayuda?

**Escala a supervisor si:**

- Cliente solicita reembolso
- Suspensión de perfil que no puedes resolver
- Cliente reporta problema de calidad de tu trabajo
- No puedes acceder a Google Business Profile del cliente
- Caso técnico complejo fuera de este manual

**Canal de soporte:**

- Slack: #workers-support (respuesta en < 1 hora)
- Email: workers@lokigi.com (respuesta en < 4 horas)
- Emergencias: WhatsApp del supervisor (solo casos críticos)

**Qué incluir en tu consulta:**

1. Order ID
2. Descripción del problema
3. Screenshots (si aplica)
4. Qué ya intentaste resolver

---

## 🎓 SECCIÓN 11: CAPACITACIÓN CONTINUA

### 11.1 Actualizaciones de Google

Google actualiza sus políticas regularmente. Mantente informado:

- **Google Business Profile Help Center:** Revisa 1 vez por semana
- **Lokigi Newsletter:** Se envía cada lunes con cambios relevantes
- **Sesión mensual:** Call obligatorio con equipo de Operations

### 11.2 Certificaciones recomendadas

- Google Digital Garage: Local Business Marketing
- SEO básico: Moz, SEMrush Academy
- Google Ads (básico): Google Skillshop

---

## ✅ CONCLUSIÓN

Este manual es tu **Biblia operativa**. Todo lo que necesitas para entregar servicios Premium está aquí.

**Recuerda:**

1. **Eficiencia:** 20 minutos promedio
2. **Calidad:** +15 puntos de score mínimo
3. **Cero errores:** Usa el checklist SIEMPRE
4. **Autonomía:** Consulta el manual antes de preguntar

**Tu éxito = Éxito del cliente = Éxito de Lokigi**

¡Ahora a optimizar! 🚀

---

**Versión:** 1.0  
**Próxima revisión:** Marzo 2026  
**Feedback:** workers-feedback@lokigi.com
