"use client";

import { useEffect, useState } from "react";
import { TrendingUp, AlertTriangle, MapPin, DollarSign, Target, Star } from "lucide-react";

interface CriticalIssue {
  titulo: string;
  descripcion: string;
  impacto_economico: string;
}

interface AuditData {
  score_visibilidad: number;
  fallos_criticos: CriticalIssue[];
  lucro_cesante_mensual: number;
  lucro_cesante_anual: number;
  business_coordinates?: [number, number];
  competitors_nearby?: Array<{
    name: string;
    distance: number;
    score: number;
  }>;
}

interface ReportCardProps {
  leadId: number;
  auditData?: AuditData;
  loading?: boolean;
}

export default function ReportCard({ leadId, auditData, loading = false }: ReportCardProps) {
  const [data, setData] = useState<AuditData | null>(auditData || null);
  const [isLoading, setIsLoading] = useState(loading);

  useEffect(() => {
    if (!auditData && leadId) {
      fetchAuditData();
    }
  }, [leadId, auditData]);

  const fetchAuditData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/audit/${leadId}`);
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error("Error fetching audit data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="w-full max-w-6xl mx-auto p-8">
        <div className="animate-pulse space-y-6">
          <div className="h-48 bg-gray-800 rounded-lg"></div>
          <div className="h-64 bg-gray-800 rounded-lg"></div>
          <div className="h-96 bg-gray-800 rounded-lg"></div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="w-full max-w-6xl mx-auto p-8 text-center text-gray-400">
        No audit data available
      </div>
    );
  }

  // Determinar color según score
  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-400 border-green-500";
    if (score >= 60) return "text-yellow-400 border-yellow-500";
    if (score >= 40) return "text-orange-400 border-orange-500";
    return "text-red-400 border-red-500";
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return "Excelente";
    if (score >= 60) return "Bueno";
    if (score >= 40) return "Regular";
    return "Crítico";
  };

  const scoreColor = getScoreColor(data.score_visibilidad);
  const scoreLabel = getScoreLabel(data.score_visibilidad);

  // Calcular porcentaje para el círculo
  const circumference = 2 * Math.PI * 70;
  const progress = (data.score_visibilidad / 100) * circumference;

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Header: Lokigi Score Gauge */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 border border-gray-700 shadow-2xl">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Left: Score Gauge */}
          <div className="flex flex-col items-center justify-center">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
              <Target className="w-8 h-8 text-neon-500" />
              Lokigi Score
            </h2>
            
            {/* Circular Progress */}
            <div className="relative w-48 h-48">
              <svg className="transform -rotate-90 w-48 h-48">
                {/* Background circle */}
                <circle
                  cx="96"
                  cy="96"
                  r="70"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="transparent"
                  className="text-gray-700"
                />
                {/* Progress circle */}
                <circle
                  cx="96"
                  cy="96"
                  r="70"
                  stroke="currentColor"
                  strokeWidth="12"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={circumference - progress}
                  className={`${scoreColor.split(" ")[0]} transition-all duration-1000 ease-out`}
                  strokeLinecap="round"
                />
              </svg>
              
              {/* Score number in center */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-6xl font-bold ${scoreColor.split(" ")[0]}`}>
                  {data.score_visibilidad}
                </span>
                <span className="text-gray-400 text-sm mt-1">/100</span>
                <span className={`text-sm font-semibold mt-2 ${scoreColor.split(" ")[0]}`}>
                  {scoreLabel}
                </span>
              </div>
            </div>

            <p className="text-gray-400 text-center mt-4 max-w-xs">
              Tu índice de visibilidad local en comparación con la competencia
            </p>
          </div>

          {/* Right: Lucro Cesante (Lost Revenue) */}
          <div className="flex flex-col justify-center space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-red-400" />
                Lucro Cesante (Dinero que estás perdiendo)
              </h3>
              <p className="text-gray-400 text-sm mb-4">
                Estimación de ingresos perdidos por baja visibilidad
              </p>
            </div>

            {/* Monthly Loss */}
            <div className="bg-red-900 bg-opacity-20 border border-red-500 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-300 text-sm font-medium mb-1">Pérdida Mensual</p>
                  <p className="text-4xl font-bold text-red-400">
                    ${data.lucro_cesante_mensual.toLocaleString()}
                  </p>
                </div>
                <TrendingUp className="w-12 h-12 text-red-400 opacity-50" />
              </div>
            </div>

            {/* Annual Loss */}
            <div className="bg-red-900 bg-opacity-30 border border-red-600 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-200 text-sm font-medium mb-1">Pérdida Anual</p>
                  <p className="text-5xl font-bold text-red-300">
                    ${data.lucro_cesante_anual.toLocaleString()}
                  </p>
                </div>
                <AlertTriangle className="w-12 h-12 text-red-300 opacity-50" />
              </div>
              <p className="text-red-200 text-xs mt-3 opacity-75">
                Si no se corrige en los próximos 12 meses
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Critical Issues Grid */}
      {data.fallos_criticos && data.fallos_criticos.length > 0 && (
        <div className="bg-gray-900 rounded-2xl p-8 border border-red-500 shadow-xl">
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <AlertTriangle className="w-7 h-7 text-red-400" />
            Fallos Críticos Detectados
          </h3>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.fallos_criticos.map((issue, index) => (
              <div
                key={index}
                className="bg-gray-800 border border-red-600 rounded-lg p-5 hover:border-red-400 transition-all duration-300 hover:shadow-lg hover:shadow-red-500/20"
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-red-500 bg-opacity-20 rounded-full flex items-center justify-center">
                    <span className="text-red-400 font-bold text-sm">{index + 1}</span>
                  </div>
                  <h4 className="text-white font-semibold text-sm leading-tight">
                    {issue.titulo}
                  </h4>
                </div>
                
                <p className="text-gray-400 text-xs mb-3 leading-relaxed">
                  {issue.descripcion}
                </p>
                
                <div className="bg-red-900 bg-opacity-30 rounded-md p-2 border-l-4 border-red-500">
                  <p className="text-red-300 text-xs font-semibold">
                    💰 {issue.impacto_economico}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Heatmap: Competitor Proximity */}
      {data.business_coordinates && data.competitors_nearby && (
        <div className="bg-gray-900 rounded-2xl p-8 border border-neon-500 shadow-xl shadow-neon-500/10">
          <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
            <MapPin className="w-7 h-7 text-neon-500" />
            Mapa de Calor: Competidores Cercanos
          </h3>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Left: Your Business */}
            <div className="bg-gradient-to-br from-neon-500 to-neon-600 rounded-lg p-6 shadow-lg">
              <div className="flex items-center gap-3 mb-3">
                <Star className="w-6 h-6 text-white" />
                <h4 className="text-white font-bold">Tu Negocio</h4>
              </div>
              <div className="space-y-2">
                <p className="text-white text-sm">
                  📍 Lat: {data.business_coordinates[0].toFixed(4)}
                </p>
                <p className="text-white text-sm">
                  📍 Lng: {data.business_coordinates[1].toFixed(4)}
                </p>
                <p className="text-white text-lg font-bold mt-3">
                  Score: {data.score_visibilidad}/100
                </p>
              </div>
            </div>

            {/* Right: Competitors List */}
            <div className="md:col-span-2 space-y-3">
              {data.competitors_nearby.map((competitor, idx) => {
                // Color según cercanía (más cerca = más rojo)
                const distanceColor =
                  competitor.distance < 500
                    ? "border-red-500 bg-red-900"
                    : competitor.distance < 1000
                    ? "border-orange-500 bg-orange-900"
                    : "border-yellow-500 bg-yellow-900";

                return (
                  <div
                    key={idx}
                    className={`${distanceColor} bg-opacity-20 border rounded-lg p-4 flex items-center justify-between hover:bg-opacity-30 transition`}
                  >
                    <div>
                      <h5 className="text-white font-semibold">{competitor.name}</h5>
                      <p className="text-gray-400 text-sm">
                        📍 {competitor.distance}m de distancia
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-bold text-lg">{competitor.score}</p>
                      <p className="text-gray-400 text-xs">Score</p>
                    </div>
                  </div>
                );
              })}

              {data.competitors_nearby.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <MapPin className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No se detectaron competidores en un radio de 2km</p>
                </div>
              )}
            </div>
          </div>

          {/* Heatmap Legend */}
          <div className="mt-6 flex items-center gap-6 justify-center">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-red-500"></div>
              <span className="text-gray-400 text-sm">{"< 500m"}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-orange-500"></div>
              <span className="text-gray-400 text-sm">500m - 1km</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-yellow-500"></div>
              <span className="text-gray-400 text-sm">{"> 1km"}</span>
            </div>
          </div>
        </div>
      )}

      {/* CTA Footer */}
      <div className="bg-gradient-to-r from-neon-500 to-green-500 rounded-2xl p-8 text-center shadow-2xl shadow-neon-500/20">
        <h3 className="text-3xl font-bold text-white mb-3">
          🚀 ¿Listo para mejorar tu visibilidad?
        </h3>
        <p className="text-white text-lg mb-6 opacity-90">
          Nuestro servicio Premium ($99) corrige estos fallos en 48 horas
        </p>
        <button className="bg-white text-gray-900 font-bold py-4 px-10 rounded-lg hover:bg-gray-100 transition-all transform hover:scale-105 shadow-lg">
          Contratar Servicio Premium →
        </button>
        <p className="text-white text-sm mt-4 opacity-75">
          ✅ Garantía de mejora mínima de +15 puntos
        </p>
      </div>
    </div>
  );
}
