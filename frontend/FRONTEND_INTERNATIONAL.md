# 🌍 Frontend Internacional - Dark Cyber Theme

## Implementado ✅

Landing page profesional con tema oscuro, detección automática de idioma y UX de "gancho" para captura de leads.

---

## 🎨 Diseño Cyber/Tech

### Tema Visual
- **Paleta de Colores:**
  - Fondo: Negro profundo (#0a0a0a, #121212)
  - Acento primario: Verde neón (#00ff41)
  - Acentos secundarios: Cyan cyber (#00d9ff), Púrpura (#b300ff)
  - Texto: Grises (#f3f4f6, #9ca3af)

- **Tipografía:**
  - Sans: Inter (UI general)
  - Mono: JetBrains Mono (elementos técnicos, código)

- **Efectos:**
  - Glow en textos importantes
  - Grid pattern de fondo sutil
  - Scanning line animations
  - Blur/backdrop-blur para profundidad
  - Gradientes radiales para orbs

### Componentes Principales

#### 1. **HeroSection** (`/components/HeroSection.tsx`)
- Headline con auto-detect de idioma
- Input de búsqueda con efecto neon border
- Grid de 3 features principales
- Social proof badge animado
- Orbs de gradiente animados en background

#### 2. **AnalysisLoader** (`/components/AnalysisLoader.tsx`)
- Animación de radar/scanner circular
- 5 etapas de carga con checkmarks progresivos
- Barra de progreso con gradiente neon
- Scanning line effect
- Texto técnico estilo "espionaje industrial"

#### 3. **LeadCaptureFormModal** (`/components/LeadCaptureFormModal.tsx`)
- Modal full-screen con backdrop blur
- Ícono de alerta animado con pulse
- Campos de formulario con efecto glow on focus
- Privacy badge
- CTA con loading state

---

## 🌐 i18n Automático

### Hook: `useLanguageDetection`
**Archivo:** `/hooks/useLanguageDetection.ts`

**Lógica de Detección:**
1. **Browser Language** (más rápido) - `navigator.languages`
2. **Backend IP Detection** - Header `X-Detected-Language`
3. **Default** - Inglés si fallan los anteriores

**Mapeo de Idiomas:**
```typescript
pt-BR, pt-PT → pt (Portugués)
es-ES, es-MX, es-AR, es-CO, es-CL → es (Español)
en-US, en-GB → en (Inglés)
```

### Traducciones: `translations.ts`
**Archivo:** `/lib/translations.ts`

**30+ keys traducidas:**
- Hero section (headline, subheadline, CTA, trust badge)
- Business input (placeholder, analyzing)
- Loading stages (5 mensajes técnicos)
- Lead form (título, campos, privacidad, submit)
- Features (3 features × title + description)
- Social proof
- Footer tagline

**Uso:**
```typescript
const { t } = useTranslations(language);
<h1>{t('hero.headline')}</h1>
```

---

## 🎯 Flujo de Conversión (UX de "Gancho")

### Estado de Flujo
```typescript
type FlowState = 'hero' | 'analyzing' | 'leadCapture';
```

### Paso 1: Hero
- Usuario ve headline en su idioma nativo
- Input para nombre del negocio
- CTA: "Analizar Mi Negocio Gratis"

### Paso 2: Analyzing (2-10 segundos)
- Full-screen loader con animación de radar
- 5 etapas de análisis con mensajes técnicos:
  - 🔍 Analizando visibilidad en radio de 2km...
  - 🎯 Comparando con 47 competidores locales...
  - ⭐ Escaneando reputación online...
  - 📸 Auditando galería de fotos...
  - 📊 Calculando lucro cesante...
- Progress bar 0-100%
- Sensación de "herramienta de espionaje"

### Paso 3: Lead Capture
- Modal con alerta "⚠️ Problemas Críticos Detectados"
- Formulario simple: Email (required) + WhatsApp (optional)
- Submit → POST a `/api/leads` → Redirect a `/audit/{id}`

---

## 📂 Archivos Creados/Modificados

### Nuevos:
- ✅ `/hooks/useLanguageDetection.ts` (~140 líneas)
- ✅ `/lib/translations.ts` (~180 líneas)
- ✅ `/components/HeroSection.tsx` (~120 líneas)
- ✅ `/components/AnalysisLoader.tsx` (~140 líneas)
- ✅ `/components/LeadCaptureFormModal.tsx` (~130 líneas)

### Modificados:
- ✅ `tailwind.config.ts` - Tema oscuro + colores neon
- ✅ `globals.css` - Estilos cyber (card, btn, input, scanner, glow)
- ✅ `app/page.tsx` - Orquestador del flujo de conversión
- ✅ `app/layout.tsx` - Metadata + Google Fonts (Inter, JetBrains Mono)

---

## 🚀 Variables de Entorno

Agregar a `.env.local` del frontend:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Para producción en Vercel:
```bash
NEXT_PUBLIC_API_URL=https://api.lokigi.com
```

---

## 🎨 Clases CSS Destacadas

### Botones
```tsx
.btn-primary    // Neon green solid button
.btn-secondary  // Ghost button con border neon
```

### Cards
```tsx
.card          // Dark card con border sutil
.card-hover    // + Hover effects (glow, translate)
```

### Inputs
```tsx
.input-cyber   // Dark input con focus:neon border
```

### Efectos
```tsx
.text-neon-glow     // Text con shadow glow
.scanner-line       // Línea de escaneo animada
.grid-background    // Grid pattern sutil
```

---

## 🌍 Soporte de Idiomas

| País | Idioma | Código | Browser Detection |
|------|--------|--------|-------------------|
| 🇧🇷 Brasil | Português | `pt` | pt-BR, pt-PT |
| 🇦🇷 Argentina | Español | `es` | es-AR |
| 🇲🇽 México | Español | `es` | es-MX |
| 🇨🇴 Colombia | Español | `es` | es-CO |
| 🇨🇱 Chile | Español | `es` | es-CL |
| 🇪🇸 España | Español | `es` | es-ES |
| 🇺🇸 USA | English | `en` | en-US |
| 🇬🇧 UK | English | `en` | en-GB |

---

## 📊 Métricas de UX

### Tiempo de Carga Simulado
- Hero → Input: 0s (instantáneo)
- Input → Analysis: 0.5s (transición)
- Analysis: 10s (5 stages × 2s)
- Analysis → Lead Form: 1s (fade)
- Total: ~11.5s hasta captura de lead

### Puntos de Fricción Minimizados
1. ❌ No hay selector de idioma manual
2. ❌ No hay pasos innecesarios
3. ✅ Solo 1 input en hero (nombre del negocio)
4. ✅ Solo 2 inputs en lead form (email + phone opcional)
5. ✅ Loading tiene propósito (genera expectativa)

---

## 🔧 Próximos Pasos

### Testing:
1. Instalar dependencias: `cd frontend && npm install`
2. Configurar `.env.local` con `NEXT_PUBLIC_API_URL`
3. Correr dev server: `npm run dev`
4. Abrir: http://localhost:3000

### Deploy en Vercel:
```bash
cd frontend
vercel --prod
```

Configurar en Vercel Dashboard:
- Environment Variable: `NEXT_PUBLIC_API_URL=https://api.lokigi.com`
- Build Command: `npm run build`
- Output Directory: `.next`

---

**Resultado:** Landing profesional estilo "herramienta de espionaje" para PYMES, con detección automática de idioma (PT/ES/EN) y flujo de conversión optimizado para captura de leads sin fricción.
