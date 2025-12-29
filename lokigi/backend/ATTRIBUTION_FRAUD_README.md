# Atribución y Prevención de Fraude - Documentación

## Objetivo
Asegurar que cada venta se asigne al socio correcto y detectar comportamientos sospechosos (auto-afiliación, IPs, ráfagas). Incluye cálculo de comisiones y soporte multimoneda.

## Componentes

### 1. Atribución Last Click (ventana 30 días)
- Busca el último click válido antes de la venta.
- Usa cookies y timestamp para asignar la venta al afiliado correcto.

### 2. Detección de Fraude
- Auto-afiliación: afiliado y comprador son el mismo usuario.
- Misma IP: afiliado y comprador usan la misma IP.
- Ráfaga de compras: más de 3 ventas en 10 minutos para un afiliado.

### 3. Cálculo de Comisiones
- Comisiones 'Pendientes': ventas pagadas en periodo de garantía (ej. 14 días).
- Comisiones 'Disponibles': ventas liberadas tras el periodo de garantía.
- Conversión automática a la moneda del afiliado usando tasas de cambio.

### 4. Internacionalización
- El sistema soporta múltiples monedas y tasas de cambio.

## Ejemplo de Uso
```python
from backend.attribution_fraud import atribuir_venta, detectar_fraude, calcular_comisiones
# ...ver ejemplo en el script...
```

## Notas
- Integrar con el sistema de tracking de cookies y eventos del frontend/backend.
- Personalizar reglas de fraude según el negocio.
- Las tasas de cambio pueden obtenerse de una API externa.

---
Última actualización: 2025-12-29
