'use client';

import { Sparkles, ArrowRight, Shield, Zap, CheckCircle2 } from 'lucide-react';

interface CTACardProps {
  leadId: number;
  onCheckout: () => void;
  isLoading?: boolean;
}

export default function CTACard({ leadId, onCheckout, isLoading = false }: CTACardProps) {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-red-600 via-orange-500 to-yellow-500 p-1">
      {/* Glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-red-500/50 to-yellow-500/50 blur-xl"></div>
      
      <div className="relative bg-white rounded-3xl p-8 md:p-12">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-full text-sm font-bold mb-6">
          <Sparkles className="w-4 h-4" />
          OFERTA EXCLUSIVA - 72 HORAS
        </div>

        {/* Main Content */}
        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div>
            <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-4">
              Arregla estos 3 fallos ahora
            </h2>
            <div className="flex items-baseline gap-3 mb-6">
              <span className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-orange-600">
                $9
              </span>
              <div>
                <div className="text-gray-400 line-through text-xl">$297</div>
                <div className="text-sm text-gray-600 font-semibold">Por tiempo limitado</div>
              </div>
            </div>
            
            <div className="space-y-3 mb-8">
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0" />
                <span className="text-gray-700 font-medium">Reclama tu negocio en Google</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0" />
                <span className="text-gray-700 font-medium">Página web profesional en 24h</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0" />
                <span className="text-gray-700 font-medium">Actualización completa de fotos</span>
              </div>
            </div>

            <button
              onClick={onCheckout}
              disabled={isLoading}
              className="w-full md:w-auto btn-primary flex items-center justify-center gap-3 group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Procesando...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Quiero arreglar mi negocio AHORA
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>

            <div className="mt-4 flex items-center gap-2 text-sm text-gray-600">
              <Shield className="w-5 h-5 text-green-600" />
              <span>Garantía de resultados o <strong>devolvemos tu dinero</strong></span>
            </div>
          </div>

          {/* Stats */}
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-8 space-y-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">
              Lo que lograrás en 7 días:
            </h3>
            
            <div className="space-y-4">
              <div className="bg-white rounded-xl p-4 shadow-sm">
                <div className="text-3xl font-black text-green-600 mb-1">+250%</div>
                <div className="text-sm text-gray-600">Aumento en búsquedas</div>
              </div>

              <div className="bg-white rounded-xl p-4 shadow-sm">
                <div className="text-3xl font-black text-blue-600 mb-1">+180%</div>
                <div className="text-sm text-gray-600">Más llamadas</div>
              </div>

              <div className="bg-white rounded-xl p-4 shadow-sm">
                <div className="text-3xl font-black text-purple-600 mb-1">+95%</div>
                <div className="text-sm text-gray-600">Visitas a tu web</div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-yellow-100 rounded-xl border-2 border-yellow-300">
              <p className="text-sm text-gray-800 text-center font-semibold">
                🔥 <strong>Solo quedan 3 spots</strong> disponibles a este precio
              </p>
            </div>
          </div>
        </div>

        {/* Social Proof */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex items-center justify-center gap-8 flex-wrap">
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900">847</div>
              <div className="text-sm text-gray-600">Negocios optimizados</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900">4.9/5.0</div>
              <div className="text-sm text-gray-600">Rating promedio</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-900">$2.4M</div>
              <div className="text-sm text-gray-600">Generados para clientes</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
