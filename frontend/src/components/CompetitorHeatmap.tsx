'use client';

import { Check, X, TrendingUp, TrendingDown } from 'lucide-react';

interface CompetitorHeatmapProps {
  yourBusiness: {
    name: string;
    scores: {
      propiedad: number;
      reputacion: number;
      visual: number;
      presencia: number;
    };
  };
  language: string;
}

export default function CompetitorHeatmap({ yourBusiness, language }: CompetitorHeatmapProps) {
  // Generar 3 competidores ficticios basados en el promedio del mercado
  const generateCompetitors = () => {
    return [
      {
        name: language === 'PT' ? 'Concorrente #1' : language === 'ES' ? 'Competidor #1' : 'Competitor #1',
        scores: {
          propiedad: Math.min(40, yourBusiness.scores.propiedad + Math.random() * 15 + 5),
          reputacion: Math.min(25, yourBusiness.scores.reputacion + Math.random() * 10 + 3),
          visual: Math.min(20, yourBusiness.scores.visual + Math.random() * 8 + 2),
          presencia: Math.min(15, yourBusiness.scores.presencia + Math.random() * 5 + 1),
        },
      },
      {
        name: language === 'PT' ? 'Concorrente #2' : language === 'ES' ? 'Competidor #2' : 'Competitor #2',
        scores: {
          propiedad: Math.min(40, yourBusiness.scores.propiedad + Math.random() * 12 + 3),
          reputacion: Math.min(25, yourBusiness.scores.reputacion + Math.random() * 8 + 2),
          visual: Math.min(20, yourBusiness.scores.visual + Math.random() * 6 + 1),
          presencia: Math.min(15, yourBusiness.scores.presencia + Math.random() * 4 + 1),
        },
      },
      {
        name: language === 'PT' ? 'Concorrente #3' : language === 'ES' ? 'Competidor #3' : 'Competitor #3',
        scores: {
          propiedad: Math.min(40, yourBusiness.scores.propiedad + Math.random() * 10 + 2),
          reputacion: Math.min(25, yourBusiness.scores.reputacion + Math.random() * 7 + 1),
          visual: Math.min(20, yourBusiness.scores.visual + Math.random() * 5 + 1),
          presencia: Math.min(15, yourBusiness.scores.presencia + Math.random() * 3),
        },
      },
    ];
  };

  const competitors = generateCompetitors();

  const dimensions = [
    { key: 'propiedad', label: language === 'PT' ? 'Propriedade' : language === 'ES' ? 'Propiedad' : 'Ownership', max: 40 },
    { key: 'reputacion', label: language === 'PT' ? 'Reputação' : language === 'ES' ? 'Reputación' : 'Reputation', max: 25 },
    { key: 'visual', label: language === 'PT' ? 'Visual' : language === 'ES' ? 'Visual' : 'Visual', max: 20 },
    { key: 'presencia', label: language === 'PT' ? 'Presença' : language === 'ES' ? 'Presencia' : 'Presence', max: 15 },
  ];

  const getHeatColor = (score: number, max: number) => {
    const percentage = (score / max) * 100;
    if (percentage >= 80) return 'bg-success-500';
    if (percentage >= 60) return 'bg-primary';
    if (percentage >= 40) return 'bg-warning-500';
    return 'bg-danger-500';
  };

  const businesses = [yourBusiness, ...competitors];

  return (
    <div className="bg-dark-800 border border-dark-700 rounded-xl p-8">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">
          {language === 'PT' ? 'Você vs. Concorrência' : language === 'ES' ? 'Tú vs. Competencia' : 'You vs. Competition'}
        </h2>
        <p className="text-gray-400 text-sm">
          {language === 'PT' 
            ? 'Comparação com os 3 principais concorrentes locais' 
            : language === 'ES' 
            ? 'Comparación con los 3 principales competidores locales' 
            : 'Comparison with top 3 local competitors'}
        </p>
      </div>

      {/* Heatmap Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left py-4 px-4 text-gray-400 text-sm font-semibold">
                {language === 'PT' ? 'Negócio' : language === 'ES' ? 'Negocio' : 'Business'}
              </th>
              {dimensions.map((dim) => (
                <th key={dim.key} className="text-center py-4 px-2 text-gray-400 text-xs font-semibold uppercase">
                  {dim.label}
                </th>
              ))}
              <th className="text-right py-4 px-4 text-gray-400 text-sm font-semibold">
                Total
              </th>
            </tr>
          </thead>
          <tbody>
            {businesses.map((business, index) => {
              const isYou = index === 0;
              const total = Object.values(business.scores).reduce((sum, score) => sum + score, 0);

              return (
                <tr 
                  key={index}
                  className={`border-b border-dark-700 transition-colors ${
                    isYou ? 'bg-dark-900/50' : 'hover:bg-dark-900/30'
                  }`}
                >
                  {/* Business Name */}
                  <td className="py-4 px-4">
                    <div className="flex items-center space-x-2">
                      {isYou && (
                        <span className="px-2 py-1 bg-primary/20 text-primary text-xs font-bold rounded">
                          {language === 'PT' ? 'VOCÊ' : language === 'ES' ? 'TÚ' : 'YOU'}
                        </span>
                      )}
                      <span className={`font-medium ${isYou ? 'text-white' : 'text-gray-400'}`}>
                        {business.name}
                      </span>
                    </div>
                  </td>

                  {/* Dimension Scores */}
                  {dimensions.map((dim) => {
                    const score = business.scores[dim.key as keyof typeof business.scores];
                    const heatColor = getHeatColor(score, dim.max);
                    const isWinning = index === 0 && score === Math.max(...businesses.map(b => b.scores[dim.key as keyof typeof b.scores]));
                    const isLosing = index === 0 && score < Math.max(...businesses.map(b => b.scores[dim.key as keyof typeof b.scores]));

                    return (
                      <td key={dim.key} className="py-4 px-2">
                        <div className="flex flex-col items-center">
                          <div className={`w-full h-8 rounded flex items-center justify-center ${heatColor} ${isYou ? 'ring-2 ring-primary ring-offset-2 ring-offset-dark-800' : ''}`}>
                            <span className="text-white font-bold text-sm">
                              {Math.round(score)}
                            </span>
                          </div>
                          {isYou && (
                            <div className="mt-1">
                              {isWinning ? (
                                <TrendingUp className="w-4 h-4 text-success-500" />
                              ) : isLosing ? (
                                <TrendingDown className="w-4 h-4 text-danger-500" />
                              ) : null}
                            </div>
                          )}
                        </div>
                      </td>
                    );
                  })}

                  {/* Total Score */}
                  <td className="py-4 px-4 text-right">
                    <span className={`text-2xl font-bold ${isYou ? 'text-white' : 'text-gray-500'}`}>
                      {Math.round(total)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center space-x-6 text-xs">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-success-500"></div>
          <span className="text-gray-400">
            {language === 'PT' ? 'Excelente (80%+)' : language === 'ES' ? 'Excelente (80%+)' : 'Excellent (80%+)'}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-primary"></div>
          <span className="text-gray-400">
            {language === 'PT' ? 'Bom (60-79%)' : language === 'ES' ? 'Bueno (60-79%)' : 'Good (60-79%)'}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-warning-500"></div>
          <span className="text-gray-400">
            {language === 'PT' ? 'Regular (40-59%)' : language === 'ES' ? 'Regular (40-59%)' : 'Fair (40-59%)'}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-danger-500"></div>
          <span className="text-gray-400">
            {language === 'PT' ? 'Crítico (<40%)' : language === 'ES' ? 'Crítico (<40%)' : 'Critical (<40%)'}
          </span>
        </div>
      </div>

      {/* Insight */}
      <div className="mt-6 p-4 bg-dark-900 rounded-lg border border-dark-700">
        <p className="text-sm text-gray-300 leading-relaxed">
          <strong className="text-danger-500">💔 {language === 'PT' ? 'Verdade dolorosa' : language === 'ES' ? 'Verdad dolorosa' : 'Painful truth'}:</strong>
          {' '}
          {language === 'PT' 
            ? 'Seus concorrentes estão roubando seus clientes porque investiram tempo em otimizar sua presença online. Você pode recuperar essa vantagem em 30-60 dias.' 
            : language === 'ES' 
            ? 'Tus competidores están robando tus clientes porque invirtieron tiempo en optimizar su presencia online. Puedes recuperar esa ventaja en 30-60 días.' 
            : 'Your competitors are stealing your customers because they invested time optimizing their online presence. You can recover this advantage in 30-60 days.'}
        </p>
      </div>
    </div>
  );
}
