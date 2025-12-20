'use client';

import { Check, X, TrendingUp } from 'lucide-react';

interface ComparisonData {
  you: {
    score: number;
    reviews: number;
    rating: number;
    photos: number;
    lastUpdate: string;
    website: boolean;
  };
  competitor: {
    score: number;
    reviews: number;
    rating: number;
    photos: number;
    lastUpdate: string;
    website: boolean;
  };
}

interface ComparisonTableProps {
  data: ComparisonData;
}

export default function ComparisonTable({ data }: ComparisonTableProps) {
  const metrics = [
    {
      label: 'Score de Salud',
      you: data.you.score,
      competitor: data.competitor.score,
      suffix: '/100',
      isNumber: true,
    },
    {
      label: 'Número de Reseñas',
      you: data.you.reviews,
      competitor: data.competitor.reviews,
      suffix: '',
      isNumber: true,
    },
    {
      label: 'Rating Promedio',
      you: data.you.rating,
      competitor: data.competitor.rating,
      suffix: '/5.0',
      isNumber: true,
    },
    {
      label: 'Fotos Publicadas',
      you: data.you.photos,
      competitor: data.competitor.photos,
      suffix: '',
      isNumber: true,
    },
    {
      label: 'Última Actualización',
      you: data.you.lastUpdate,
      competitor: data.competitor.lastUpdate,
      suffix: '',
      isNumber: false,
    },
    {
      label: 'Sitio Web Activo',
      you: data.you.website,
      competitor: data.competitor.website,
      suffix: '',
      isBoolean: true,
    },
  ];

  const getWinner = (youValue: any, compValue: any, isBoolean: boolean = false) => {
    if (isBoolean) {
      if (youValue && !compValue) return 'you';
      if (!youValue && compValue) return 'competitor';
      return 'tie';
    }
    
    if (typeof youValue === 'number' && typeof compValue === 'number') {
      if (youValue > compValue) return 'you';
      if (youValue < compValue) return 'competitor';
      return 'tie';
    }
    
    return 'neutral';
  };

  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-blue-100 rounded-xl">
          <TrendingUp className="w-8 h-8 text-blue-600" />
        </div>
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Tú vs. Competencia Directa</h2>
          <p className="text-gray-600">Así es como te ven los clientes comparado con tu competidor más cercano</p>
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="px-4 py-4 text-left text-sm font-semibold text-gray-600 uppercase tracking-wider">
                Métrica
              </th>
              <th className="px-4 py-4 text-center text-sm font-semibold text-red-600 uppercase tracking-wider">
                Tú
              </th>
              <th className="px-4 py-4 text-center text-sm font-semibold text-green-600 uppercase tracking-wider">
                Competencia
              </th>
              <th className="px-4 py-4 text-center text-sm font-semibold text-gray-600 uppercase tracking-wider">
                Diferencia
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {metrics.map((metric, index) => {
              const winner = getWinner(metric.you, metric.competitor, metric.isBoolean);
              const youValue = metric.isBoolean ? (metric.you ? <Check className="w-6 h-6 text-green-500" /> : <X className="w-6 h-6 text-red-500" />) : `${metric.you}${metric.suffix}`;
              const compValue = metric.isBoolean ? (metric.competitor ? <Check className="w-6 h-6 text-green-500" /> : <X className="w-6 h-6 text-red-500" />) : `${metric.competitor}${metric.suffix}`;
              
              let difference = '';
              if (metric.isNumber && typeof metric.you === 'number' && typeof metric.competitor === 'number') {
                const diff = metric.competitor - metric.you;
                difference = diff > 0 ? `+${diff}` : `${diff}`;
              }

              return (
                <tr key={index} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-5 text-sm font-semibold text-gray-900">
                    {metric.label}
                  </td>
                  <td className={`px-4 py-5 text-center ${winner === 'you' ? 'bg-green-50' : winner === 'competitor' ? 'bg-red-50' : ''}`}>
                    <div className="flex justify-center items-center">
                      <span className={`text-lg font-bold ${winner === 'you' ? 'text-green-600' : 'text-red-600'}`}>
                        {youValue}
                      </span>
                    </div>
                  </td>
                  <td className={`px-4 py-5 text-center ${winner === 'competitor' ? 'bg-green-50' : winner === 'you' ? 'bg-red-50' : ''}`}>
                    <div className="flex justify-center items-center">
                      <span className={`text-lg font-bold ${winner === 'competitor' ? 'text-green-600' : 'text-gray-600'}`}>
                        {compValue}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-5 text-center">
                    {difference && (
                      <span className={`text-sm font-bold ${difference.startsWith('+') ? 'text-red-600' : 'text-green-600'}`}>
                        {difference}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Resumen */}
      <div className="mt-6 p-6 bg-gradient-to-r from-orange-50 to-red-50 rounded-2xl border-2 border-orange-200">
        <div className="flex items-start gap-4">
          <div className="text-5xl">⚠️</div>
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">
              Tu competencia te está superando en todos los frentes
            </h3>
            <p className="text-gray-700">
              Mientras lees esto, están capturando el <span className="font-bold text-red-600">67% más de clientes</span> que 
              deberían estar buscándote a ti. Cada hora cuenta.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
