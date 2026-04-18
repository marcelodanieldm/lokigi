"""
Cron Job para Monitoreo Automático de Radar Lokigi
Ejecutar diariamente para monitorear competidores y generar alertas

Uso:
    python radar_cron_job.py

En producción, configurar con crontab o Windows Task Scheduler:
    # Ejecutar todos los días a las 2 AM
    0 2 * * * /path/to/python /path/to/radar_cron_job.py
"""
import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from competitor_monitoring_service import CompetitorMonitoringService
from radar_service import RadarService


def run_monitoring_job():
    """
    Ejecuta el trabajo de monitoreo de todas las suscripciones
    """
    print("=" * 70)
    print("🎯 RADAR LOKIGI - MONITOREO AUTOMÁTICO DE COMPETENCIA")
    print("=" * 70)
    print(f"⏰ Inicio: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    
    db = SessionLocal()
    radar_service = RadarService()
    
    try:
        # Obtener suscripciones que necesitan monitoreo
        subscriptions = CompetitorMonitoringService.get_subscriptions_to_monitor(db)
        
        print(f"📊 Suscripciones a monitorear: {len(subscriptions)}\n")
        
        if not subscriptions:
            print("✅ No hay suscripciones pendientes de monitoreo")
            return
        
        total_snapshots = 0
        total_alerts = 0
        total_heatmaps = 0
        errors = []
        
        # Procesar cada suscripción
        for i, subscription in enumerate(subscriptions, 1):
            print(f"\n[{i}/{len(subscriptions)}] Monitoreando suscripción #{subscription.id} (Lead: {subscription.lead_id})...")
            
            try:
                # Monitorear competidores
                result = CompetitorMonitoringService.monitor_subscription_competitors(
                    db=db,
                    subscription_id=subscription.id,
                    radar_service=radar_service
                )
                
                if "error" in result:
                    print(f"   ❌ Error: {result['error']}")
                    errors.append({
                        "subscription_id": subscription.id,
                        "error": result["error"]
                    })
                    continue
                
                snapshots = result.get("snapshots_created", 0)
                alerts = result.get("alerts_generated", 0)
                
                total_snapshots += snapshots
                total_alerts += alerts
                
                print(f"   ✅ Snapshots creados: {snapshots}")
                print(f"   📢 Alertas generadas: {alerts}")
                
                # Generar heatmap si corresponde (cada 30 días)
                if subscription.last_monitoring_at:
                    days_since_last = (datetime.utcnow() - subscription.last_monitoring_at).days
                    if days_since_last >= 30:
                        print(f"   🗺️  Generando heatmap mensual...")
                        heatmap = CompetitorMonitoringService.update_visibility_heatmap(
                            db=db,
                            subscription_id=subscription.id,
                            radar_service=radar_service
                        )
                        if heatmap:
                            total_heatmaps += 1
                            print(f"   ✅ Heatmap generado (Dominancia: {heatmap.area_dominance_score:.1f}%)")
                
            except Exception as e:
                print(f"   ❌ Error inesperado: {str(e)}")
                errors.append({
                    "subscription_id": subscription.id,
                    "error": str(e)
                })
        
        # Resumen
        print("\n" + "=" * 70)
        print("📊 RESUMEN DEL MONITOREO")
        print("=" * 70)
        print(f"✅ Suscripciones procesadas: {len(subscriptions)}")
        print(f"📸 Snapshots creados: {total_snapshots}")
        print(f"📢 Alertas generadas: {total_alerts}")
        print(f"🗺️  Heatmaps actualizados: {total_heatmaps}")
        
        if errors:
            print(f"\n⚠️  Errores encontrados: {len(errors)}")
            for error in errors:
                print(f"   - Suscripción #{error['subscription_id']}: {error['error']}")
        else:
            print("\n✅ Todos los monitoreos completados sin errores")
        
        print(f"\n⏰ Fin: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    try:
        run_monitoring_job()
    except Exception as e:
        print(f"\n💥 El cron job falló: {str(e)}")
        sys.exit(1)
