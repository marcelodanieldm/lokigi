# Certificado de Éxito Lokigi (Impact Report)

## Objetivo
Diseñar un reporte PDF/Web que el cliente quiera imprimir y colgar en su oficina o compartir en LinkedIn.

## Implementación

### 1. Visualización de Impacto
- **Medidor de Score gigante**: Se implementa con `GaugeChart.tsx` usando canvas y gradiente de Rojo a Verde Neón.
- **Estética**: Fondo oscuro (`bg-gray-950`), tipografía técnica (`font-mono`), acentos en verde neón (`#39FF14`).

### 2. Layout de Contenido
- **Secciones**:
  - Mejoras Realizadas
  - Fotos Optimizadas con Geo-tag
  - Ranking de Competencia Actualizado
- **Componente**: `ImpactReport.tsx` (Tailwind CSS, visual limpio y ejecutivo).

### 3. The Hook (Suscripción)
- **Sección 'Tu Radar de Protección'**: Muestra un gráfico radar (react-chartjs-2) con escenarios de reacción de la competencia.

### 4. Exportación a PDF
- **next-pdf**: Se usa `@react-pdf/renderer` para exportar el reporte a PDF desde `/impact-report`.
- El PDF replica la estética y estructura del reporte web.
- El gráfico radar se exporta como imagen base64.

### 5. Uso
- Accede a `/impact-report` para ver y descargar el certificado personalizado.
- El botón "Descargar PDF" genera el reporte listo para imprimir o compartir.

## Archivos Clave
- `frontend/src/app/components/ImpactReport.tsx`: Renderiza el reporte web.
- `frontend/src/app/components/GaugeChart.tsx`: Medidor de Score visual.
- `frontend/src/app/impact-report/page.tsx`: Página y lógica de exportación PDF.

## Personalización
- Todos los datos (score, mejoras, fotos, ranking, radar) son parametrizables vía props o query params.

## Ejemplo Visual
![Ejemplo Impact Report](../public/demo/impact_report_example.png)

---

**Recomendación UX:**
- Imprime el PDF en alta calidad o compártelo en LinkedIn para mostrar el éxito de tu negocio con Lokigi.
