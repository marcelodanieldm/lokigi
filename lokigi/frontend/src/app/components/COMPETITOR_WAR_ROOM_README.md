# Competitor War Room: Visualización de la Zona de Peligro

## Objetivo
Componente visual para cerrar la venta premium ($99):
- Mapa minimalista dark mode.
- Punto rojo parpadeante (cliente), puntos verdes sólidos (competidores).
- Copy dinámico multilingüe.
- Radar chart ultra liviano (SVG puro, sin librerías pesadas).

## Props principales
- `client`: posición del cliente en el mapa (x, y)
- `competitors`: lista de competidores (x, y)
- `radar`: datos de fortalezas vs debilidades
- `lang`: idioma ('es', 'pt', 'en')

## Ejemplo de uso
```tsx
<CompetitorWarRoom
  client={{ x: 120, y: 120 }}
  competitors={[
    { x: 60, y: 80 },
    { x: 180, y: 100 },
    { x: 100, y: 180 }
  ]}
  radar={{
    labels: ["Reputación", "SEO", "Visual", "NAP"],
    client: [80, 60, 70, 90],
    competitor: [90, 80, 85, 95]
  }}
  lang="es"
/>
```

## Copy dinámico
- ES: "Esta es tu zona de pérdida de clientes"
- PT: "Esta é a sua zona de perda de clientes"
- EN: "This is your customer loss zone"

## Interactividad
- El radar chart compara fortalezas y debilidades de forma visual y ligera.
- El mapa puede ampliarse para mostrar áreas de influencia reales.

## Estilo
- 100% Tailwind CSS, dark mode, neón verde y rojo.
- Sin dependencias pesadas.

---

Ver implementación en `frontend/src/app/components/CompetitorWarRoom.tsx`.
