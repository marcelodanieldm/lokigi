'use client';

import { useState } from 'react';
import { Sparkles, ArrowRight, Zap, CheckCircle2, X } from 'lucide-react';

interface StickyCTAProps {
  score: number;
  onSelectPlan: (plan: 'pdf' | 'full') => void;
}

export default function StickyCTA({ score, onSelectPlan }: StickyCTAProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  const plans = [
    {
      id: 'pdf' as const,
      name: 'Plan de Acción PDF',
      price: 9,
      originalPrice: 49,
      emoji: '📄',
      features: [
        'Plan de acción personalizado paso a paso',
        'Análisis detallado de tus 3 fallos críticos',
        'Checklist accionable (30-60 días)',
        'Priorización de tareas por impacto',
        'Plantillas de respuesta a reseñas'
      ],
      cta: 'Descargar Plan PDF',
      badge: 'POPULAR',
      highlight: true
    },
    {
      id: 'full' as const,
      name: 'Optimización Full',
      price: 99,
      originalPrice: 299,
      emoji: '🚀',
      features: [
        'Todo del Plan PDF +',
        'Reclamar/optimizar tu Google Business',
        'Creación de landing page SEO',
        'Estrategia de reseñas (90 días)',
        'Actualización de fotos profesionales',
        '3 meses de seguimiento y soporte'
      ],
      cta: 'Contratar Optimización',
      badge: 'BEST VALUE',
      highlight: false
    }
  ];

  if (!isVisible) return null;

  return (
    <>
      {/* Mobile Sticky Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-50 md:hidden">
        <div className="bg-gradient-to-r from-red-600 to-orange-600 p-4 shadow-2xl">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between text-white"
          >
            <div className="flex items-center gap-3">
              <Zap className="w-6 h-6" />
              <div className="text-left">
                <div className="font-bold">Arregla tu negocio HOY</div>
                <div className="text-xs text-white/80">Desde $9</div>
              </div>
            </div>
            <ArrowRight className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
          </button>
        </div>

        {/* Expanded Mobile View */}
        {isExpanded && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" onClick={() => setIsExpanded(false)}>
            <div className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl max-h-[80vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
              <button
                onClick={() => setIsExpanded(false)}
                className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full"
              >
                <X className="w-6 h-6" />
              </button>

              <h3 className="text-2xl font-black text-gray-900 mb-6">Elige tu plan</h3>

              <div className="space-y-4">
                {plans.map((plan) => (
                  <PlanCard key={plan.id} plan={plan} onSelect={() => onSelectPlan(plan.id)} />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Desktop Sticky Sidebar */}
      <div className="hidden md:block fixed right-8 top-1/2 -translate-y-1/2 z-50 w-96">
        <div className="bg-white rounded-2xl shadow-2xl border-2 border-gray-200 overflow-hidden">
          {/* Close Button */}
          <button
            onClick={() => setIsVisible(false)}
            className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full transition-colors z-10"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>

          {/* Header */}
          <div className="bg-gradient-to-r from-red-600 to-orange-600 p-6 text-white">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5" />
              <span className="text-sm font-bold uppercase">Oferta Exclusiva</span>
            </div>
            <h3 className="text-2xl font-black">Arregla tu negocio ahora</h3>
            <p className="text-white/90 text-sm mt-2">
              {score < 50 ? 'Tu score es crítico. Actúa YA.' : 'Mejora tu presencia local HOY.'}
            </p>
          </div>

          {/* Plans */}
          <div className="p-6 space-y-4 max-h-[calc(100vh-300px)] overflow-y-auto">
            {plans.map((plan) => (
              <PlanCard key={plan.id} plan={plan} onSelect={() => onSelectPlan(plan.id)} compact />
            ))}
          </div>

          {/* Trust Badge */}
          <div className="px-6 pb-6">
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="flex items-center gap-2 text-green-700 text-sm">
                <CheckCircle2 className="w-5 h-5" />
                <span className="font-semibold">Garantía de resultados o 100% reembolso</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

interface PlanCardProps {
  plan: {
    id: string;
    name: string;
    price: number;
    originalPrice: number;
    emoji: string;
    features: string[];
    cta: string;
    badge: string;
    highlight: boolean;
  };
  onSelect: () => void;
  compact?: boolean;
}

function PlanCard({ plan, onSelect, compact = false }: PlanCardProps) {
  return (
    <div className={`relative border-2 rounded-2xl p-6 ${
      plan.highlight 
        ? 'border-orange-500 bg-gradient-to-br from-orange-50 to-red-50' 
        : 'border-gray-200 bg-white'
    }`}>
      {/* Badge */}
      <div className="absolute -top-3 left-4">
        <span className={`text-xs font-bold px-3 py-1 rounded-full ${
          plan.highlight ? 'bg-orange-500 text-white' : 'bg-blue-500 text-white'
        }`}>
          {plan.badge}
        </span>
      </div>

      {/* Header */}
      <div className="mb-4">
        <div className="text-4xl mb-2">{plan.emoji}</div>
        <h4 className="text-lg font-bold text-gray-900">{plan.name}</h4>
      </div>

      {/* Pricing */}
      <div className="mb-4">
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-black text-gray-900">${plan.price}</span>
          <span className="text-gray-400 line-through">${plan.originalPrice}</span>
        </div>
        <div className="text-sm text-gray-600 mt-1">
          Ahorras ${plan.originalPrice - plan.price} ({Math.round((1 - plan.price / plan.originalPrice) * 100)}% OFF)
        </div>
      </div>

      {/* Features */}
      {!compact && (
        <div className="mb-6 space-y-2">
          {plan.features.map((feature, idx) => (
            <div key={idx} className="flex items-start gap-2 text-sm">
              <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
              <span className="text-gray-700">{feature}</span>
            </div>
          ))}
        </div>
      )}

      {/* CTA */}
      <button
        onClick={onSelect}
        className={`w-full py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${
          plan.highlight
            ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white hover:from-red-600 hover:to-orange-600 shadow-lg hover:shadow-xl'
            : 'bg-gray-900 text-white hover:bg-gray-800 shadow-lg hover:shadow-xl'
        }`}
      >
        {plan.cta}
        <ArrowRight className="w-5 h-5" />
      </button>
    </div>
  );
}
