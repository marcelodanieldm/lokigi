# Visualización de Dominance Index en Frontend

## Integración
- El dashboard premium ahora muestra el Dominance Index y el Competidor Amenaza en la parte superior.
- Los datos se obtienen del endpoint `/api/dominance-index` (proxy al backend).
- El heatmap puede ser visualizado usando los datos de `heatmap` para futuras mejoras.

## Ejemplo visual

```
Dominance Index
  41.2%
Amenaza: Barberia Lisboa

[Mapa interactivo]
[Feed de alertas]
[ROI Tracker]
```

## Código relevante
Ver `frontend/src/app/dashboard/premium/page.tsx` y `PremiumControlTower.tsx`.

## Notas
- El Dominance Index se actualiza automáticamente al cargar el dashboard.
- El color y formato siguen la estética dark mode con neón verde.
- Para personalizar el heatmap, usar la clave `heatmap` del endpoint.

---

Para ampliar la visualización, se recomienda integrar la capa de calor en el mapa de Leaflet.
