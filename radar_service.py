"""
Radar Lokigi - Sistema de Monitoreo Pasivo para Suscripción Mensual ($29)
Competitor Tracker + Alert Generator + Heatmap Dynamics

Funcionalidades:
- Monitoreo mensual de competidores (re-scraping eficiente)
- Detección de movimientos significativos
- Alertas automáticas por email/WhatsApp
- Actualización de mapas de calor de visibilidad
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
import random


class CompetitorTracker:
    """
    Tracker de competidores - Monitoreo mensual de métricas
    
    Detecta cambios significativos en:
    - Score de visibilidad (+5 puntos)
    - Número de reseñas (+10 reseñas)
    - Fotos nuevas
    - Actualización de sitio web
    """
    
    # Umbrales para detectar movimientos significativos
    SCORE_THRESHOLD = 5  # +5 puntos en score
    REVIEW_THRESHOLD = 10  # +10 reseñas
    PHOTO_THRESHOLD = 5  # +5 fotos nuevas
    
    def __init__(self, db: Session):
        self.db = db
    
    def scan_competitor(
        self,
        lead_id: int,
        competitor_name: str,
        competitor_data: Dict
    ) -> Dict:
        """
        Escanea un competidor y crea snapshot
        
        Args:
            lead_id: ID del lead que monitorea
            competitor_name: Nombre del competidor
            competitor_data: Datos actuales del competidor
            
        Returns:
            Dict con snapshot y cambios detectados
        """
        from models import CompetitorSnapshot
        
        # Buscar último snapshot de este competidor
        last_snapshot = self.db.query(CompetitorSnapshot).filter(
            CompetitorSnapshot.lead_id == lead_id,
            CompetitorSnapshot.competitor_name == competitor_name
        ).order_by(desc(CompetitorSnapshot.created_at)).first()
        
        # Extraer métricas actuales
        current_metrics = {
            "score": competitor_data.get("score", 0),
            "rating": competitor_data.get("rating", 0),
            "review_count": competitor_data.get("review_count", 0),
            "photo_count": competitor_data.get("photo_count", 0),
            "has_website": competitor_data.get("has_website", False)
        }
        
        # Calcular cambios vs último snapshot
        changes = {}
        if last_snapshot:
            prev_data = last_snapshot.snapshot_data
            
            changes = {
                "score_delta": current_metrics["score"] - prev_data.get("score", 0),
                "rating_delta": current_metrics["rating"] - prev_data.get("rating", 0),
                "review_delta": current_metrics["review_count"] - prev_data.get("review_count", 0),
                "photo_delta": current_metrics["photo_count"] - prev_data.get("photo_count", 0),
                "website_added": current_metrics["has_website"] and not prev_data.get("has_website", False),
                "days_since_last_scan": (datetime.utcnow() - last_snapshot.created_at).days
            }
        
        # Crear nuevo snapshot
        new_snapshot = CompetitorSnapshot(
            lead_id=lead_id,
            competitor_name=competitor_name,
            competitor_place_id=competitor_data.get("place_id"),
            score=current_metrics["score"],
            rating=current_metrics["rating"],
            review_count=current_metrics["review_count"],
            photo_count=current_metrics["photo_count"],
            has_website=current_metrics["has_website"],
            snapshot_data=competitor_data,
            changes_detected=changes if changes else None,
            snapshot_type="monthly"
        )
        
        self.db.add(new_snapshot)
        self.db.commit()
        self.db.refresh(new_snapshot)
        
        return {
            "snapshot_id": new_snapshot.id,
            "competitor_name": competitor_name,
            "current_metrics": current_metrics,
            "changes": changes,
            "movement_detected": self._is_significant_movement(changes)
        }
    
    def scan_all_competitors(
        self,
        lead_id: int,
        competitors_data: List[Dict]
    ) -> List[Dict]:
        """
        Escanea todos los competidores de un lead
        
        Args:
            lead_id: ID del lead
            competitors_data: Lista de datos de competidores
            
        Returns:
            Lista de resultados de scans
        """
        results = []
        
        for competitor in competitors_data:
            try:
                result = self.scan_competitor(
                    lead_id=lead_id,
                    competitor_name=competitor.get("name", "Unknown"),
                    competitor_data=competitor
                )
                results.append(result)
            except Exception as e:
                results.append({
                    "competitor_name": competitor.get("name", "Unknown"),
                    "error": str(e),
                    "movement_detected": False
                })
        
        return results
    
    def get_competitor_history(
        self,
        lead_id: int,
        competitor_name: str,
        limit: int = 12  # Últimos 12 meses
    ) -> List[Dict]:
        """
        Obtiene el histórico de snapshots de un competidor
        
        Args:
            lead_id: ID del lead
            competitor_name: Nombre del competidor
            limit: Número máximo de snapshots a retornar
            
        Returns:
            Lista de snapshots ordenados por fecha
        """
        from models import CompetitorSnapshot
        
        snapshots = self.db.query(CompetitorSnapshot).filter(
            CompetitorSnapshot.lead_id == lead_id,
            CompetitorSnapshot.competitor_name == competitor_name
        ).order_by(desc(CompetitorSnapshot.created_at)).limit(limit).all()
        
        history = []
        for snapshot in reversed(snapshots):  # Orden cronológico
            history.append({
                "date": snapshot.created_at.isoformat(),
                "score": snapshot.score,
                "rating": snapshot.rating,
                "review_count": snapshot.review_count,
                "photo_count": snapshot.photo_count,
                "has_website": snapshot.has_website,
                "changes": snapshot.changes_detected
            })
        
        return history
    
    def get_all_competitors_summary(self, lead_id: int) -> Dict:
        """
        Obtiene resumen de todos los competidores monitoreados
        
        Args:
            lead_id: ID del lead
            
        Returns:
            Dict con resumen de competidores
        """
        from models import CompetitorSnapshot
        
        # Obtener últimos snapshots de cada competidor
        latest_snapshots = self.db.query(
            CompetitorSnapshot.competitor_name,
            CompetitorSnapshot
        ).filter(
            CompetitorSnapshot.lead_id == lead_id
        ).order_by(
            CompetitorSnapshot.competitor_name,
            desc(CompetitorSnapshot.created_at)
        ).all()
        
        # Agrupar por competidor (tomar solo el más reciente)
        competitors_dict = {}
        for name, snapshot in latest_snapshots:
            if name not in competitors_dict:
                competitors_dict[name] = snapshot
        
        summary = {
            "total_competitors": len(competitors_dict),
            "competitors": []
        }
        
        for name, snapshot in competitors_dict.items():
            summary["competitors"].append({
                "name": name,
                "current_score": snapshot.score,
                "rating": snapshot.rating,
                "review_count": snapshot.review_count,
                "last_scan": snapshot.created_at.isoformat(),
                "recent_changes": snapshot.changes_detected
            })
        
        return summary
    
    def _is_significant_movement(self, changes: Dict) -> bool:
        """
        Determina si los cambios detectados son significativos
        
        Args:
            changes: Dict con deltas de métricas
            
        Returns:
            True si hay movimiento significativo
        """
        if not changes:
            return False
        
        # Verificar umbrales
        score_moved = abs(changes.get("score_delta", 0)) >= self.SCORE_THRESHOLD
        reviews_grew = changes.get("review_delta", 0) >= self.REVIEW_THRESHOLD
        photos_added = changes.get("photo_delta", 0) >= self.PHOTO_THRESHOLD
        website_added = changes.get("website_added", False)
        
        return score_moved or reviews_grew or photos_added or website_added


class AlertGenerator:
    """
    Generador de alertas automáticas
    
    Tipos de alertas:
    - competitor_movement: Competidor mejoró significativamente
    - market_shift: Cambios generales en el mercado
    - position_risk: Tu posición está en riesgo
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_alerts_from_scan(
        self,
        lead_id: int,
        scan_results: List[Dict]
    ) -> List[Dict]:
        """
        Genera alertas basadas en resultados de scan de competidores
        
        Args:
            lead_id: ID del lead
            scan_results: Resultados del scan de CompetitorTracker
            
        Returns:
            Lista de alertas generadas
        """
        from models import RadarAlert
        
        alerts_created = []
        
        for result in scan_results:
            if not result.get("movement_detected"):
                continue
            
            competitor_name = result.get("competitor_name")
            changes = result.get("changes", {})
            
            # Determinar severidad y tipo de alerta
            severity, alert_type = self._classify_movement(changes)
            
            # Generar título y mensaje
            title = self._generate_alert_title(competitor_name, changes)
            message = self._generate_alert_message(competitor_name, changes)
            recommendations = self._generate_recommendations(changes)
            
            # Crear alerta en base de datos
            alert = RadarAlert(
                lead_id=lead_id,
                alert_type=alert_type,
                severity=severity,
                competitor_name=competitor_name,
                competitor_snapshot_id=result.get("snapshot_id"),
                title=title,
                message=message,
                trigger_data=changes,
                recommendations=recommendations,
                status="pending"
            )
            
            self.db.add(alert)
            alerts_created.append({
                "title": title,
                "message": message,
                "severity": severity,
                "competitor": competitor_name
            })
        
        self.db.commit()
        
        return alerts_created
    
    def get_pending_alerts(self, lead_id: int) -> List[Dict]:
        """
        Obtiene alertas pendientes de un lead
        
        Args:
            lead_id: ID del lead
            
        Returns:
            Lista de alertas pendientes
        """
        from models import RadarAlert
        
        alerts = self.db.query(RadarAlert).filter(
            RadarAlert.lead_id == lead_id,
            RadarAlert.status == "pending"
        ).order_by(desc(RadarAlert.created_at)).all()
        
        return [self._alert_to_dict(alert) for alert in alerts]
    
    def mark_alert_as_sent(self, alert_id: int, channels: List[str]):
        """
        Marca una alerta como enviada
        
        Args:
            alert_id: ID de la alerta
            channels: Canales por los que se envió ["email", "whatsapp"]
        """
        from models import RadarAlert
        
        alert = self.db.query(RadarAlert).filter(RadarAlert.id == alert_id).first()
        if alert:
            alert.notification_sent = True
            alert.notification_sent_at = datetime.utcnow()
            alert.notification_channels = channels
            alert.status = "sent"
            self.db.commit()
    
    def _classify_movement(self, changes: Dict) -> Tuple[str, str]:
        """
        Clasifica el movimiento del competidor en severidad y tipo
        
        Returns:
            (severity, alert_type)
        """
        score_delta = changes.get("score_delta", 0)
        review_delta = changes.get("review_delta", 0)
        photo_delta = changes.get("photo_delta", 0)
        
        # Critical: Múltiples mejoras grandes
        if score_delta >= 10 or review_delta >= 20:
            return ("critical", "position_risk")
        
        # Warning: Mejora significativa
        if score_delta >= 5 or review_delta >= 10 or photo_delta >= 5:
            return ("warning", "competitor_movement")
        
        # Info: Cambios menores
        return ("info", "competitor_movement")
    
    def _generate_alert_title(self, competitor_name: str, changes: Dict) -> str:
        """Genera título de la alerta"""
        score_delta = changes.get("score_delta", 0)
        
        if score_delta >= 10:
            return f"🚨 Alerta Lokigi: {competitor_name} creció {score_delta} puntos"
        elif score_delta >= 5:
            return f"⚠️ Alerta Lokigi: {competitor_name} se está moviendo"
        else:
            return f"📊 Actualización: {competitor_name} está activo"
    
    def _generate_alert_message(self, competitor_name: str, changes: Dict) -> str:
        """Genera mensaje detallado de la alerta"""
        parts = [f"{competitor_name} ha realizado mejoras significativas:"]
        
        score_delta = changes.get("score_delta", 0)
        if score_delta > 0:
            parts.append(f"- Score de visibilidad: +{score_delta} puntos")
        
        review_delta = changes.get("review_delta", 0)
        if review_delta > 0:
            parts.append(f"- Nuevas reseñas: +{review_delta}")
        
        photo_delta = changes.get("photo_delta", 0)
        if photo_delta > 0:
            parts.append(f"- Fotos nuevas: +{photo_delta}")
        
        if changes.get("website_added"):
            parts.append("- ✅ Agregaron sitio web")
        
        parts.append(f"\n⚠️ Tu posición competitiva está en riesgo. Revisa tu perfil ahora.")
        
        return "\n".join(parts)
    
    def _generate_recommendations(self, changes: Dict) -> List[str]:
        """Genera recomendaciones basadas en los cambios"""
        recs = []
        
        if changes.get("review_delta", 0) >= 10:
            recs.append("Aumenta tu campaña de reseñas para no quedar atrás")
        
        if changes.get("photo_delta", 0) >= 5:
            recs.append("Actualiza tus fotos de negocio esta semana")
        
        if changes.get("score_delta", 0) >= 5:
            recs.append("Considera contratar el servicio de optimización SEO ($99)")
        
        if changes.get("website_added"):
            recs.append("Si no tienes sitio web, créalo urgentemente")
        
        if not recs:
            recs.append("Mantén tu perfil actualizado constantemente")
        
        return recs
    
    def _alert_to_dict(self, alert) -> Dict:
        """Convierte modelo de alerta a dict"""
        return {
            "id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity,
            "alert_type": alert.alert_type,
            "competitor_name": alert.competitor_name,
            "trigger_data": alert.trigger_data,
            "recommendations": alert.recommendations,
            "status": alert.status,
            "notification_sent": alert.notification_sent,
            "created_at": alert.created_at.isoformat()
        }


class HeatmapGenerator:
    """
    Generador de mapas de calor de visibilidad
    
    Actualiza mapas cada 30 días mostrando:
    - Área de influencia del negocio
    - Densidad de competidores
    - Score de dominancia en la zona
    - Crecimiento/reducción del área
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_heatmap(
        self,
        lead_id: int,
        business_coordinates: Tuple[float, float],
        business_score: float,
        competitors_data: List[Dict]
    ) -> Dict:
        """
        Genera mapa de calor de visibilidad
        
        Args:
            lead_id: ID del lead
            business_coordinates: (lat, lng) del negocio
            business_score: Score del negocio
            competitors_data: Lista de competidores con coordenadas y scores
            
        Returns:
            Dict con datos del heatmap generado
        """
        from models import VisibilityHeatmap
        
        # Calcular radio de influencia basado en score
        radius_meters = self._calculate_influence_radius(business_score)
        
        # Calcular densidad de competidores
        competitors_in_radius = self._filter_competitors_in_radius(
            business_coordinates,
            competitors_data,
            radius_meters
        )
        
        area_km2 = (radius_meters / 1000) ** 2 * 3.14159
        competitor_density = len(competitors_in_radius) / area_km2 if area_km2 > 0 else 0
        
        # Calcular score de dominancia
        dominance_score = self._calculate_dominance_score(
            business_score,
            competitors_in_radius
        )
        
        # Generar grid de visibilidad
        visibility_zones = self._generate_visibility_grid(
            business_coordinates,
            business_score,
            competitors_in_radius,
            radius_meters
        )
        
        # Buscar heatmap anterior para comparación
        previous_heatmap = self.db.query(VisibilityHeatmap).filter(
            VisibilityHeatmap.lead_id == lead_id
        ).order_by(desc(VisibilityHeatmap.created_at)).first()
        
        # Calcular cambios
        area_growth = None
        dominance_change = None
        previous_id = None
        
        if previous_heatmap:
            previous_id = previous_heatmap.id
            area_growth = ((radius_meters - previous_heatmap.radius_meters) / 
                          previous_heatmap.radius_meters * 100)
            dominance_change = dominance_score - previous_heatmap.area_dominance_score
        
        # Preparar datos completos del heatmap
        heatmap_data = {
            "business_coordinates": list(business_coordinates),
            "business_score": business_score,
            "radius_meters": radius_meters,
            "competitors_count": len(competitors_in_radius),
            "competitor_density": round(competitor_density, 2),
            "dominance_score": dominance_score,
            "visibility_zones": visibility_zones,
            "competitors": competitors_in_radius,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Crear nuevo heatmap en BD
        new_heatmap = VisibilityHeatmap(
            lead_id=lead_id,
            center_coordinates=list(business_coordinates),
            radius_meters=radius_meters,
            visibility_zones=visibility_zones,
            competitors_in_area=competitors_in_radius,
            competitor_density=competitor_density,
            area_dominance_score=dominance_score,
            previous_heatmap_id=previous_id,
            area_growth_percent=area_growth,
            dominance_change=dominance_change,
            heatmap_data=heatmap_data,
            snapshot_type="monthly"
        )
        
        self.db.add(new_heatmap)
        self.db.commit()
        self.db.refresh(new_heatmap)
        
        return {
            "heatmap_id": new_heatmap.id,
            "radius_meters": radius_meters,
            "area_growth_percent": area_growth,
            "dominance_score": dominance_score,
            "dominance_change": dominance_change,
            "competitor_density": competitor_density,
            "heatmap_data": heatmap_data
        }
    
    def get_latest_heatmap(self, lead_id: int) -> Optional[Dict]:
        """Obtiene el heatmap más reciente de un lead"""
        from models import VisibilityHeatmap
        
        heatmap = self.db.query(VisibilityHeatmap).filter(
            VisibilityHeatmap.lead_id == lead_id
        ).order_by(desc(VisibilityHeatmap.created_at)).first()
        
        if not heatmap:
            return None
        
        return {
            "id": heatmap.id,
            "created_at": heatmap.created_at.isoformat(),
            "radius_meters": heatmap.radius_meters,
            "dominance_score": heatmap.area_dominance_score,
            "area_growth_percent": heatmap.area_growth_percent,
            "dominance_change": heatmap.dominance_change,
            "competitor_density": heatmap.competitor_density,
            "heatmap_data": heatmap.heatmap_data
        }
    
    def _calculate_influence_radius(self, business_score: float) -> float:
        """
        Calcula radio de influencia basado en score
        Score alto = mayor radio de influencia
        
        Returns:
            Radio en metros
        """
        # Score 100 = 2km, Score 50 = 1km, Score 0 = 500m
        min_radius = 500
        max_radius = 2000
        
        radius = min_radius + (business_score / 100) * (max_radius - min_radius)
        return radius
    
    def _filter_competitors_in_radius(
        self,
        center: Tuple[float, float],
        competitors: List[Dict],
        radius_meters: float
    ) -> List[Dict]:
        """Filtra competidores dentro del radio de influencia"""
        from data_quality_service import NAPEvaluator
        
        evaluator = NAPEvaluator()
        competitors_in_radius = []
        
        for comp in competitors:
            if "coordinates" not in comp:
                continue
            
            comp_coords = tuple(comp["coordinates"])
            distance = evaluator._calculate_haversine_distance(center, comp_coords)
            
            if distance <= radius_meters:
                competitors_in_radius.append({
                    "name": comp.get("name"),
                    "coordinates": comp["coordinates"],
                    "score": comp.get("score", 0),
                    "distance_meters": round(distance, 2)
                })
        
        return competitors_in_radius
    
    def _calculate_dominance_score(
        self,
        business_score: float,
        competitors: List[Dict]
    ) -> float:
        """
        Calcula qué tan dominante es el negocio en su área
        
        Considera:
        - Score del negocio vs promedio de competidores
        - Número de competidores
        
        Returns:
            Score 0-100
        """
        if not competitors:
            return 100.0  # Sin competencia = máxima dominancia
        
        # Score promedio de competidores
        avg_competitor_score = sum(c.get("score", 0) for c in competitors) / len(competitors)
        
        # Dominancia relativa
        if avg_competitor_score == 0:
            relative_dominance = 100
        else:
            relative_dominance = (business_score / avg_competitor_score) * 100
            relative_dominance = min(relative_dominance, 100)  # Cap at 100
        
        # Penalizar por alta densidad de competidores
        density_penalty = min(len(competitors) * 5, 30)  # Max 30% penalty
        
        dominance = relative_dominance - density_penalty
        dominance = max(dominance, 0)  # Min 0
        
        return round(dominance, 2)
    
    def _generate_visibility_grid(
        self,
        center: Tuple[float, float],
        business_score: float,
        competitors: List[Dict],
        radius_meters: float
    ) -> List[Dict]:
        """
        Genera grid de zonas con scores de visibilidad
        Divide el área en 9 zonas (3x3 grid)
        
        Returns:
            Lista de zonas con sus scores
        """
        # Grid simple: 9 zonas (N, NE, E, SE, S, SW, W, NW, CENTER)
        directions = [
            {"name": "N", "offset": (0.005, 0)},
            {"name": "NE", "offset": (0.004, 0.004)},
            {"name": "E", "offset": (0, 0.005)},
            {"name": "SE", "offset": (-0.004, 0.004)},
            {"name": "S", "offset": (-0.005, 0)},
            {"name": "SW", "offset": (-0.004, -0.004)},
            {"name": "W", "offset": (0, -0.005)},
            {"name": "NW", "offset": (0.004, -0.004)},
            {"name": "CENTER", "offset": (0, 0)}
        ]
        
        zones = []
        for direction in directions:
            zone_center = (
                center[0] + direction["offset"][0],
                center[1] + direction["offset"][1]
            )
            
            # Calcular score de la zona (basado en distancia al negocio y competidores)
            zone_score = self._calculate_zone_score(
                zone_center,
                center,
                business_score,
                competitors
            )
            
            zones.append({
                "direction": direction["name"],
                "coordinates": zone_center,
                "visibility_score": zone_score
            })
        
        return zones
    
    def _calculate_zone_score(
        self,
        zone_center: Tuple[float, float],
        business_center: Tuple[float, float],
        business_score: float,
        competitors: List[Dict]
    ) -> float:
        """Calcula score de visibilidad de una zona específica"""
        from data_quality_service import NAPEvaluator
        
        evaluator = NAPEvaluator()
        
        # Distancia de la zona al negocio
        distance_to_business = evaluator._calculate_haversine_distance(
            zone_center,
            business_center
        )
        
        # Score base: Mayor distancia = menor visibilidad
        base_score = business_score * (1 - min(distance_to_business / 2000, 0.5))
        
        # Penalizar por competidores cercanos a la zona
        competition_penalty = 0
        for comp in competitors:
            comp_coords = tuple(comp["coordinates"])
            distance_to_comp = evaluator._calculate_haversine_distance(
                zone_center,
                comp_coords
            )
            
            if distance_to_comp < 500:  # Competidor muy cerca de la zona
                competition_penalty += 10
        
        zone_score = base_score - competition_penalty
        zone_score = max(zone_score, 0)
        
        return round(zone_score, 2)
