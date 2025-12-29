# Partnerships & White-Label Admin Dashboard

## Indicadores de "Poder de Red"
- **Active Affiliates:** Número de socios con al menos 1 lead esta semana.
- **EPC (Earnings Per Click):** Promedio de ingresos por clic de afiliado.
- **Affiliate Revenue vs. Direct Revenue:** Comparativa de ingresos por canal.

## White-Label para Agencias
- Permite a agencias grandes personalizar el dashboard y reportes con su logo y colores.
- El Branding Engine usa Tailwind CSS y variables CSS para temas dinámicos.
- El reporte PDF/Web puede mostrar el logo de la agencia en vez del de Lokigi.

## Componentes
- `PartnershipsDashboard.tsx`: Vista principal de partnerships y white-label.
- `partnershipsMetrics.ts`: Lógica de métricas (simulada, conectar a backend real).
- `BrandingEngine.tsx`: UI para subir logo y elegir color primario.
- `WhiteLabelReport.tsx`: Reporte PDF/Web con branding de agencia.

## UX/UI
- Estética neutra, adaptable a cualquier marca (azul, rojo, verde, etc).
- El color y logo se aplican en tiempo real usando CSS Variables.
- El sistema es extensible para futuras fases B2B.

## Cómo usar
1. Integra los componentes en el panel de admin.
2. Conecta `partnershipsMetrics.ts` a tu backend real.
3. Usa `BrandingEngine` para permitir a la agencia personalizar su branding.
4. Usa `WhiteLabelReport` para generar reportes con el logo y color de la agencia.

---

> **Nota:** Este sistema está preparado para la fase de white-label y el mercado B2B. El diseño es limpio y eficiente, y puede adaptarse a cualquier identidad visual de agencia.
