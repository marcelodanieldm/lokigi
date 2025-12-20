'use client';

import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { TrendingDown, AlertTriangle, ChevronDown } from 'lucide-react';

interface ScoreGaugeProps {
  score: number;
  businessName: string;
}

export default function ScoreGauge({ score, businessName }: ScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      const interval = setInterval(() => {
        setAnimatedScore(prev => {
          if (prev >= score) {
            clearInterval(interval);
            return score;
          }
          return prev + 1;
        });
      }, 15);
      return () => clearInterval(interval);
    }, 300);
    return () => clearTimeout(timer);
  }, [score]);

  const getScoreColor = (score: number) => {
    if (score < 50) return { primary: '#ef4444', secondary: '#fecaca', label: 'CRÍTICO', emoji: '🔴' };
    if (score < 80) return { primary: '#f59e0b', secondary: '#fed7aa', label: 'MEJORABLE', emoji: '🟡' };
    return { primary: '#22c55e', secondary: '#bbf7d0', label: 'EXCELENTE', emoji: '🟢' };
  };

  const scoreData = getScoreColor(score);
  const data = [
    { name: 'Score', value: animatedScore },
    { name: 'Remaining', value: 100 - animatedScore },
  ];

  return (
    <div className="relative w-full bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(120,119,198,0.3),rgba(255,255,255,0))]" />
      </div>

      <div className="relative px-8 py-12">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full mb-4">
            <span className="text-2xl">{scoreData.emoji}</span>
            <span className="text-white font-bold text-sm">AUDITORÍA COMPLETADA</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-white mb-2">{businessName}</h1>
          <p className="text-slate-300 text-lg">Score de Salud Local</p>
        </div>

        {/* Gauge Chart */}
        <div className="relative max-w-md mx-auto">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                startAngle={180}
                endAngle={0}
                innerRadius={90}
                outerRadius={130}
                paddingAngle={0}
                dataKey="value"
              >
                <Cell fill={scoreData.primary} />
                <Cell fill="rgba(255,255,255,0.1)" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>

          {/* Score Display */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center mt-8">
              <div className="relative">
                <div className="text-7xl md:text-8xl font-black text-white mb-2">
                  {animatedScore}
                </div>
                <div className="absolute -right-8 top-0 text-3xl text-slate-400">/100</div>
              </div>
              <div 
                className="inline-block px-6 py-2 rounded-full text-sm font-bold text-white mt-2"
                style={{ backgroundColor: scoreData.primary }}
              >
                {scoreData.label}
              </div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-4 mt-12 max-w-2xl mx-auto">
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-white/10">
            <div className="text-slate-400 text-xs font-semibold mb-1">VISIBILIDAD</div>
            <div className="text-white text-2xl font-bold">{score < 50 ? 'Baja' : score < 80 ? 'Media' : 'Alta'}</div>
          </div>
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-white/10">
            <div className="text-slate-400 text-xs font-semibold mb-1">PRIORIDAD</div>
            <div className="text-white text-2xl font-bold">{score < 50 ? 'Alta' : score < 80 ? 'Media' : 'Baja'}</div>
          </div>
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-4 border border-white/10">
            <div className="text-slate-400 text-xs font-semibold mb-1">ACCIÓN</div>
            <div className="text-white text-2xl font-bold">{score < 50 ? 'YA' : score < 80 ? 'Pronto' : 'Mantén'}</div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="flex justify-center mt-8">
          <div className="flex flex-col items-center text-slate-400 animate-bounce">
            <span className="text-sm mb-1">Ver detalles</span>
            <ChevronDown className="w-5 h-5" />
          </div>
        </div>
      </div>
    </div>
  );
}
