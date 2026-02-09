# Auditoría AI con Gemini: Estrategia y Documentación

## Estrategia de Dirección
Se utiliza Prompt Engineering avanzado sobre la API de Gemini (Google Generative AI, capa gratuita). El prompt no pide "consejos" sino una auditoría bajo estándares de conversión de marketing local, con contexto de negocio enriquecido.

- **System Prompt:**
  - Rol: "Eres un experto en Growth Hacking para negocios locales. Tu tono es directo, profesional y enfocado en el retorno de inversión (ROI). No des consejos obvios."
  - Contexto enviado: rubro, competencia, fallo crítico, país.
  - Multilingüe: Si el país es Brasil, responde en portugués nativo con jerga empresarial local.

- **Estructura de la respuesta:**
  - QuickWin: Acción de 5 minutos que suba el ranking hoy.
  - StrategicGap: Por qué la competencia le está robando clientes.
  - TechnicalFix: Ajuste técnico (NAP o Geo-tagging) necesario.

## Ejemplo de Uso del Endpoint

### Request
POST `/audit/gemini_prompt`

```json
{
  "score": 68,
  "rubro": "Peluquería",
  "competencia": "3 locales en un radio de 1km con 4.5 estrellas",
  "fallo": "No tiene fotos de los trabajos realizados (Social Proof)",
  "pais": "BR",
  "lang": "pt"
}
```

### Respuesta esperada
```json
{
  "QuickWin": "Publique imediatamente 3 fotos de cortes recentes no Google Meu Negócio.",
  "StrategicGap": "Seus concorrentes estão mostrando resultados reais, gerando mais confiança e atraindo novos clientes.",
  "TechnicalFix": "Adicione geotagging nas fotos e garanta que o NAP esteja consistente em todos os diretórios."
}
```

## Detalles Técnicos
- El backend utiliza la librería `google-generativeai` y requiere la variable de entorno `GEMINI_API_KEY`.
- El prompt y contexto se construyen dinámicamente según el input del usuario.
- El endpoint está documentado en el código fuente (`main.py`).

## Notas
- Si la API Key no está configurada, el endpoint devuelve un error informativo.
- El output es siempre un JSON con las tres claves solicitadas.
- El endpoint es fácilmente extensible para otros rubros y países.

---

Para más detalles, ver la implementación en `backend/main.py` y `backend/alert_radar.py`.
