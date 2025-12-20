'use client';

import { LucideIcon } from 'lucide-react';

interface CriticalPoint {
  id: number;
  title: string;
  description: string;
  impact: string;
  icon: LucideIcon;
  severity: 'critical' | 'high' | 'medium';
}

interface CriticalPointsProps {
  points: CriticalPoint[];
}

export default function CriticalPoints({ points }: CriticalPointsProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500';
      case 'high':
        return 'bg-orange-500';
      case 'medium':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-red-100 rounded-xl">
          <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Puntos Críticos</h2>
          <p className="text-gray-600">Problemas que están costándote dinero AHORA</p>
        </div>
      </div>

      <div className="space-y-4">
        {points.map((point, index) => {
          const Icon = point.icon;
          return (
            <div 
              key={point.id}
              className="relative p-6 border-2 border-red-200 rounded-2xl bg-gradient-to-r from-red-50 to-white card-hover"
            >
              {/* Número */}
              <div className="absolute -top-4 -left-4 w-12 h-12 bg-red-600 text-white rounded-full flex items-center justify-center text-xl font-bold shadow-lg">
                {index + 1}
              </div>

              <div className="flex items-start gap-4 ml-6">
                {/* Icono */}
                <div className={`p-4 ${getSeverityColor(point.severity)} rounded-xl flex-shrink-0`}>
                  <Icon className="w-8 h-8 text-white" />
                </div>

                {/* Contenido */}
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {point.title}
                  </h3>
                  <p className="text-gray-700 mb-3">
                    {point.description}
                  </p>
                  <div className="inline-block px-4 py-2 bg-red-100 text-red-700 rounded-lg font-semibold">
                    💸 {point.impact}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Total perdido */}
      <div className="mt-6 p-6 bg-gradient-to-r from-red-600 to-orange-600 rounded-2xl text-white">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-red-100 text-sm font-semibold mb-1">PÉRDIDA TOTAL ESTIMADA</p>
            <p className="text-4xl font-bold">$5,100<span className="text-2xl">/mes</span></p>
            <p className="text-red-100 mt-2">Eso son <span className="font-bold">$61,200 al año</span> que se van por el desagüe</p>
          </div>
          <div className="text-6xl">📉</div>
        </div>
      </div>
    </div>
  );
}
