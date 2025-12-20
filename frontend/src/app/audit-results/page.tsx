'use client';

import { useState } from 'react';
import ScoreGauge from '@/components/audit/ScoreGauge';
import CriticalAlertsGrid from '@/components/audit/CriticalAlertsGrid';
import LocalComparison from '@/components/audit/LocalComparison';
import MoneyAtRisk from '@/components/audit/MoneyAtRisk';
import StickyCTA from '@/components/audit/StickyCTA';

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

  const handlePlanSelect = (plan: 'pdf' | 'full') => {
    setSelectedPlan(plan);
    console.log('Plan seleccionado:', plan);
    // Aquí integrarías con Stripe o tu sistema de pagos
    alert(`Has seleccionado: ${plan === 'pdf' ? 'Plan de Acción PDF ($9)' : 'Optimización Full ($99)'}`);
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

      {/* Local Comparison */}
      <section className="container mx-auto px-4 py-12">
        <LocalComparison 
          userMetrics={mockAuditData.comparison.user}
          avgCompetitor={mockAuditData.comparison.avgCompetitor}
        />
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
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => handlePlanSelect('pdf')}
                className="px-8 py-4 bg-gradient-to-r from-red-500 to-orange-500 text-white font-bold rounded-xl hover:from-red-600 hover:to-orange-600 transition-all transform hover:scale-105 shadow-lg"
              >
                Obtener Plan PDF ($9)
              </button>
              <button
                onClick={() => handlePlanSelect('full')}
                className="px-8 py-4 bg-white text-gray-900 font-bold rounded-xl hover:bg-gray-100 transition-all transform hover:scale-105 shadow-lg"
              >
                Optimización Full ($99)
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Sticky CTA */}
      <StickyCTA score={mockAuditData.business.score} onSelectPlan={handlePlanSelect} />

      {/* Spacer for mobile sticky bar */}
      <div className="h-20 md:hidden" />
    </div>
  );
}
