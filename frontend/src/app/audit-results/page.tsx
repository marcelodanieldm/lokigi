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

      {/* Gated Recommendations Section - LEAD WALL */}
      <section className="container mx-auto px-4 py-12">
        {!showRecommendations ? (
          <div className="relative">
            {/* Blurred Preview */}
            <div className="blur-lg pointer-events-none select-none brightness-75">
              <LocalComparison 
                userMetrics={mockAuditData.comparison.user}
                avgCompetitor={mockAuditData.comparison.avgCompetitor}
              />
            </div>

            {/* Unlock Overlay - CENTRADO Y LLAMATIVO */}
            <div className="absolute inset-0 flex items-center justify-center p-4">
              <div className="bg-gradient-to-br from-white via-orange-50 to-red-50 rounded-3xl shadow-[0_20px_80px_rgba(0,0,0,0.3)] p-10 max-w-xl w-full text-center border-4 border-orange-500 transform hover:scale-105 transition-all">
                {/* Icon con animación */}
                <div className="text-8xl mb-6 animate-bounce">🔒</div>
                
                <h3 className="text-4xl font-black text-gray-900 mb-4 leading-tight">
                  Descubre Cómo Arreglar <span className="text-red-600">Estos Fallos</span>
                </h3>
                
                <p className="text-lg text-gray-700 mb-6 leading-relaxed">
                  Deja tu <span className="font-bold text-orange-600">email y WhatsApp</span> para 
                  desbloquear tu <span className="font-bold text-orange-600">plan de acción GRATUITO</span> 
                  y ver exactamente qué hace tu competencia para superarte.
                </p>

                {/* Beneficios */}
                <div className="bg-white rounded-2xl p-6 mb-6 space-y-3 text-left border-2 border-orange-200">
                  {[
                    '✅ Plan de acción personalizado paso a paso',
                    '✅ Comparativa detallada con tu competencia',
                    '✅ Priorización por impacto económico',
                    '✅ Acceso inmediato (sin tarjeta de crédito)'
                  ].map((benefit, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-green-600 text-xs">✓</span>
                      </div>
                      <span className="text-gray-800 font-medium">{benefit}</span>
                    </div>
                  ))}
                </div>

                <button
                  onClick={handleUnlockRecommendations}
                  className="w-full bg-gradient-to-r from-red-600 via-orange-600 to-red-600 text-white font-black text-xl py-5 px-8 rounded-2xl hover:from-red-700 hover:via-orange-700 hover:to-red-700 transition-all transform hover:scale-105 shadow-2xl hover:shadow-3xl relative overflow-hidden group"
                >
                  <span className="relative z-10 flex items-center justify-center gap-2">
                    🔓 DESBLOQUEAR GRATIS AHORA
                  </span>
                  {/* Button shine effect */}
                  <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r from-transparent via-white/30 to-transparent" />
                </button>
                
                <p className="text-sm text-gray-500 mt-4 font-medium">
                  ⏱️ Solo toma 30 segundos · 🔒 Tus datos están seguros
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
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-5xl font-black text-gray-900 mb-4">
            Ya viste el problema. <span className="text-orange-600">Ahora elige la solución 💡</span>
          </h2>
          <p className="text-2xl text-gray-600 font-medium">
            Cada día que pases sin actuar, <span className="font-bold text-red-600">pierdes $170 USD</span>
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto mb-16">
          {/* E-book Card - Self Service */}
          <div className="relative bg-white rounded-3xl shadow-xl p-8 border-2 border-gray-200 hover:border-blue-400 transition-all transform hover:scale-105 hover:shadow-2xl">
            <div className="absolute -top-4 left-8">
              <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm font-bold px-4 py-2 rounded-full shadow-lg">
                HAZLO TÚ MISMO
              </span>
            </div>

            <div className="text-6xl mb-4">📚</div>
            <h3 className="text-3xl font-bold text-gray-900 mb-2">Guía Paso a Paso (E-book)</h3>
            <p className="text-gray-600 mb-6 text-lg">Para dueños de negocio que prefieren implementar ellos mismos</p>

            <div className="mb-6">
              <div className="flex items-baseline gap-3">
                <span className="text-6xl font-black text-blue-600">$9</span>
                <div className="flex flex-col">
                  <span className="text-gray-400 line-through text-2xl">$49</span>
                  <span className="bg-green-100 text-green-700 text-xs font-bold px-3 py-1 rounded-full">
                    82% OFF LANZAMIENTO
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 rounded-2xl p-4 mb-6 border-2 border-blue-200">
              <div className="font-bold text-blue-900 mb-2">✅ Incluye:</div>
              <ul className="space-y-2">
                {[
                  'Plan personalizado para tu negocio',
                  'Análisis de tus 3 fallos críticos',
                  'Checklist accionable (30-60 días)',
                  'Priorización por impacto económico',
                  'Plantillas de respuesta a reseñas',
                  'Guía de optimización de fotos'
                ].map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <div className="text-blue-600 mt-1 font-bold">✓</div>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            <button
              onClick={() => handlePlanSelect('pdf')}
              disabled={isProcessingPayment}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold text-lg py-5 rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl disabled:opacity-50 mb-4"
            >
              {isProcessingPayment ? '⏳ Procesando...' : '📥 Comprar Guía por $9'}
            </button>

            {/* Testimonial */}
            <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
              <div className="flex items-start gap-3 mb-2">
                <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                  JR
                </div>
                <div>
                  <div className="font-semibold text-gray-900">Juan Ramírez</div>
                  <div className="text-sm text-gray-600">Café Don Juan, Lima</div>
                </div>
              </div>
              <p className="text-sm text-gray-700 italic">
                "Seguí la guía al pie de la letra y en 3 semanas mi perfil pasó de la página 2 a estar en el Top 3. 
                Súper claro y fácil de implementar."
              </p>
              <div className="flex gap-1 mt-2">
                {'⭐'.repeat(5)}
              </div>
            </div>
          </div>

          {/* Service Card - VIP RECOMENDADA */}
          <div className="relative bg-gradient-to-br from-orange-50 via-red-50 to-orange-50 rounded-3xl shadow-2xl p-8 border-4 border-orange-500 transform hover:scale-105 transition-all overflow-hidden">
            {/* Animated Shine Effect */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute -inset-full animate-[shine_3s_ease-in-out_infinite] bg-gradient-to-r from-transparent via-white/40 to-transparent skew-x-12" />
            </div>

            <div className="relative z-10">
              <div className="absolute -top-4 left-8">
                <span className="bg-gradient-to-r from-orange-500 to-red-500 text-white text-sm font-bold px-5 py-2 rounded-full shadow-lg animate-pulse">
                  🔥 MÁS POPULAR - RECOMENDADO
                </span>
              </div>

              <div className="text-6xl mb-4">🚀</div>
              <h3 className="text-3xl font-bold text-gray-900 mb-2">Optimización Profesional</h3>
              <p className="text-gray-700 mb-6 text-lg font-medium">Los expertos lo hacen TODO por ti</p>

              <div className="mb-6">
                <div className="flex items-baseline gap-3">
                  <span className="text-6xl font-black text-orange-600">$99</span>
                  <div className="flex flex-col">
                    <span className="text-gray-400 line-through text-2xl">$299</span>
                    <span className="bg-green-100 text-green-800 text-xs font-bold px-3 py-1 rounded-full">
                      67% OFF LANZAMIENTO
                    </span>
                  </div>
                </div>
              </div>

              {/* Badge de Resultados Rápidos */}
              <div className="bg-green-100 border-2 border-green-500 rounded-xl p-4 mb-6 text-center">
                <div className="text-green-800 font-black text-2xl mb-1">⚡ Resultados en 72 Horas</div>
                <div className="text-green-700 text-sm font-semibold">
                  Garantizamos mejoras visibles en menos de 3 días
                </div>
              </div>

              <div className="bg-white rounded-2xl p-5 mb-6 border-2 border-orange-200">
                <div className="font-bold text-orange-900 mb-3 text-lg">✨ Todo del Plan PDF +</div>
                <ul className="space-y-3">
                  {[
                    '🏆 Reclamamos y optimizamos tu Google Business',
                    '🌐 Creación de landing page SEO optimizada',
                    '⭐ Estrategia de reseñas (90 días)',
                    '📸 Actualización con 5 fotos profesionales',
                    '📊 3 meses de seguimiento + informes mensuales',
                    '💬 Soporte prioritario por WhatsApp'
                  ].map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <div className="mt-1">
                        <span className="text-orange-600 font-bold">✓</span>
                      </div>
                      <span className="text-gray-900 font-medium">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={() => handlePlanSelect('full')}
                disabled={isProcessingPayment}
                className="w-full bg-gradient-to-r from-orange-500 via-red-500 to-orange-500 text-white font-black text-xl py-6 rounded-2xl hover:from-orange-600 hover:via-red-600 hover:to-orange-600 transition-all shadow-2xl hover:shadow-3xl disabled:opacity-50 relative overflow-hidden group mb-4"
              >
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {isProcessingPayment ? '⏳ Procesando...' : '🔥 CONTRATAR AHORA POR $99'}
                </span>
                {/* Button Shine */}
                <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/30 to-transparent" />
              </button>

              {/* Testimonial */}
              <div className="bg-white rounded-xl p-4 border-2 border-orange-200">
                <div className="flex items-start gap-3 mb-2">
                  <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold">
                    MC
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">María Castro</div>
                    <div className="text-sm text-gray-600">Ferretería El Tornillo, CDMX</div>
                  </div>
                </div>
                <p className="text-sm text-gray-700 italic">
                  "En 10 días pasamos de 15 a 89 llamadas mensuales. El equipo es profesional y los resultados hablan por sí solos. 
                  Mejor inversión que hemos hecho este año."
                </p>
                <div className="flex gap-1 mt-2">
                  {'⭐'.repeat(5)}
                </div>
              </div>

              <p className="text-center text-sm text-orange-800 mt-4 font-bold bg-orange-100 rounded-full py-2">
                🎯 Solo 5 espacios disponibles esta semana
              </p>
            </div>
          </div>
        </div>

        {/* Social Proof - Otros negocios que subieron su ranking */}
        <div className="max-w-5xl mx-auto mb-12">
          <h3 className="text-3xl font-black text-gray-900 text-center mb-8">
            🏆 Otros negocios que ya mejoraron su ranking
          </h3>
          
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                name: 'Pizzería Napolitana',
                city: 'Bogotá',
                before: 28,
                after: 82,
                revenue: '+$4,200/mes',
                avatar: 'PN'
              },
              {
                name: 'Peluquería Glamour',
                city: 'Buenos Aires',
                before: 35,
                after: 91,
                revenue: '+$3,800/mes',
                avatar: 'PG'
              },
              {
                name: 'Taller Mecánico Pro',
                city: 'Santiago',
                before: 42,
                after: 88,
                revenue: '+$5,600/mes',
                avatar: 'TM'
              }
            ].map((business, idx) => (
              <div key={idx} className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-200 hover:border-green-400 transition-all">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                    {business.avatar}
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">{business.name}</div>
                    <div className="text-sm text-gray-600">{business.city}</div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mb-3">
                  <div className="text-center">
                    <div className="text-3xl font-black text-red-600">{business.before}</div>
                    <div className="text-xs text-gray-600 font-semibold">ANTES</div>
                  </div>
                  <div className="text-3xl text-gray-400">→</div>
                  <div className="text-center">
                    <div className="text-3xl font-black text-green-600">{business.after}</div>
                    <div className="text-xs text-gray-600 font-semibold">DESPUÉS</div>
                  </div>
                </div>

                <div className="bg-green-100 rounded-lg p-3 text-center border border-green-300">
                  <div className="text-green-800 font-bold text-lg">{business.revenue}</div>
                  <div className="text-xs text-green-700">Incremento en ventas</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Trust Indicators */}
        <div className="flex flex-wrap justify-center gap-8 text-center max-w-4xl mx-auto">
          <div className="flex-1 min-w-[150px]">
            <div className="text-4xl font-black text-gray-900">100%</div>
            <div className="text-sm text-gray-600 font-semibold">Garantía de satisfacción</div>
          </div>
          <div className="flex-1 min-w-[150px]">
            <div className="text-4xl font-black text-gray-900">&lt;24h</div>
            <div className="text-sm text-gray-600 font-semibold">Respuesta promedio</div>
          </div>
          <div className="flex-1 min-w-[150px]">
            <div className="text-4xl font-black text-gray-900">500+</div>
            <div className="text-sm text-gray-600 font-semibold">Negocios optimizados</div>
          </div>
          <div className="flex-1 min-w-[150px]">
            <div className="text-4xl font-black text-gray-900">4.9★</div>
            <div className="text-sm text-gray-600 font-semibold">Rating promedio</div>
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
