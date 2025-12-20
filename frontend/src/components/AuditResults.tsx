'use client';

import { AlertCircle, TrendingDown, Globe, Image, Star, Zap } from 'lucide-react';
import HealthScoreChart from './HealthScoreChart';
import CriticalPoints from './CriticalPoints';
import ComparisonTable from './ComparisonTable';
import CTACard from './CTACard';

interface AuditResultsProps {
  auditData: {
    lead: {
      id: number;
      email: string;
      nombre_negocio: string;
    };
    datos_analizados: {
      nombre: string;
      rating: number;
      numero_resenas: number;
      tiene_sitio_web: boolean;
      fecha_ultima_foto: string;
    };
    reporte: {
      fallos_criticos: Array<{
        titulo: string;
        descripcion: string;
        impacto_economico: string;
      }>;
      score_visibilidad: number;
    };
    oferta_plan_express: boolean;
  };
  onCheckout: () => void;
  isCheckoutLoading?: boolean;
}

export default function AuditResults({ auditData, onCheckout, isCheckoutLoading = false }: AuditResultsProps) {
  const { lead, datos_analizados, reporte, oferta_plan_express } = auditData;

  // Mapear los fallos con iconos
  const criticalPointsWithIcons = reporte.fallos_criticos.map((fallo, index) => {
    const iconMap = [AlertCircle, Globe, Image];
    return {
      id: index + 1,
      title: fallo.titulo,
      description: fallo.descripcion,
      impact: fallo.impacto_economico,
      icon: iconMap[index] || AlertCircle,
      severity: 'critical' as const,
    };
  });

  // Datos de comparación simulados
  const comparison = {
    you: {
      score: reporte.score_visibilidad,
      reviews: datos_analizados.numero_resenas,
      rating: datos_analizados.rating,
      photos: 12,
      lastUpdate: '540 días',
      website: datos_analizados.tiene_sitio_web,
    },
    competitor: {
      score: 78,
      reviews: 234,
      rating: 4.6,
      photos: 89,
      lastUpdate: '3 días',
      website: true,
    }
  };
  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="inline-block px-4 py-2 bg-red-100 text-red-700 rounded-full text-sm font-semibold">
          🚨 Auditoría Completada
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900">
          {datos_analizados.nombre}
        </h1>
        <p className="text-xl text-gray-600">
          Resultados de tu Auditoría de SEO Local
        </p>
      </div>

      {/* Score Section */}
      <div className="grid md:grid-cols-2 gap-8">
        <HealthScoreChart score={reporte.score_visibilidad} />
        
        {/* Quick Stats */}
        <div className="card space-y-4">
          <h3 className="text-2xl font-bold text-gray-900">Diagnóstico Rápido</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-4 bg-red-50 rounded-xl">
              <div className="flex items-center gap-3">
                <AlertCircle className="w-6 h-6 text-red-500" />
                <span className="font-semibold text-gray-900">Fallos Críticos</span>
              </div>
              <span className="text-2xl font-bold text-red-600">{reporte.fallos_criticos.length}</span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-orange-50 rounded-xl">
              <div className="flex items-center gap-3">
                <TrendingDown className="w-6 h-6 text-orange-500" />
                <span className="font-semibold text-gray-900">Pérdida Mensual</span>
              </div>
              <span className="text-2xl font-bold text-orange-600">$5,100</span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-xl">
              <div className="flex items-center gap-3">
                <Star className="w-6 h-6 text-blue-500" />
                <span className="font-semibold text-gray-900">Rating Actual</span>
              </div>
              <span className="text-2xl font-bold text-blue-600">{datos_analizados.rating}/5.0</span>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Points */}
      <CriticalPoints points={criticalPointsWithIcons} />

      {/* Comparison Table */}
      <ComparisonTable data={comparison} />

      {/* CTA Card - Solo si el score es menor a 50 */}
      {oferta_plan_express && (
        <CTACard 
          leadId={lead.id} 
          onCheckout={onCheckout}
          isLoading={isCheckoutLoading}
        />
      )}

      {/* Footer Info */}
      <div className="card bg-gradient-to-r from-gray-900 to-gray-800 text-white">
        <div className="flex items-start gap-4">
          <Zap className="w-8 h-8 text-yellow-400 flex-shrink-0" />
          <div>
            <h3 className="text-xl font-bold mb-2">¿Por qué actuar ahora?</h3>
            <p className="text-gray-300">
              Cada día que pasa sin optimizar tu presencia local, tus competidores están capturando 
              a los clientes que deberían ser tuyos. El 76% de las personas que buscan algo cercano 
              en su móvil visitan un negocio en 24 horas. <span className="text-yellow-400 font-semibold">
              No dejes que sean ellos y no tú.</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
