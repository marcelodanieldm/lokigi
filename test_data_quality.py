"""
Tests para el módulo de Data Quality Evaluation
Ejecutar: python test_data_quality.py
"""

from data_quality_service import NAPEvaluator
import json


def test_basic_evaluation():
    """Test básico de evaluación de calidad de datos"""
    
    print("🧪 Test 1: Evaluación básica con datos perfectos")
    print("=" * 60)
    
    evaluator = NAPEvaluator()
    
    # Datos perfectos (mismo nombre, teléfono, dirección)
    google_data = {
        "name": "Café del Sol",
        "phone": "+54 11 1234-5678",
        "address": "Av. Libertador 1234, CABA",
        "business_hours": "Lun-Vie 8am-10pm",
        "description": "Café especializado",
        "website": "https://cafedelsol.com",
        "menu_url": "https://cafedelsol.com/menu"
    }
    
    facebook_data = {
        "name": "Café del Sol",
        "phone": "+54 11 1234-5678",
        "address": "Av. Libertador 1234, CABA"
    }
    
    results = evaluator.evaluate_full_quality(
        google_maps_data=google_data,
        facebook_data=facebook_data,
        coordinates=(-34.5833, -58.4011),
        address_coordinates=(-34.5833, -58.4012)  # 11 metros de diferencia
    )
    
    print(f"\n✅ Overall Score: {results['overall_score']}%")
    print(f"📊 Dimensiones:")
    for dim_name, dim_data in results['dimensions'].items():
        print(f"   - {dim_name}: {dim_data['score']}% ({dim_data['status']})")
    
    print(f"\n🚨 Alertas: {len(results['alerts'])}")
    for alert in results['alerts']:
        print(f"   - [{alert['type']}] {alert['title']}")
    
    print(f"\n💡 Recomendaciones: {len(results['recommendations'])}")
    for rec in results['recommendations']:
        print(f"   - {rec}")
    
    print(f"\n🛠️  Requiere servicio de limpieza: {results['requires_cleanup_service']}")
    
    assert results['overall_score'] > 90, "Score debería ser > 90% con datos perfectos"
    print("\n✅ Test 1 PASSED\n")


def test_inconsistent_data():
    """Test con datos inconsistentes (debe recomendar servicio)"""
    
    print("🧪 Test 2: Evaluación con datos inconsistentes")
    print("=" * 60)
    
    evaluator = NAPEvaluator()
    
    # Datos con problemas
    google_data = {
        "name": "Pizzería Napolitana",
        "phone": "+5491145678901",
        "address": "Calle Corrientes 3456, CABA",
        "business_hours": "Lun-Dom 12pm-12am"
    }
    
    facebook_data = {
        "name": "Pizzeria Napolitana - Corrientes",  # Nombre diferente
        "phone": "+5491145678902",  # ❌ Teléfono diferente
        "address": "Corrientes 3456"
    }
    
    website_data = {
        "name": "Napolitana Pizza",  # Nombre diferente
        "phone": "+5491145678901",
        "address": "Av. Corrientes 3456, Buenos Aires"
    }
    
    results = evaluator.evaluate_full_quality(
        google_maps_data=google_data,
        facebook_data=facebook_data,
        website_data=website_data,
        coordinates=(-34.6037, -58.3816),
        address_coordinates=(-34.6045, -58.3820)  # 85 metros de diferencia
    )
    
    print(f"\n✅ Overall Score: {results['overall_score']}%")
    print(f"📊 Dimensiones:")
    for dim_name, dim_data in results['dimensions'].items():
        print(f"   - {dim_name}: {dim_data['score']}% ({dim_data['status']})")
    
    print(f"\n🚨 Alertas: {len(results['alerts'])}")
    for alert in results['alerts']:
        print(f"   - [{alert['type']}] {alert['title']}: {alert['message']}")
    
    print(f"\n💡 Recomendaciones: {len(results['recommendations'])}")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print(f"\n🛠️  Requiere servicio de limpieza: {results['requires_cleanup_service']}")
    
    assert results['requires_cleanup_service'] == True, "Debería requerir servicio con datos inconsistentes"
    assert results['overall_score'] < 90, "Score debería ser < 90% con datos inconsistentes"
    print("\n✅ Test 2 PASSED\n")


def test_phone_normalization():
    """Test de normalización de teléfonos"""
    
    print("🧪 Test 3: Normalización de teléfonos")
    print("=" * 60)
    
    evaluator = NAPEvaluator()
    
    test_cases = [
        ("+54 11 1234-5678", "541112345678"),
        ("(555) 123-4567", "5551234567"),
        ("+1-800-CALL-NOW", "1800"),  # Solo dígitos
        ("11 1234 5678", "1112345678"),
    ]
    
    for original, expected in test_cases:
        result = evaluator._normalize_phone(original)
        print(f"   {original} → {result}")
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("\n✅ Test 3 PASSED\n")


def test_location_accuracy():
    """Test de exactitud de ubicación (Haversine)"""
    
    print("🧪 Test 4: Cálculo de distancia (Haversine)")
    print("=" * 60)
    
    evaluator = NAPEvaluator()
    
    # Coordenadas conocidas
    coord1 = (-34.6037, -58.3816)  # Obelisco, Buenos Aires
    coord2 = (-34.6045, -58.3820)  # ~90 metros al sur
    
    distance = evaluator._calculate_haversine_distance(coord1, coord2)
    print(f"   Distancia calculada: {distance:.2f} metros")
    
    assert 80 < distance < 100, f"Distancia debería ser ~90m, obtenido {distance}m"
    
    # Test con coordenadas idénticas
    distance_zero = evaluator._calculate_haversine_distance(coord1, coord1)
    print(f"   Distancia misma coordenada: {distance_zero:.2f} metros")
    
    assert distance_zero == 0, "Distancia de coordenada idéntica debe ser 0"
    
    print("\n✅ Test 4 PASSED\n")


def test_string_similarity():
    """Test de similitud de strings"""
    
    print("🧪 Test 5: Similitud de strings")
    print("=" * 60)
    
    evaluator = NAPEvaluator()
    
    test_cases = [
        ("Café del Sol", "Café del Sol", 100.0),
        ("Café del Sol", "Cafe del Sol", 90.0),  # Aproximado
        ("Restaurant ABC", "ABC Restaurant", 60.0),  # Aproximado
        ("Pizza Place", "Burger Place", 50.0),  # Aproximado
    ]
    
    for str1, str2, expected_min in test_cases:
        similarity = evaluator._calculate_string_similarity(str1, str2)
        print(f"   '{str1}' vs '{str2}': {similarity}%")
        assert similarity >= expected_min - 10, f"Similitud muy baja: {similarity}%"
    
    print("\n✅ Test 5 PASSED\n")


def test_critical_alerts():
    """Test de generación de alertas críticas"""
    
    print("🧪 Test 6: Alertas críticas con score bajo")
    print("=" * 60)
    
    evaluator = NAPEvaluator()
    
    # Datos con score muy bajo
    google_data = {
        "name": "Mi Negocio",
        "phone": "+54111111111",
        "address": "Calle 123"
    }
    
    facebook_data = {
        "name": "Otro Nombre Completamente Diferente",
        "phone": "+54999999999",  # Teléfono diferente
        "address": "Otra Calle 456"
    }
    
    results = evaluator.evaluate_full_quality(
        google_maps_data=google_data,
        facebook_data=facebook_data,
        coordinates=(-34.6037, -58.3816),
        address_coordinates=(-34.7037, -58.5816)  # ~15km de diferencia
    )
    
    print(f"\n✅ Overall Score: {results['overall_score']}%")
    
    critical_alerts = [a for a in results['alerts'] if a['type'] == 'critical']
    print(f"\n🚨 Alertas Críticas: {len(critical_alerts)}")
    for alert in critical_alerts:
        print(f"   - {alert['title']}")
    
    assert len(critical_alerts) >= 2, "Debería haber al menos 2 alertas críticas"
    assert results['requires_cleanup_service'] == True, "Debería requerir servicio"
    
    print("\n✅ Test 6 PASSED\n")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("🚀 INICIANDO TESTS DE DATA QUALITY MODULE")
    print("=" * 60 + "\n")
    
    try:
        test_basic_evaluation()
        test_inconsistent_data()
        test_phone_normalization()
        test_location_accuracy()
        test_string_similarity()
        test_critical_alerts()
        
        print("=" * 60)
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
