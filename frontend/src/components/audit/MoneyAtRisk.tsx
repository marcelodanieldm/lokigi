'use client';

import { TrendingDown, Users, Phone, DollarSign, AlertTriangle } from 'lucide-react';

interface MoneyAtRiskProps {
  monthlyLoss: number;
  lostCalls: number;
  lostCustomers: number;
}

export default function MoneyAtRisk({ monthlyLoss, lostCalls, lostCustomers }: MoneyAtRiskProps) {
  const annualLoss = monthlyLoss * 12;

  return (
    <div className="w-full">
      {/* Main Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-red-600 via-red-700 to-orange-600 p-1">
        {/* Animated Background */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(255,255,255,0.1),rgba(255,255,255,0))]" />
        </div>

        <div className="relative bg-gradient-to-br from-red-600 to-orange-600 rounded-3xl p-8 md:p-12">
          {/* Alert Icon */}
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-white/30 rounded-full blur-xl animate-pulse" />
              <div className="relative bg-white rounded-full p-4">
                <AlertTriangle className="w-12 h-12 text-red-600" />
              </div>
            </div>
          </div>

          {/* Main Message */}
          <div className="text-center mb-8">
            <div className="text-white/90 text-sm font-bold uppercase tracking-wider mb-3">
              💰 DINERO EN RIESGO
            </div>
            <h2 className="text-3xl md:text-5xl font-black text-white mb-4">
              Estás perdiendo aproximadamente
            </h2>
            <div className="inline-block bg-white/20 backdrop-blur-sm rounded-2xl px-8 py-4 border-2 border-white/30">
              <div className="text-5xl md:text-7xl font-black text-white mb-2">
                ${monthlyLoss.toLocaleString()}
              </div>
              <div className="text-white/90 text-xl font-bold">por mes</div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {/* Annual Loss */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-white/20 rounded-xl p-3">
                  <DollarSign className="w-6 h-6 text-white" />
                </div>
                <div className="text-white/80 text-sm font-semibold">PÉRDIDA ANUAL</div>
              </div>
              <div className="text-3xl font-black text-white">
                ${annualLoss.toLocaleString()}
              </div>
              <div className="text-white/70 text-sm mt-2">
                Eso son {Math.round(annualLoss / 1000)}k al año
              </div>
            </div>

            {/* Lost Calls */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-white/20 rounded-xl p-3">
                  <Phone className="w-6 h-6 text-white" />
                </div>
                <div className="text-white/80 text-sm font-semibold">LLAMADAS PERDIDAS</div>
              </div>
              <div className="text-3xl font-black text-white">
                ~{lostCalls}
              </div>
              <div className="text-white/70 text-sm mt-2">
                Llamadas/mes que van a otros
              </div>
            </div>

            {/* Lost Customers */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="bg-white/20 rounded-xl p-3">
                  <Users className="w-6 h-6 text-white" />
                </div>
                <div className="text-white/80 text-sm font-semibold">CLIENTES PERDIDOS</div>
              </div>
              <div className="text-3xl font-black text-white">
                ~{lostCustomers}
              </div>
              <div className="text-white/70 text-sm mt-2">
                Clientes/mes a competencia
              </div>
            </div>
          </div>

          {/* Bottom Message */}
          <div className="mt-8 text-center">
            <p className="text-white/90 text-lg md:text-xl leading-relaxed max-w-3xl mx-auto">
              Debido a estos <span className="font-bold underline">fallos críticos</span> en tu presencia local, 
              estás dejando ir oportunidades de negocio <span className="font-black">CADA HORA</span> que pasa.
            </p>
          </div>
        </div>
      </div>

      {/* Supporting Stats */}
      <div className="mt-6 grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-gray-100">
          <div className="flex items-start gap-4">
            <div className="text-4xl">📊</div>
            <div>
              <h3 className="font-bold text-gray-900 mb-2">Impacto Real</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                Cada punto de rating que subes = +25% más conversiones. 
                Cada 50 reseñas adicionales = +40% más tráfico orgánico.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-lg border-2 border-gray-100">
          <div className="flex items-start gap-4">
            <div className="text-4xl">⏰</div>
            <div>
              <h3 className="font-bold text-gray-900 mb-2">El Tiempo Corre</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                El 76% de búsquedas locales resultan en visita en 24h. 
                Si no apareces fuerte, pierdes esas oportunidades para siempre.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
