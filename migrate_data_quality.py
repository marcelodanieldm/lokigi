"""
Script de migración: Agregar tabla data_quality_evaluations
Ejecutar: python migrate_data_quality.py
"""

from database import engine, Base
from models import DataQualityEvaluation

def run_migration():
    """Crea la tabla data_quality_evaluations si no existe"""
    print("🔄 Iniciando migración: data_quality_evaluations...")
    
    try:
        # Crear solo la tabla DataQualityEvaluation
        DataQualityEvaluation.__table__.create(engine, checkfirst=True)
        print("✅ Tabla 'data_quality_evaluations' creada exitosamente")
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        raise

if __name__ == "__main__":
    run_migration()
    print("\n🎉 Migración completada!")
