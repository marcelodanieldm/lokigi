"""
Servicio de Monitoreo de Competidores - Radar Lokigi
Sistema de tracking mensual y generación de alertas automáticas
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import (
    Lead, RadarSubscription, CompetitorSnapshot, RadarAlert,
    VisibilityHeatmap, SubscriptionStatus, AlertSeverity
)
from radar_service import RadarService
import math


class CompetitorMonitoringService:
    """Servicio de monitoreo de competidores"""
    
    # Umbrales para disparar alertas
    ALERT_THRESHOLDS = {
        "score_increase": 5.0,      # +5 puntos en score
        "new_reviews": 10,           # +10 reseñas
        "new_photos": 5,             # +5 fotos nuevas
        "rating_increase": 0.3,      # +0.3 en rating
    }
    
    @staticmethod
    def calculate_visibility_score(lead_data: Dict) -> float:
        """
        Calcula un score de visibilidad basado en múltiples factores
        Score de 0-100
        """
        score = 0.0
        
        # Rating (30%)
        if lead_data.get("rating"):
            rating = lead_data["rating"]
            score += (rating / 5.0) * 30
        
        # Número de reseñas (25%)
        reviews = lead_data.get("reviews_count", 0)
        if reviews > 0:
            # Escala logarítmica: más reseñas = mejor, pero con rendimientos decrecientes
            reviews_score = min(25, math.log(reviews + 1) * 5)
            score += reviews_score
        
        # Fotos (15%)
        photos = lead_data.get("photos_count", 0)
        if photos > 0:
            photos_score = min(15, photos * 0.5)
            score += photos_score
        
        # Completitud de información (20%)
        completeness = 0
        fields = ["phone", "website", "address", "categories", "hours"]
        for field in fields:
            if lead_data.get(field):
                completeness += 4  # 5 campos × 4 = 20
        score += completeness
        
        # Actividad reciente (10%)
        # Si tiene datos de última actualización
        if lead_data.get("last_updated"):
            try:
                last_update = datetime.fromisoformat(lead_data["last_updated"])
                days_since_update = (datetime.utcnow() - last_update).days
                if days_since_update < 30:
                    score += 10
                elif days_since_update < 90:
                    score += 5
            except:
                pass
        
        return min(100.0, score)
    
    @classmethod
    def create_competitor_snapshot(
        cls,
        db: Session,
        competitor_id: int,
        subscription_id: int,
        radar_service: RadarService
    ) -> Optional[CompetitorSnapshot]:
        """
        Crea un snapshot del estado actual de un competidor
        """
        # Obtener datos actuales del competidor
        competitor = db.query(Lead).filter(Lead.id == competitor_id).first()
        if not competitor:
            return None
        
        # Preparar datos para el snapshot
        snapshot_data = {
            "name": competitor.name,
            "rating": competitor.rating,
            "reviews_count": competitor.reviews_count,
            "phone": competitor.phone,
            "address": competitor.address,
            "website": competitor.website,
            "categories": competitor.categories,
            "latitude": competitor.latitude,
            "longitude": competitor.longitude,
            "photos_count": 0,  # TODO: Obtener de Google Maps
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Calcular visibility score
        visibility_score = cls.calculate_visibility_score(snapshot_data)
        
        # Buscar snapshot anterior
        previous_snapshot = db.query(CompetitorSnapshot)\
            .filter(
                and_(
                    CompetitorSnapshot.competitor_id == competitor_id,
                    CompetitorSnapshot.subscription_id == subscription_id
                )
            )\
            .order_by(CompetitorSnapshot.captured_at.desc())\
            .first()
        
        # Calcular cambios
        rating_change = None
        reviews_change = None
        photos_change = None
        score_change = None
        alert_triggered = False
        alert_reasons = []
        
        if previous_snapshot:
            # Cambios en métricas
            if competitor.rating and previous_snapshot.rating:
                rating_change = competitor.rating - previous_snapshot.rating
                if rating_change >= cls.ALERT_THRESHOLDS["rating_increase"]:
                    alert_triggered = True
                    alert_reasons.append({
                        "type": "rating_increase",
                        "message": f"Rating subió {rating_change:.1f} puntos",
                        "severity": "medium"
                    })
            
            if competitor.reviews_count and previous_snapshot.reviews_count:
                reviews_change = competitor.reviews_count - previous_snapshot.reviews_count
                if reviews_change >= cls.ALERT_THRESHOLDS["new_reviews"]:
                    alert_triggered = True
                    alert_reasons.append({
                        "type": "reviews_surge",
                        "message": f"Recibió {reviews_change} nuevas reseñas",
                        "severity": "high"
                    })
            
            # Cambio en score
            if previous_snapshot.visibility_score:
                score_change = visibility_score - previous_snapshot.visibility_score
                if score_change >= cls.ALERT_THRESHOLDS["score_increase"]:
                    alert_triggered = True
                    alert_reasons.append({
                        "type": "score_increase",
                        "message": f"Score de visibilidad subió {score_change:.1f} puntos",
                        "severity": "high"
                    })
        
        # Crear snapshot
        snapshot = CompetitorSnapshot(
            competitor_id=competitor_id,
            subscription_id=subscription_id,
            name=competitor.name,
            rating=competitor.rating,
            reviews_count=competitor.reviews_count,
            photos_count=snapshot_data["photos_count"],
            visibility_score=visibility_score,
            snapshot_data=snapshot_data,
            previous_snapshot_id=previous_snapshot.id if previous_snapshot else None,
            rating_change=rating_change,
            reviews_change=reviews_change,
            photos_change=photos_change,
            score_change=score_change,
            alert_triggered=alert_triggered,
            alert_reasons=alert_reasons if alert_reasons else None,
            captured_at=datetime.utcnow()
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        
        return snapshot
    
    @classmethod
    def generate_alert_for_snapshot(
        cls,
        db: Session,
        snapshot: CompetitorSnapshot,
        subscription: RadarSubscription
    ) -> Optional[RadarAlert]:
        """
        Genera una alerta basada en un snapshot si se cumplen las condiciones
        """
        if not snapshot.alert_triggered or not snapshot.alert_reasons:
            return None
        
        # Determinar severidad máxima
        severities = [reason.get("severity", "low") for reason in snapshot.alert_reasons]
        if "critical" in severities:
            severity = AlertSeverity.CRITICAL
        elif "high" in severities:
            severity = AlertSeverity.HIGH
        elif "medium" in severities:
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW
        
        # Construir mensaje
        competitor_name = snapshot.name
        reasons_text = "\n".join([f"• {r['message']}" for r in snapshot.alert_reasons])
        
        title = f"🚨 Alerta Lokigi: {competitor_name} se está moviendo"
        message = f"""
Tu competidor {competitor_name} ha mostrado actividad significativa:

{reasons_text}

Tu posición en el mercado local está en riesgo. 
Te recomendamos revisar tu estrategia y considerar acciones inmediatas.
"""
        
        # Crear alerta
        alert = RadarAlert(
            lead_id=subscription.lead_id,
            subscription_id=subscription.id,
            competitor_snapshot_id=snapshot.id,
            title=title,
            message=message.strip(),
            severity=severity,
            alert_type="competitor_movement",
            metadata={
                "competitor_name": competitor_name,
                "competitor_id": snapshot.competitor_id,
                "changes": snapshot.alert_reasons,
                "score_change": snapshot.score_change,
                "reviews_change": snapshot.reviews_change
            },
            created_at=datetime.utcnow()
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        return alert
    
    @classmethod
    def monitor_subscription_competitors(
        cls,
        db: Session,
        subscription_id: int,
        radar_service: RadarService
    ) -> Dict:
        """
        Monitorea todos los competidores de una suscripción
        """
        subscription = db.query(RadarSubscription)\
            .filter(RadarSubscription.id == subscription_id)\
            .first()
        
        if not subscription:
            return {"error": "Subscription not found"}
        
        if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
            return {"error": "Subscription not active"}
        
        competitor_ids = subscription.competitors_to_track
        if not competitor_ids:
            return {"error": "No competitors to track"}
        
        results = {
            "subscription_id": subscription_id,
            "lead_id": subscription.lead_id,
            "monitored_at": datetime.utcnow().isoformat(),
            "competitors_checked": len(competitor_ids),
            "snapshots_created": 0,
            "alerts_generated": 0,
            "snapshots": [],
            "alerts": []
        }
        
        # Procesar cada competidor
        for competitor_id in competitor_ids:
            try:
                # Crear snapshot
                snapshot = cls.create_competitor_snapshot(
                    db=db,
                    competitor_id=competitor_id,
                    subscription_id=subscription_id,
                    radar_service=radar_service
                )
                
                if snapshot:
                    results["snapshots_created"] += 1
                    results["snapshots"].append({
                        "competitor_id": competitor_id,
                        "name": snapshot.name,
                        "score": snapshot.visibility_score,
                        "score_change": snapshot.score_change,
                        "alert_triggered": snapshot.alert_triggered
                    })
                    
                    # Generar alerta si es necesario
                    if snapshot.alert_triggered and subscription.alerts_enabled:
                        alert = cls.generate_alert_for_snapshot(
                            db=db,
                            snapshot=snapshot,
                            subscription=subscription
                        )
                        
                        if alert:
                            results["alerts_generated"] += 1
                            results["alerts"].append({
                                "alert_id": alert.id,
                                "title": alert.title,
                                "severity": alert.severity.value
                            })
                            
                            # Actualizar contador de alertas
                            subscription.total_alerts_sent += 1
            
            except Exception as e:
                results["snapshots"].append({
                    "competitor_id": competitor_id,
                    "error": str(e)
                })
        
        # Actualizar fechas de monitoreo
        subscription.last_monitoring_at = datetime.utcnow()
        subscription.next_monitoring_at = datetime.utcnow() + timedelta(
            days=subscription.monitoring_frequency_days
        )
        db.commit()
        
        return results
    
    @classmethod
    def get_subscriptions_to_monitor(cls, db: Session) -> List[RadarSubscription]:
        """
        Obtiene las suscripciones que necesitan ser monitoreadas
        """
        now = datetime.utcnow()
        
        subscriptions = db.query(RadarSubscription)\
            .filter(
                and_(
                    RadarSubscription.status.in_([
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIAL
                    ]),
                    or_(
                        RadarSubscription.next_monitoring_at.is_(None),
                        RadarSubscription.next_monitoring_at <= now
                    )
                )
            )\
            .all()
        
        return subscriptions
    
    @classmethod
    def update_visibility_heatmap(
        cls,
        db: Session,
        subscription_id: int,
        radar_service: RadarService
    ) -> Optional[VisibilityHeatmap]:
        """
        Actualiza el mapa de calor de visibilidad para una suscripción
        """
        subscription = db.query(RadarSubscription)\
            .filter(RadarSubscription.id == subscription_id)\
            .first()
        
        if not subscription:
            return None
        
        lead = db.query(Lead).filter(Lead.id == subscription.lead_id).first()
        if not lead or not lead.latitude or not lead.longitude:
            return None
        
        # Obtener competidores
        competitor_ids = subscription.competitors_to_track
        competitors_data = []
        
        for comp_id in competitor_ids:
            competitor = db.query(Lead).filter(Lead.id == comp_id).first()
            if competitor and competitor.latitude and competitor.longitude:
                competitors_data.append({
                    "id": competitor.id,
                    "name": competitor.name,
                    "lat": competitor.latitude,
                    "lng": competitor.longitude,
                    "rating": competitor.rating,
                    "reviews": competitor.reviews_count
                })
        
        # Calcular área de influencia y dominance
        # TODO: Implementar cálculo real del heatmap
        radius = 2000  # 2km por defecto
        area_dominance = 65.0  # Placeholder
        
        # Obtener heatmap anterior
        previous_heatmap = db.query(VisibilityHeatmap)\
            .filter(VisibilityHeatmap.lead_id == subscription.lead_id)\
            .order_by(VisibilityHeatmap.created_at.desc())\
            .first()
        
        # Calcular cambios
        area_growth = None
        dominance_change = None
        
        if previous_heatmap:
            area_growth = ((radius - previous_heatmap.radius_meters) / 
                          previous_heatmap.radius_meters * 100)
            dominance_change = area_dominance - previous_heatmap.area_dominance_score
        
        # Crear nuevo heatmap
        heatmap = VisibilityHeatmap(
            lead_id=subscription.lead_id,
            center_coordinates=[lead.latitude, lead.longitude],
            radius_meters=radius,
            visibility_zones={},  # TODO: Calcular grid de visibilidad
            competitors_in_area=competitors_data,
            competitor_density=len(competitors_data) / (math.pi * (radius/1000)**2),
            area_dominance_score=area_dominance,
            previous_heatmap_id=previous_heatmap.id if previous_heatmap else None,
            area_growth_percent=area_growth,
            dominance_change=dominance_change,
            heatmap_data={
                "center": [lead.latitude, lead.longitude],
                "radius": radius,
                "competitors": competitors_data,
                "generated_at": datetime.utcnow().isoformat()
            },
            snapshot_type="monthly",
            created_at=datetime.utcnow()
        )
        
        db.add(heatmap)
        
        # Actualizar contador en suscripción
        subscription.total_heatmaps_generated += 1
        
        db.commit()
        db.refresh(heatmap)
        
        return heatmap
