# Motor de Curación del Marketplace
# Sencillo: ranking, detección de reseñas falsas, recomendación de add-ons

from collections import Counter
from datetime import datetime, timedelta

# 1. Ranking Algorítmico

def ranking_algoritmico(app):
    """
    app: dict con 'ventas', 'rating', 'desinstalaciones'
    """
    ventas = app.get('ventas', 1)
    rating = app.get('rating', 1)
    desinstalaciones = app.get('desinstalaciones', 1)
    return ventas * (rating ** 2) / max(desinstalaciones, 1)

# 2. Detección de Reseñas Falsas

def detectar_reseñas_falsas(reviews):
    """
    reviews: lista de dicts con 'ip', 'fecha_compra', 'fecha_review'
    Devuelve lista de ids sospechosos
    """
    ips = [r['ip'] for r in reviews]
    ip_counts = Counter(ips)
    sospechosos = []
    for r in reviews:
        # IP repetida
        if ip_counts[r['ip']] > 2:
            sospechosos.append(r.get('id'))
        # Reseña muy rápida tras compra
        try:
            fc = datetime.strptime(r['fecha_compra'], '%Y-%m-%d %H:%M:%S')
            fr = datetime.strptime(r['fecha_review'], '%Y-%m-%d %H:%M:%S')
            if (fr - fc) < timedelta(minutes=10):
                sospechosos.append(r.get('id'))
        except Exception:
            continue
    return list(set(sospechosos))

# 3. Recomendación de Add-ons

def recomendar_addons(cliente, apps, addons):
    """
    cliente: dict con 'rubro', 'idioma'
    apps: lista de apps instaladas
    addons: lista de dicts con 'rubro', 'idiomas', 'nombre'
    Devuelve lista de add-ons recomendados
    """
    rubro = cliente.get('rubro')
    idioma = cliente.get('idioma')
    recomendados = []
    for addon in addons:
        if rubro and addon.get('rubro') == rubro:
            if idioma in addon.get('idiomas', []):
                recomendados.append(addon['nombre'])
    return recomendados

# Ejemplo de uso
if __name__ == '__main__':
    app = {'ventas': 100, 'rating': 4.5, 'desinstalaciones': 10}
    print('Ranking:', ranking_algoritmico(app))

    reviews = [
        {'id': 1, 'ip': '1.2.3.4', 'fecha_compra': '2026-02-09 10:00:00', 'fecha_review': '2026-02-09 10:05:00'},
        {'id': 2, 'ip': '1.2.3.4', 'fecha_compra': '2026-02-09 10:00:00', 'fecha_review': '2026-02-09 10:06:00'},
        {'id': 3, 'ip': '5.6.7.8', 'fecha_compra': '2026-02-09 09:00:00', 'fecha_review': '2026-02-09 11:00:00'},
    ]
    print('Sospechosos:', detectar_reseñas_falsas(reviews))

    cliente = {'rubro': 'Restaurante', 'idioma': 'es'}
    addons = [
        {'nombre': 'Menú Digital Generator', 'rubro': 'Restaurante', 'idiomas': ['es', 'en']},
        {'nombre': 'POS Integrator', 'rubro': 'Retail', 'idiomas': ['en']},
    ]
    print('Add-ons recomendados:', recomendar_addons(cliente, [], addons))
