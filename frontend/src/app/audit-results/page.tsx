'use client';

import { useState, useEffect } from 'react';
import ScoreGauge from '@/components/audit/ScoreGauge';
import CriticalAlertsGrid from '@/components/audit/CriticalAlertsGrid';
import LocalComparison from '@/components/audit/LocalComparison';
import MoneyAtRisk from '@/components/audit/MoneyAtRisk';
import StickyCTA from '@/components/audit/StickyCTA';
import LeadCaptureModal from '@/components/LeadCaptureModal';

// Datos de ejemplo (en producción vendrían del backend)
const mockAuditData = {
  business: {
    name: 'Restaurante Casa Pepe',
    score: 38
  },
  criticalAlerts: [
    {
      id: '1',
      severity: 'critical' as const,
      title: 'Perfil No Reclamado en Google',
      description: 'Tu negocio NO está reclamado. Cualquiera puede editar tu información, horarios y hasta cambiar el número de teléfono.',
      impact: '$2,400/mes en negocio robado'
    },
    {
      id: '2',
      severity: 'critical' as const,
      title: 'Sin Sitio Web Activo',
      description: 'El 87% de clientes potenciales buscan tu sitio web antes de visitar. Sin destino claro, pierdes el 30% de conversiones.',
      impact: '$1,800/mes en ventas perdidas'
    },
    {
      id: '3',
      severity: 'high' as const,
      title: 'Fotos Desactualizadas',
      description: 'Tu última foto tiene 540 días. Negocios con fotos recientes obtienen 42% más clics en búsquedas locales.',
      impact: '$900/mes en visibilidad'
    }
  ],
  comparison: {
    user: {
      businessName: 'Restaurante Casa Pepe',
      reviews: 23,
      rating: 3.5,
      hasPhotos: true,
      hasWebsite: false,
      responseRate: 15
    },
    avgCompetitor: {
      reviews: 187,
      rating: 4.6,
      hasPhotos: true,
      hasWebsite: true,
      responseRate: 85
    }
  },
  moneyAtRisk: {
    monthlyLoss: 5100,
    lostCalls: 48,
    lostCustomers: 32
  }
};

export default function AuditResultsPage() {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [showLeadModal, setShowLeadModal] = useState(false);
  const [leadId, setLeadId] = useState<number | null>(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  // Verificar si ya existe un lead_id en localStorage
  useEffect(() => {
    const storedLeadId = localStorage.getItem('lokigi_lead_id');
    if (storedLeadId) {
      setLeadId(parseInt(storedLeadId));
      setShowRecommendations(true);
    }
  }, []);

  const handleLeadSubmit = async (leadData: any) => {
    try {
      const response = await fetch('http://localhost:8000/api/leads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...leadData,
          fallos_criticos: mockAuditData.criticalAlerts,
          audit_data: mockAuditData
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al guardar los datos');
      }

      const data = await response.json();
      setLeadId(data.id);
      localStorage.setItem('lokigi_lead_id', data.id.toString());
      setShowRecommendations(true);
      setShowLeadModal(false);
    } catch (error: any) {
      throw error;
    }
  };

  const handlePlanSelect = async (plan: 'pdf' | 'full') => {
    // Si no hay lead, mostrar modal primero
    if (!leadId) {
      setShowLeadModal(true);
      setSelectedPlan(plan);
      return;
    }

    setIsProcessingPayment(true);
    
    try {
      // Llamar al endpoint correspondiente
      const endpoint = plan === 'pdf' 
        ? 'http://localhost:8000/api/create-checkout-session/ebook'
        : 'http://localhost:8000/api/create-checkout-session/service';
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ lead_id: leadId }),
      });

      if (!response.ok) {
        throw new Error('Error al crear la sesión de pago');
      }

      const data = await response.json();
      
      // Redirigir a Stripe Checkout
      window.location.href = data.url;
    } catch (error) {
      console.error('Error:', error);
      alert('Error al procesar el pago. Por favor intenta nuevamente.');
    } finally {
      setIsProcessingPayment(false);
    }
  };

  const handleUnlockRecommendations = () => {
    if (leadId) {
      setShowRecommendations(true);
    } else {
      setShowLeadModal(true);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-12">
        <ScoreGauge 
          score={mockAuditData.business.score}
          businessName={mockAuditData.business.name}
        />
      </section>

      {/* Critical Alerts */}
      <section className="container mx-auto px-4 py-12">
        <CriticalAlertsGrid alerts={mockAuditData.criticalAlerts} />
      </section>

      {/* Money at Risk Banner */}
      <section className="container mx-auto px-4 py-12">
        <MoneyAtRisk 
          monthlyLoss={mockAuditData.moneyAtRisk.monthlyLoss}
          lostCalls={mockAuditData.moneyAtRisk.lostCalls}
          lostCustomers={mockAuditData.moneyAtRisk.lostCustomers}
        />
      </section>

      {/* Gated Recommendations Section */}
      <section className="container mx-auto px-4 py-12">
        {!showRecommendations ? (
          <div className="relative">
            {/* Blurred Preview */}
            <div className="blur-md pointer-events-none select-none">
              <LocalComparison 
                userMetrics={mockAuditData.comparison.user}
                avgCompetitor={mockAuditData.comparison.avgCompetitor}
              />
            </div>

            {/* Unlock Overlay */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md text-center border-4 border-orange-500">
                <div className="text-6xl mb-4">🔒</div>
                <h3 className="text-3xl font-black text-gray-900 mb-4">
                  Análisis Competitivo Bloqueado
                </h3>
                <p className="text-gray-600 mb-6 leading-relaxed">
                  Para ver la <span className="font-bold text-red-600">comparativa detallada</span> con 
                  tu competencia y el <span className="font-bold text-red-600">plan de acción completo</span>, 
                  necesitamos tus datos de contacto.
                </p>
                <button
                  onClick={handleUnlockRecommendations}
                  className="w-full bg-gradient-to-r from-red-600 to-orange-600 text-white font-bold py-4 px-8 rounded-xl hover:from-red-700 hover:to-orange-700 transition-all transform hover:scale-105 shadow-lg"
                >
                  🔓 Desbloquear GRATIS
                </button>
                <p className="text-xs text-gray-500 mt-4">
                  Solo toma 30 segundos. No requiere tarjeta de crédito.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <LocalComparison 
            userMetrics={mockAuditData.comparison.user}
            avgCompetitor={mockAuditData.comparison.avgCompetitor}
          />
        )}
      </section>

      {/* Enhanced Pricing Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-black text-gray-900 mb-4">
            Ya viste el problema. Ahora elige la solución 💡
          </h2>
          <p className="text-xl text-gray-600">
            Cada día que pases sin actuar, <span className="font-bold text-red-600">pierdes más dinero</span>
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* E-book Card */}
          <div className="relative bg-white rounded-3xl shadow-xl p-8 border-2 border-gray-200 hover:border-orange-400 transition-all transform hover:scale-105">
            <div className="absolute -top-4 left-8">
              <span className="bg-blue-500 text-white text-sm font-bold px-4 py-2 rounded-full shadow-lg">
                POPULAR
              </span>
            </div>

            <div className="text-5xl mb-4">📄</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Plan de Acción PDF</h3>
            <p className="text-gray-600 mb-6">Hazlo tú mismo, paso a paso</p>

            <div className="mb-6">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-black text-gray-900">$9</span>
                <span className="text-gray-400 line-through text-xl">$49</span>
                <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded-full">
                  82% OFF
                </span>
              </div>
            </div>

            <ul className="space-y-3 mb-8">
              {[
                'Plan personalizado para tu negocio',
                'Análisis de tus 3 fallos críticos',
                'Checklist accionable (30-60 días)',
                'Priorización por impacto económico',
                'Plantillas de respuesta a reseñas'
              ].map((feature, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>

            <button
              onClick={() => handlePlanSelect('pdf')}
              disabled={isProcessingPayment}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold py-4 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50"
            >
              {isProcessingPayment ? 'Procesando...' : 'Comprar por $9'}
            </button>
          </div>

          {/* Service Card - WITH SHINE EFFECT */}
          <div className="relative bg-gradient-to-br from-orange-50 to-red-50 rounded-3xl shadow-2xl p-8 border-4 border-orange-500 transform hover:scale-105 transition-all overflow-hidden">
            {/* Animated Shine Effect */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute -inset-full animate-[shine_3s_ease-in-out_infinite] bg-gradient-to-r from-transparent via-white/30 to-transparent skew-x-12" />
            </div>

            <div className="relative z-10">
              <div className="absolute -top-4 left-8">
                <span className="bg-gradient-to-r from-orange-500 to-red-500 text-white text-sm font-bold px-4 py-2 rounded-full shadow-lg animate-pulse">
                  🔥 MÁS ELEGIDO
                </span>
              </div>

              <div className="text-5xl mb-4">🚀</div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Optimización Full</h3>
              <p className="text-gray-600 mb-6">Lo hacemos TODO por ti</p>

              <div className="mb-6">
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-gray-900">$99</span>
                  <span className="text-gray-400 line-through text-xl">$299</span>
                  <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded-full">
                    67% OFF
                  </span>
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                {[
                  '✨ Todo del Plan PDF +',
                  'Reclamamos/optimizamos tu Google Business',
                  'Creación de landing page SEO optimizada',
                  'Estrategia de reseñas (90 días)',
                  'Actualización con fotos profesionales',
                  '3 meses de seguimiento + soporte'
                ].map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <div className="text-orange-500 mt-1 font-bold">✓</div>
                    <span className="text-gray-900 font-medium">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handlePlanSelect('full')}
                disabled={isProcessingPayment}
                className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white font-black py-5 rounded-xl hover:from-orange-600 hover:to-red-600 transition-all shadow-2xl hover:shadow-3xl text-lg disabled:opacity-50 relative overflow-hidden group"
              >
                <span className="relative z-10">
                  {isProcessingPayment ? 'Procesando...' : '🔥 Contratar por $99'}
                </span>
                {/* Button Shine */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/30 to-transparent" />
              </button>

              <p className="text-center text-sm text-gray-600 mt-4 font-semibold">
                ⚡ Resultados visibles en 7-14 días
              </p>
            </div>
          </div>
        </div>

        {/* Trust Indicators */}
        <div className="mt-12 flex flex-wrap justify-center gap-8 text-center">
          <div>
            <div className="text-3xl font-black text-gray-900">100%</div>
            <div className="text-sm text-gray-600">Garantía de reembolso</div>
          </div>
          <div>
            <div className="text-3xl font-black text-gray-900">24h</div>
            <div className="text-sm text-gray-600">Respuesta promedio</div>
          </div>
          <div>
            <div className="text-3xl font-black text-gray-900">500+</div>
            <div className="text-sm text-gray-600">Negocios mejorados</div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="container mx-auto px-4 py-12">
        <div className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-3xl p-8 md:p-12 text-white text-center">
          <div className="max-w-3xl mx-auto">
            <div className="text-5xl mb-4">🎯</div>
            <h2 className="text-3xl md:text-4xl font-black mb-4">
              ¿Listo para dejar de perder dinero?
            </h2>
            <p className="text-xl text-gray-300 mb-6">
              Cada día que pasa sin actuar, tu competencia captura más clientes que deberían ser tuyos.
              El momento de actuar es <span className="font-bold text-orange-400">AHORA</span>.
            </p>
          </div>
        </div>
      </section>

      {/* Sticky CTA */}
      <StickyCTA score={mockAuditData.business.score} onSelectPlan={handlePlanSelect} />

      {/* Lead Capture Modal */}
      <LeadCaptureModal
        isOpen={showLeadModal}
        onClose={() => setShowLeadModal(false)}
        onSubmit={handleLeadSubmit}
        businessName={mockAuditData.business.name}
        score={mockAuditData.business.score}
      />

      {/* Spacer for mobile sticky bar */}
      <div className="h-20 md:hidden" />

      {/* Tailwind Animation for Shine */}
      <style jsx global>{`
        @keyframes shine {
          0% {
            transform: translateX(-100%) skewX(-12deg);
          }
          100% {
            transform: translateX(200%) skewX(-12deg);
          }
        }
      `}</style>
    </div>
  );
}
