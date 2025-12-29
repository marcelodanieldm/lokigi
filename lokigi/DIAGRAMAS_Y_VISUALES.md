# Diagramas de Flujo y Ejemplos Visuales

## 1. Diagrama de Flujo General del Sistema

```mermaid
graph TD
    A[Usuario] -->|Login/Registro| B[Frontend Next.js]
    B -->|Auth| C[Supabase Auth]
    B -->|Solicita datos| D[Backend FastAPI]
    D -->|Consulta| E[Supabase DB]
    D -->|Procesa| F[Motor de Alertas/Proyección]
    D -->|Webhook| G[Stripe]
    B -->|Muestra| H[Dashboard/Reportes]
```

---

## 2. Flujo de Generación de Reporte de Impacto

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend
    participant BE as Backend
    U->>FE: Solicita Impact Report
    FE->>BE: POST /impact-report
    BE->>BE: Procesa métricas y genera PDF
    BE-->>FE: Devuelve reporte
    FE-->>U: Muestra/descarga reporte
```

---

## 3. Flujo de Alertas Competitivas

```mermaid
sequenceDiagram
    participant Cron as Tarea Programada
    participant BE as Backend
    participant DB as Supabase
    participant FE as Frontend
    Cron->>BE: Trigger mensual
    BE->>DB: Obtiene snapshots de competidores
    BE->>BE: Analiza cambios y genera alertas
    BE->>DB: Guarda alertas
    FE->>DB: Consulta alertas
    DB-->>FE: Devuelve alertas
    FE-->>Usuario: Muestra alertas en dashboard
```

---

## 4. Ejemplo Visual de Dashboard Premium

![Ejemplo Dashboard Premium](https://raw.githubusercontent.com/marcelodanieldm/lokigi/main/docs/dashboard_ejemplo.png)

*Nota: Puedes reemplazar la URL por una imagen propia del dashboard si la tienes.*

---

## 5. Recomendaciones para Diagramas
- Usa Mermaid para diagramas de flujo y secuencia en Markdown.
- Usa herramientas como Lucidchart, Whimsical o Figma para diagramas visuales avanzados.
- Guarda imágenes de ejemplo en la carpeta `docs/` y enlázalas en la documentación.

---

Este archivo puede ampliarse con más diagramas y ejemplos visuales según evolucione el sistema.
