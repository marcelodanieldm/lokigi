"""
Script de prueba para verificar la generación automática de tareas
"""
from database import SessionLocal
from models import Lead, Order, ProductType, OrderStatus, CustomerStatus
from task_generator import generate_tasks_from_audit
from datetime import datetime

def test_task_generation():
    """
    Crea un lead y orden de prueba, luego genera tareas
    """
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("TEST: GENERACIÓN AUTOMÁTICA DE TAREAS")
        print("=" * 70)
        print()
        
        # 1. Crear Lead de prueba
        print("📝 Creando lead de prueba...")
        lead = Lead(
            nombre="María García",
            email="maria.garcia@test.com",
            telefono="+34612345678",
            whatsapp="+34612345678",
            nombre_negocio="Restaurante La Trattoria",
            direccion_negocio="Calle Mayor 45, Madrid",
            score_visibilidad=35,
            score_reputacion=25,
            score_engagement=20,
            score_inicial=27,
            fallos_criticos=[
                "perfil no reclamado",
                "sin sitio web",
                "fotos antiguas o inexistentes"
            ],
            audit_data={
                "rating": 3.8,
                "numero_resenas": 12,
                "tiene_horarios": False,
                "tiene_descripcion": False
            },
            customer_status=CustomerStatus.CLIENTE,
            created_at=datetime.utcnow(),
            paid_at=datetime.utcnow()
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        print(f"✅ Lead creado con ID: {lead.id}")
        print(f"   Negocio: {lead.nombre_negocio}")
        print(f"   Score inicial: {lead.score_inicial}/100")
        print(f"   Fallos críticos: {len(lead.fallos_criticos)}")
        print()
        
        # 2. Crear Order de prueba
        print("📦 Creando orden de prueba...")
        order = Order(
            lead_id=lead.id,
            product_type=ProductType.SERVICE,
            amount=99.00,
            currency="USD",
            status=OrderStatus.COMPLETED,
            stripe_session_id="test_session_123",
            stripe_payment_intent_id="test_pi_456",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        print(f"✅ Orden creada con ID: {order.id}")
        print(f"   Producto: {order.product_type.value}")
        print(f"   Monto: ${order.amount}")
        print()
        
        # 3. Generar tareas automáticamente
        print("🤖 Generando tareas automáticamente...")
        print("-" * 70)
        tasks = generate_tasks_from_audit(
            order_id=order.id,
            audit_data=lead.audit_data,
            fallos_criticos=lead.fallos_criticos,
            db=db
        )
        
        print()
        print("=" * 70)
        print(f"✅ ÉXITO: {len(tasks)} TAREAS GENERADAS")
        print("=" * 70)
        print()
        
        # Mostrar tareas por categoría
        categorias = {}
        for task in tasks:
            cat = task.category.value
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(task)
        
        for categoria, tareas_cat in categorias.items():
            print(f"\n📁 {categoria} ({len(tareas_cat)} tareas)")
            print("-" * 70)
            for task in sorted(tareas_cat, key=lambda t: t.priority, reverse=True):
                prioridad_emoji = "🔴" if task.priority >= 9 else "🟠" if task.priority >= 7 else "🟡" if task.priority >= 5 else "🟢" if task.priority >= 3 else "🔵"
                print(f"{prioridad_emoji} Prioridad {task.priority:2d} | {task.description[:60]}...")
        
        print()
        print("=" * 70)
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print()
        print(f"🔍 Para ver las tareas en la API:")
        print(f"   GET http://localhost:8000/api/dashboard/orders/{order.id}/tasks")
        print()
        print(f"✏️  Para marcar una tarea como completada:")
        print(f"   PATCH http://localhost:8000/api/dashboard/tasks/{{task_id}}")
        print(f'   Body: {{"is_completed": true, "notes": "Tarea completada"}}')
        print()
        
        return order.id
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None
    
    finally:
        db.close()

if __name__ == "__main__":
    order_id = test_task_generation()
    
    if order_id:
        print("✅ Test exitoso. Base de datos lista para usar.")
    else:
        print("❌ Test falló. Revisa los errores arriba.")
