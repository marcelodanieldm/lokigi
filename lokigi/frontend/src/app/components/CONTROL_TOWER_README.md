# Premium Customer Dashboard: Control Tower

## Objetivo
Interfaz adictiva y mobile-first para clientes premium de Lokigi, mostrando el estado de la "guerra local" en tiempo real.

## Componentes Clave

### 1. Visualización Central: Heatmap
- Componente `MapHeatmap.tsx` (Leaflet + Tailwind):
  - Muestra puntos de visibilidad.
  - Verde: dominio del cliente. Rojo: dominio de la competencia.
  - Mobile-first, dark mode, acentos neón.

### 2. Sección de Alertas
- Feed tipo muro de noticias con las alertas generadas por el motor de Data Science.
- Visual destacado, con tipo de alerta y nombre del competidor.

### 3. ROI Tracker
- Widget que muestra el "Dinero Protegido este mes" (lucro cesante evitado).
- Visual central, acento verde neón.

### 4. Estética
- Dark mode absoluto (`bg-gray-950`), tipografía técnica (`font-mono`), acentos en verde neón (`#39FF14`).
- Inspiración: centro de inteligencia militar, pero amigable para pizzerías y clínicas.

## Ejemplo de Uso

```tsx
import PremiumControlTower from "../components/PremiumControlTower";

<PremiumControlTower
  visibilityPoints={[
    { lat: -34.6, lon: -58.4, dominance: "client" },
    { lat: -34.61, lon: -58.41, dominance: "competitor" }
  ]}
  alerts={[
    { alert: "Competidor A ha subido 10 fotos nuevas", type: "photos", competitor: "Competidor A" }
  ]}
  roi={1200}
  currency="USD"
/>
```

## Dependencias
- `react-leaflet`, `leaflet` para el mapa interactivo.
- Tailwind CSS para estilos.

---

**UX/UI Designer: Dashboard validado y listo para producción.**
