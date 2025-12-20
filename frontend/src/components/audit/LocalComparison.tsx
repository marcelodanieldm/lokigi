'use client';

import { TrendingUp, TrendingDown, Minus, Crown, Target } from 'lucide-react';

interface CompetitorMetrics {
  reviews: number;
  rating: number;
  hasPhotos: boolean;
  hasWebsite: boolean;
  responseRate: number;
}

interface LocalComparisonProps {
  userMetrics: CompetitorMetrics & { businessName: string };
  avgCompetitor: CompetitorMetrics;
}

export default function LocalComparison({ userMetrics, avgCompetitor }: LocalComparisonProps) {
  const metrics = [
    {
      label: 'Número de Reseñas',
      user: userMetrics.reviews,
      competitor: avgCompetitor.reviews,
      format: (val: number) => val.toString(),
      icon: '💬'
    },
    {
      label: 'Calificación Promedio',
      user: userMetrics.rating,
      competitor: avgCompetitor.rating,
      format: (val: number) => `${val.toFixed(1)}★`,
      icon: '⭐'
    },
    {
      label: 'Galería de Fotos',
      user: userMetrics.hasPhotos ? 100 : 0,
      competitor: avgCompetitor.hasPhotos ? 100 : 0,
      format: (val: number) => val > 0 ? 'Sí' : 'No',
      icon: '📸'
    },
    {
      label: 'Sitio Web Activo',
      user: userMetrics.hasWebsite ? 100 : 0,
      competitor: avgCompetitor.hasWebsite ? 100 : 0,
      format: (val: number) => val > 0 ? 'Sí' : 'No',
      icon: '🌐'
    },
    {
      label: 'Tasa de Respuesta',
      user: userMetrics.responseRate,
      competitor: avgCompetitor.responseRate,
      format: (val: number) => `${val}%`,
      icon: '💬'
    },
  ];

  const getComparisonIcon = (user: number, competitor: number) => {
    if (user > competitor) return <TrendingUp className="w-5 h-5 text-green-500" />;
    if (user < competitor) return <TrendingDown className="w-5 h-5 text-red-500" />;
    return <Minus className="w-5 h-5 text-gray-400" />;
  };

  const getPerformanceColor = (user: number, competitor: number) => {
    if (user > competitor) return 'bg-green-50 border-green-200';
    if (user < competitor) return 'bg-red-50 border-red-200';
    return 'bg-gray-50 border-gray-200';
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-blue-500/10 rounded-xl">
            <Target className="w-8 h-8 text-blue-600" />
          </div>
          <div>
            <h2 className="text-3xl font-black text-gray-900">Análisis Competitivo Local</h2>
            <p className="text-gray-600 mt-1">Cómo te ven los clientes vs. tu competencia en 1km a la redonda</p>
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="bg-white rounded-2xl shadow-lg overflow-hidden border-2 border-gray-100">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 bg-gradient-to-r from-gray-900 to-gray-800 text-white p-6">
          <div className="col-span-5 font-bold text-lg">Métrica</div>
          <div className="col-span-3 text-center">
            <div className="flex items-center justify-center gap-2">
              <Crown className="w-5 h-5 text-yellow-400" />
              <span className="font-bold">Tú</span>
            </div>
          </div>
          <div className="col-span-3 text-center font-bold">Competencia Promedio</div>
          <div className="col-span-1 text-center font-bold">Δ</div>
        </div>

        {/* Table Rows */}
        <div className="divide-y divide-gray-200">
          {metrics.map((metric, index) => {
            const diff = metric.user - metric.competitor;
            const diffPercent = metric.competitor > 0 
              ? Math.round((diff / metric.competitor) * 100) 
              : 0;

            return (
              <div
                key={index}
                className={`grid grid-cols-12 gap-4 p-6 hover:bg-gray-50 transition-colors ${
                  index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                }`}
              >
                {/* Metric Name */}
                <div className="col-span-5 flex items-center gap-3">
                  <span className="text-2xl">{metric.icon}</span>
                  <span className="font-semibold text-gray-900">{metric.label}</span>
                </div>

                {/* User Value */}
                <div className="col-span-3 flex items-center justify-center">
                  <div className={`px-4 py-2 rounded-xl border-2 ${getPerformanceColor(metric.user, metric.competitor)}`}>
                    <span className="text-xl font-bold text-gray-900">
                      {metric.format(metric.user)}
                    </span>
                  </div>
                </div>

                {/* Competitor Value */}
                <div className="col-span-3 flex items-center justify-center">
                  <div className="px-4 py-2 rounded-xl bg-blue-50 border-2 border-blue-200">
                    <span className="text-xl font-bold text-blue-900">
                      {metric.format(metric.competitor)}
                    </span>
                  </div>
                </div>

                {/* Comparison Icon */}
                <div className="col-span-1 flex items-center justify-center">
                  {getComparisonIcon(metric.user, metric.competitor)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary Card */}
      <div className="mt-6 bg-gradient-to-br from-orange-50 to-red-50 border-2 border-orange-200 rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="text-5xl">⚠️</div>
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              Tu competencia te está superando en métricas clave
            </h3>
            <p className="text-gray-700 leading-relaxed">
              Los negocios en tu zona con mejor presencia online están capturando el{' '}
              <span className="font-bold text-red-600">67% más de clientes potenciales</span>. 
              Mientras lees esto, tus competidores están recibiendo llamadas, visitas y ventas 
              que deberían ser tuyas.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
