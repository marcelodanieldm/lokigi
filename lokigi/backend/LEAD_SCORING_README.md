# Algoritmo de Lead Scoring Automático (Lokigi)

## Objetivo
Filtrar entre miles de negocios para encontrar los que tienen más probabilidad de pagar hoy.

## Implementación

### 1. Filtro de Selección
- Selecciona negocios que cumplan al menos uno:
  - `is_claimed == False`
  - `rating < 4.0`
  - `last_review_days > 180`

### 2. Priorización por Ticket
- Cruza la categoría con la tabla de 'Valor de Cliente' (`CLIENT_VALUE`).
- Prioriza Dentistas, Abogados y Reformas sobre Cafeterías y Tiendas.

### 3. Detección de Idioma de Prospección
- Basado en el código de país del teléfono o el dominio del sitio web:
  - +55 o .br → PT
  - +1, .us, .com → EN
  - +34, .es → ES
  - Default: ES

### 4. Output
- Genera un JSON de 'high_value_targets' listo para el motor de despacho.

## Ejemplo de Uso

```python
from lead_scoring import lead_scoring

businesses = [
    {"name": "Dentista Smile", "is_claimed": False, "rating": 4.5, "last_review_days": 10, "category": "Dentista", "phone": "+34...", "website": "smile.es"},
    {"name": "Café Central", "is_claimed": True, "rating": 3.8, "last_review_days": 20, "category": "Cafetería", "phone": "+34...", "website": "cafecentral.com"},
    {"name": "Reformas Pro", "is_claimed": True, "rating": 4.2, "last_review_days": 200, "category": "Reformas", "phone": "+55...", "website": "reformaspro.com.br"},
    {"name": "Tienda X", "is_claimed": True, "rating": 4.5, "last_review_days": 30, "category": "Tienda", "phone": "+1...", "website": "tiendax.us"}
]
targets = lead_scoring(businesses)
print(targets)
```

## Documentación de funciones
- `lead_scoring(businesses)`: Devuelve lista de High-Value Targets priorizados y con idioma asignado.

---

**Chief Data Officer: Algoritmo validado y listo para producción.**
