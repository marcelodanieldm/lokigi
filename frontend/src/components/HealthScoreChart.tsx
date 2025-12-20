'use client';

import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface HealthScoreChartProps {
  score: number;
}

export default function HealthScoreChart({ score }: HealthScoreChartProps) {
  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score },
  ];

  // Colores basados en el score
  const getScoreColor = (score: number) => {
    if (score < 40) return '#ef4444'; // Rojo
    if (score < 70) return '#f59e0b'; // Naranja
    return '#22c55e'; // Verde
  };

  const scoreColor = getScoreColor(score);
  const COLORS = [scoreColor, '#e5e7eb'];

  const getScoreLabel = (score: number) => {
    if (score < 40) return 'Crítico';
    if (score < 70) return 'Mejorable';
    return 'Excelente';
  };

  return (
    <div className="card card-hover">
      <h3 className="text-2xl font-bold text-gray-900 mb-6">Score de Salud Local</h3>
      
      <div className="relative">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              startAngle={90}
              endAngle={-270}
              innerRadius={80}
              outerRadius={120}
              paddingAngle={0}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        
        {/* Score en el centro */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl font-bold" style={{ color: scoreColor }}>
              {score}
            </div>
            <div className="text-gray-500 text-sm font-semibold mt-1">/ 100</div>
          </div>
        </div>
      </div>

      {/* Label del score */}
      <div className="mt-6 text-center">
        <div 
          className="inline-block px-6 py-3 rounded-full text-lg font-bold text-white"
          style={{ backgroundColor: scoreColor }}
        >
          Estado: {getScoreLabel(score)}
        </div>
      </div>

      {/* Descripción */}
      <div className="mt-6 p-4 bg-gray-50 rounded-xl">
        <p className="text-sm text-gray-600 text-center">
          Tu negocio tiene un score <span className="font-bold text-gray-900">{score}/100</span>.
          {score < 40 && ' Necesitas acción inmediata para no perder más clientes.'}
          {score >= 40 && score < 70 && ' Hay oportunidades claras de mejora.'}
          {score >= 70 && ' ¡Vas por buen camino! Sigue optimizando.'}
        </p>
      </div>
    </div>
  );
}
