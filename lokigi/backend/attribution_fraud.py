"""
Atribución y Prevención de Fraude para Afiliados - Lokigi
Chief Data Officer Implementation

- Sistema de atribución Last Click (ventana 30 días, cookies).
- Detección de fraude: IPs, ráfagas, auto-afiliación.
- Cálculo de comisiones: Pendientes (en garantía) y Disponibles (liberadas).
- Internacionalización: Soporte multimoneda.
"""
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict

# --- Atribución Last Click ---
def atribuir_venta(eventos: List[dict], fecha_venta: datetime) -> str:
    """
    Busca el último click válido en la ventana de 30 días antes de la venta.
    eventos: [{"afiliado_id", "timestamp", "ip", "cookie_id"}]
    fecha_venta: datetime de la compra
    Return: afiliado_id o None
    """
    ventana = fecha_venta - timedelta(days=30)
    clicks = [e for e in eventos if ventana <= e['timestamp'] <= fecha_venta]
    if not clicks:
        return None
    # Last click
    return sorted(clicks, key=lambda e: e['timestamp'], reverse=True)[0]['afiliado_id']

# --- Detección de Fraude ---
def detectar_fraude(afiliado_id: str, comprador_id: str, ip_afiliado: str, ip_comprador: str, eventos: List[dict], fecha_venta: datetime) -> List[str]:
    """
    Detecta patrones de fraude:
    - Auto-afiliación (afiliado == comprador)
    - Misma IP afiliado y comprador
    - Ráfaga de compras (>3 ventas en 10 min)
    """
    alertas = []
    if afiliado_id == comprador_id:
        alertas.append("Auto-afiliación detectada")
    if ip_afiliado == ip_comprador:
        alertas.append("Misma IP para afiliado y comprador")
    # Ráfaga de compras
    ventas = [e['timestamp'] for e in eventos if e.get('tipo') == 'venta' and e.get('afiliado_id') == afiliado_id]
    ventas_en_rango = [t for t in ventas if fecha_venta - timedelta(minutes=10) <= t <= fecha_venta]
    if len(ventas_en_rango) > 3:
        alertas.append("Ráfaga de compras sospechosa")
    return alertas

# --- Cálculo de Comisiones ---
def calcular_comisiones(ventas: List[dict], moneda_afiliado: str, tasa_cambio: Dict[str, float], dias_garantia: int = 14) -> dict:
    """
    ventas: [{"afiliado_id", "monto", "moneda", "fecha", "status"}]
    moneda_afiliado: moneda destino
    tasa_cambio: {"USD": 1, "EUR": 0.9, ...}
    Return: {"pendientes": float, "disponibles": float}
    """
    ahora = datetime.utcnow()
    pendientes = 0.0
    disponibles = 0.0
    for v in ventas:
        monto = v['monto'] * (tasa_cambio.get(moneda_afiliado, 1) / tasa_cambio.get(v['moneda'], 1))
        dias = (ahora - v['fecha']).days
        if v['status'] == 'pagada' and dias < dias_garantia:
            pendientes += monto
        elif v['status'] == 'pagada' and dias >= dias_garantia:
            disponibles += monto
    return {"pendientes": round(pendientes, 2), "disponibles": round(disponibles, 2)}

# --- Ejemplo de uso ---
if __name__ == "__main__":
    # Simulación de eventos de click y venta
    eventos = [
        {"afiliado_id": "a1", "timestamp": datetime(2025,12,1,10), "ip": "1.1.1.1", "cookie_id": "c1"},
        {"afiliado_id": "a2", "timestamp": datetime(2025,12,10,12), "ip": "2.2.2.2", "cookie_id": "c2"},
    ]
    fecha_venta = datetime(2025,12,15,13)
    afiliado = atribuir_venta(eventos, fecha_venta)
    print("Afiliado atribuido:", afiliado)

    alertas = detectar_fraude("a1", "u1", "1.1.1.1", "1.1.1.1", eventos + [{"tipo": "venta", "afiliado_id": "a1", "timestamp": fecha_venta}], fecha_venta)
    print("Alertas de fraude:", alertas)

    ventas = [
        {"afiliado_id": "a1", "monto": 100, "moneda": "USD", "fecha": datetime(2025,12,20), "status": "pagada"},
        {"afiliado_id": "a1", "monto": 200, "moneda": "EUR", "fecha": datetime(2025,12,10), "status": "pagada"},
    ]
    tasas = {"USD": 1, "EUR": 1.1}
    comisiones = calcular_comisiones(ventas, "USD", tasas)
    print("Comisiones:", comisiones)
