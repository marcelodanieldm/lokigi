"""
Script de migración: Agregar tablas de Radar Lokigi
Ejecutar: python migrate_radar_lokigi.py
"""

from database import engine
from models import CompetitorSnapshot, RadarAlert, VisibilityHeatmap

def run_migration():
    """Crea las tablas de Radar Lokigi"""
    print("🔄 Iniciando migración: Radar Lokigi tables...")
    
    try:
        # Crear tablas
        CompetitorSnapshot.__table__.create(engine, checkfirst=True)
        print("✅ Tabla 'competitor_snapshots' creada exitosamente")
        
        RadarAlert.__table__.create(engine, checkfirst=True)
        print("✅ Tabla 'radar_alerts' creada exitosamente")
        
        VisibilityHeatmap.__table__.create(engine, checkfirst=True)
        print("✅ Tabla 'visibility_heatmaps' creada exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        raise

if __name__ == "__main__":
    run_migration()
    print("\n🎉 Migración completada!")
    print("📊 3 nuevas tablas creadas para Radar Lokigi")
