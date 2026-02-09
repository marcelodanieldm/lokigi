# QA Automation: Validador de Resultados para Reportes de Impacto (Certificado de Éxito Lokigi)

## Objetivo
Garantizar que los números del reporte sean coherentes y el archivo PDF sea legible en cualquier dispositivo.

## Pruebas Implementadas

### 1. Integridad de Datos
- Valida que el `final_score` en el PDF coincida exactamente con el enviado y guardado en la base de datos tras la intervención del Worker.
- Usa Pytest y PyPDF2 para extraer y comparar el texto del PDF generado.

### 2. Test de Generación Concurrente
- Automatiza la creación de 10 reportes simultáneos para verificar que no haya fugas de memoria ni errores de concurrencia en el backend Python.
- Usa `concurrent.futures` para lanzar múltiples requests en paralelo.

### 3. Visual Regression
- Verifica que los gráficos y textos no se corten en el PDF final, especialmente en nombres de negocios largos o direcciones brasileñas complejas.
- Extrae el texto del PDF y valida que los campos largos aparecen completos.

## Ejecución

1. Asegúrate de tener el backend corriendo en `localhost:8000` y acceso a Supabase Storage.
2. Instala dependencias:
   ```bash
   pip install pytest requests PyPDF2
   ```
3. Ejecuta las pruebas:
   ```bash
   pytest tests/test_impact_report_pdf.py
   ```

## Requisitos
- El endpoint `/order` debe estar disponible y funcional.
- El bucket `reports` en Supabase debe ser público.
- El backend debe tener configuradas las variables de entorno para Supabase y SendGrid.

---

**QA Automation by Lokigi**
