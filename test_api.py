# Script de prueba para el MVP de SEO Local
# Ejecuta este archivo para probar el endpoint sin frontend

import requests
import json

BASE_URL = "http://localhost:8000"

def test_audit_endpoint():
    """
    Prueba el endpoint POST /audit/test con datos de ejemplo
    """
    print("🧪 Testing SEO Local Analyzer API\n")
    print("=" * 60)
    
    # Datos de prueba
    test_data = {
        "business": {
            "name": "Restaurante Casa Pepe",
            "rating": 3.5,
            "review_count": 23,
            "has_website": False,
            "is_claimed": False,
            "last_photo_date": "2023-03-15",
            "category": "Restaurante Español",
            "location": "Madrid"
        },
        "include_ai_analysis": False  # Cambiar a True si tienes OpenAI configurado
    }
    
    print("\n📤 Enviando request a /audit/test...")
    print(f"\nDatos del negocio:")
    print(f"  • Nombre: {test_data['business']['name']}")
    print(f"  • Rating: {test_data['business']['rating']}/5.0")
    print(f"  • Reseñas: {test_data['business']['review_count']}")
    print(f"  • Sitio web: {'Sí' if test_data['business']['has_website'] else 'No'}")
    print(f"  • Reclamado: {'Sí' if test_data['business']['is_claimed'] else 'No'}")
    print(f"  • Última foto: {test_data['business']['last_photo_date']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/audit/test",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ RESPUESTA EXITOSA\n")
            print("=" * 60)
            
            # Mostrar score
            print(f"\n📊 SCORE DE SALUD: {result['score']}/100")
            score_status = "🔴 CRÍTICO" if result['score'] < 40 else "🟡 MEJORABLE" if result['score'] < 70 else "🟢 BUENO"
            print(f"   Estado: {score_status}\n")
            
            # Problema crítico
            print(f"🚨 PROBLEMA CRÍTICO:")
            print(f"   {result['critical_fix']}\n")
            
            # Impacto económico
            print(f"💰 IMPACTO ECONÓMICO:")
            for line in result['economic_impact'].split('\n'):
                if line.strip():
                    print(f"   {line}")
            print()
            
            # FODA
            print(f"📈 ANÁLISIS FODA:\n")
            print(f"   FORTALEZAS:")
            for f in result['foda']['fortalezas']:
                print(f"   ✓ {f}")
            print(f"\n   OPORTUNIDADES:")
            for o in result['foda']['oportunidades']:
                print(f"   → {o}")
            print(f"\n   DEBILIDADES:")
            for d in result['foda']['debilidades']:
                print(f"   ✗ {d}")
            print(f"\n   AMENAZAS:")
            for a in result['foda']['amenazas']:
                print(f"   ⚠ {a}")
            
            # Competidores
            print(f"\n🏆 COMPETENCIA (10km a la redonda):\n")
            for i, comp in enumerate(result['competitors'], 1):
                print(f"   {i}. {comp['name']}")
                print(f"      Rating: {comp['rating']}★ | Reseñas: {comp['review_count']}")
                print(f"      Web: {'Sí' if comp['has_website'] else 'No'} | Distancia: {comp['distance_km']}km")
                print(f"      Revenue estimado: {comp['estimated_monthly_revenue']}/mes\n")
            
            # Análisis detallado
            print(f"📝 ANÁLISIS DETALLADO:\n")
            for line in result['detailed_analysis'].split('\n'):
                if line.strip():
                    print(f"   {line}")
            
            # Plan de acción
            print(f"\n✅ PLAN DE ACCIÓN:\n")
            for step in result['action_plan']:
                print(f"   {step}")
            
            print("\n" + "=" * 60)
            print("\n💾 Respuesta completa guardada en: audit_result.json")
            
            # Guardar resultado
            with open("audit_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor está corriendo:")
        print("   python api_mvp.py")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


def test_quick_audit():
    """
    Prueba el endpoint rápido /audit/quick
    """
    print("\n\n🚀 Testing Quick Audit Endpoint\n")
    print("=" * 60)
    
    test_data = {
        "name": "Bar La Esquina",
        "rating": 4.2,
        "review_count": 89,
        "has_website": True,
        "is_claimed": True,
        "last_photo_date": "2024-11-20"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/audit/quick",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Quick Audit Result:\n")
            print(f"Score: {result['score']}/100")
            print(f"\n{result['critical_fix']}")
            print(f"\n{result['economic_impact']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("\n" + "🎯" * 30)
    print("  SEO LOCAL ANALYZER - TEST SUITE")
    print("🎯" * 30 + "\n")
    
    # Test principal
    test_audit_endpoint()
    
    # Test rápido
    # test_quick_audit()
    
    print("\n✨ Tests completados!\n")
