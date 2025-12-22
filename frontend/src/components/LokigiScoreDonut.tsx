'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';
import { useLanguageDetection } from '@/hooks/useLanguageDetection';
import { getTranslation } from '@/lib/translations';

interface LokigiScoreDonutProps {
  score: number;
  dimensions: Array<{
    nombre: string;
    puntos: number;
    maximo: number;
    porcentaje: number;
  }>;
}

export default function LokigiScoreDonut({ score, dimensions }: LokigiScoreDonutProps) {
  const { language } = useLanguageDetection();

  // Colores para las dimensiones (coordinar con el donut)
  const dimensionColors: Record<string, string> = {
    'Propiedad': '#ff1744', // Rojo (crítico)
    'Reputación': '#ffaa00', // Naranja
    'Contenido Visual': '#00d9ff', // Cyan
    'Presencia Digital': '#00ff41', // Verde neón
  };

  // Datos para el gráfico de dona
  const chartData = dimensions.map((dim) => ({
    name: dim.nombre,
    value: dim.puntos,
    fill: dimensionColors[dim.nombre] || '#666',
  }));

  // Determinar etiqueta del score
  const getScoreLabel = () => {
    if (score >= 85) return { text: 'Excelente', color: 'text-success-500' };
    if (score >= 70) return { text: 'Bueno', color: 'text-primary' };
    if (score >= 50) return { text: 'Regular', color: 'text-warning-500' };
    return { text: 'Crítico', color: 'text-danger-500' };
  };

  const scoreLabel = getScoreLabel();

  return (
    <div className="bg-dark-800 border border-dark-700 rounded-xl p-8">
      {/* Header */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">
          Lokigi <span className="text-primary">Score</span>
        </h2>
        <p className="text-gray-400 text-sm">
          Índice de Visibilidad Local (0-100)
        </p>
      </div>

      {/* Donut Chart */}
      <div className="relative">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={80}
              outerRadius={120}
              paddingAngle={3}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Score en el centro */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className={`text-6xl font-black ${scoreLabel.color}`}>
            {score}
          </div>
          <div className={`text-sm font-semibold uppercase tracking-wide ${scoreLabel.color}`}>
            {scoreLabel.text}
          </div>
        </div>
      </div>

      {/* Dimensions Breakdown */}
      <div className="mt-8 space-y-3">
        {dimensions.map((dim) => {
          const percentage = Math.round((dim.puntos / dim.maximo) * 100);
          const color = dimensionColors[dim.nombre];

          return (
            <div key={dim.nombre} className="space-y-1">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-300 font-medium">{dim.nombre}</span>
                <span className="text-gray-400 font-mono">
                  {dim.puntos}/{dim.maximo}
                </span>
              </div>
              <div className="h-2 bg-dark-700 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all duration-700 ease-out"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Explicación */}
      <div className="mt-6 p-4 bg-dark-900 rounded-lg border border-dark-700">
        <p className="text-xs text-gray-400 leading-relaxed">
          <strong className="text-primary">Cómo se calcula:</strong> El Lokigi Score
          analiza 4 dimensiones críticas de tu presencia en Google Maps.
          Propiedad (40%), Reputación (25%), Contenido Visual (20%) y Presencia Digital (15%).
        </p>
      </div>
    </div>
  );
}
