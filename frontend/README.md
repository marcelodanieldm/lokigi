# Lokigi Frontend - Página de Resultados de Auditoría 🎨

Dashboard de auditoría SEO Local construido con Next.js 14, TypeScript y Tailwind CSS.

## 🎯 Características

- ✅ **Gráfico circular animado** con Score de Salud Local (Recharts)
- ✅ **Puntos Críticos** con iconos vibrantes y alertas rojas
- ✅ **Tabla comparativa** Tú vs. Competencia con colores dinámicos
- ✅ **CTA Card premium** - Oferta de $9 con diseño llamativo
- ✅ **Responsive** - Perfecto en móvil y desktop
- ✅ **Animaciones fluidas** - Hover effects y transiciones
- ✅ **TypeScript** - Type-safe components

## 🚀 Instalación

```bash
cd frontend
npm install
```

## 💻 Desarrollo

```bash
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000) en tu navegador.

## 🏗️ Estructura del Proyecto

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # Layout principal
│   │   ├── page.tsx         # Página home
│   │   └── globals.css      # Estilos globales
│   └── components/
│       ├── AuditResults.tsx      # Componente principal
│       ├── HealthScoreChart.tsx  # Gráfico circular
│       ├── CriticalPoints.tsx    # Lista de fallos
│       ├── ComparisonTable.tsx   # Tabla comparativa
│       └── CTACard.tsx           # Card de conversión
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

## 🎨 Componentes

### HealthScoreChart
Gráfico circular animado que muestra el score de salud de 0-100 con colores dinámicos:
- 🔴 Rojo (0-39): Crítico
- 🟠 Naranja (40-69): Mejorable  
- 🟢 Verde (70-100): Excelente

### CriticalPoints
Tarjetas de fallos críticos con:
- Iconos de Lucide React
- Numeración visual
- Impacto económico destacado
- Total de pérdidas mensual

### ComparisonTable
Tabla comparativa con:
- Métricas clave (Score, reseñas, rating, fotos, etc.)
- Colores para ganador/perdedor
- Cálculo automático de diferencias
- Responsive en móvil

### CTACard
Card de conversión premium con:
- Gradientes vibrantes
- Precio destacado ($9)
- Lista de beneficios
- Stats de resultados
- Social proof

## 🎨 Paleta de Colores

```css
Alertas:
- Crítico: #ef4444 (Rojo)
- Alto: #f59e0b (Naranja)
- Medio: #f59e0b (Amarillo)

Acciones:
- Primario: Gradiente Red → Orange
- Éxito: #22c55e (Verde)
- Info: #3b82f6 (Azul)
```

## 🔌 Integración con Backend

Para conectar con el backend de FastAPI:

```typescript
// En producción, reemplaza los datos simulados con:
const response = await fetch('http://localhost:8000/audit/test');
const data = await response.json();
```

## 📦 Build para Producción

```bash
npm run build
npm start
```

## 🚢 Deploy

### Vercel (Recomendado)
```bash
npm install -g vercel
vercel
```

### Otras opciones
- Netlify
- AWS Amplify
- Docker + Nginx

## 📝 Próximas Mejoras

- [ ] Animaciones avanzadas con Framer Motion
- [ ] Dark mode
- [ ] Exportar reporte a PDF
- [ ] Comparativa con múltiples competidores
- [ ] Panel de seguimiento de mejoras

## 🛠️ Tecnologías

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **Recharts** - Gráficos React
- **Lucide React** - Iconos modernos

---

Made with ❤️ for Lokigi
