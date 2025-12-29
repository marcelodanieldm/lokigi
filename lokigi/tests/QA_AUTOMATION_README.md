# QA Automation: Validador Global de Inteligencia

Este módulo implementa una suite de pruebas automatizadas para validar el "sentido común" y la robustez de la IA de Lokigi en diferentes culturas y escenarios de negocio.

## Objetivo
Asegurar que la lógica de negocio y la localización de la IA funcionen correctamente en distintos países y que el despliegue mantenga altos estándares de performance.

## Herramientas
- **Pytest**: Framework de testing para Python.
- **Playwright**: Automatización de navegador para pruebas end-to-end y performance.
- **Lighthouse (npx)**: Auditoría de performance web.

## Pruebas Incluidas

### 1. Test de Consistencia
- **Propósito:** Verificar que el 'Lucro Cesante' nunca sea negativo.
- **Lógica:** Simula una auditoría y comprueba que el campo `lucro_cesante` en la respuesta de la API sea siempre mayor o igual a cero.

### 2. Test de Localización
- **Propósito:** Validar que la moneda y el ticket promedio cambian correctamente según la localización.
- **Lógica:**
  - Simula una auditoría en San Pablo (Brasil) y otra en Miami (USA).
  - Verifica que la moneda sea BRL/R$ en Brasil y USD/$ en USA.
  - Verifica que el ticket promedio sea positivo en ambos casos.

### 3. Test de Performance
- **Propósito:** Garantizar que el score de Lighthouse en Vercel sea > 95 incluso con el mapa de calor cargado.
- **Lógica:**
  - Usa Playwright y Lighthouse para auditar la página `/dashboard/premium` en producción.
  - Falla si el score de performance es menor o igual a 95.

## Ejecución

1. Instala dependencias:
   ```bash
   pip install pytest requests
   npm install -g playwright lighthouse
   playwright install
   ```
2. Ejecuta los tests:
   ```bash
   pytest tests/test_global_validator.py
   ```

## Notas
- Asegúrate de que el backend esté corriendo localmente para los tests de API.
- El test de Lighthouse requiere acceso a la URL de producción en Vercel.
- Los tests pueden ser extendidos para otros países y monedas según se requiera.

---

**Autor:** Equipo Lokigi
**Fecha:** 2025-12-29

Para ampliar la cobertura, agrega más casos en `test_gemini_audit.py` según evolucione la lógica de negocio.
