/**
 * CancellationModal
 * 
 * Main cancellation flow modal that guides users through:
 * 1. Impact Modal (hours saved)
 * 2. Churn Reason Selection
 * 3. Downsell Offers (Plan Pausa if price-related)
 * 4. Final Confirmation
 */

import React, { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { AlertCircle, TrendingUp, Zap, Clock, DollarSign, X } from 'lucide-react'
import { cn } from '@/lib/utils'

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────

interface ImpactData {
  user_id: string
  hours_saved_this_month: number
  responses_approved_this_month: number
  impact_message: string
  total_reviews_processed: number
  total_approved_responses: number
  approval_rate: number
  days_subscribed: number
  current_plan: string
  is_high_value: boolean
  plan_price_monthly: number
}

interface DownsellOffer {
  type: string
  name: string
  description: string
  price: number
  duration_days: number
  features: string[]
  benefit_message: string
}

interface CancellationInitiateResponse {
  status: string
  impact_data: ImpactData
  churn_reason: string
  alternative_offers: DownsellOffer[]
  billing_cycle_end: string
}

interface CancellationConfirmResponse {
  status: string
  message: string
  user_id: string
  cancellation_date: string
  last_charge_date: string
  google_api_permissions_active_until: string
  access_level_after_cancellation: string
  cutoff_date: string
  metrics_pdf_url: string
  goodbye_email_sent: boolean
  alerts_triggered: number
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

interface CancellationModalProps {
  isOpen: boolean
  onOpenChange: (open: boolean) => void
  onCancellationComplete?: () => void
}

export function CancellationModal({
  isOpen,
  onOpenChange,
  onCancellationComplete,
}: CancellationModalProps) {
  const [step, setStep] = useState<'impact' | 'reason' | 'offer' | 'confirmation' | 'success'>('impact')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [impactData, setImpactData] = useState<ImpactData | null>(null)
  const [offers, setOffers] = useState<DownsellOffer[]>([])
  const [selectedReason, setSelectedReason] = useState<string | null>(null)
  const [selectedOffer, setSelectedOffer] = useState<string | null>(null)
  const [feedback, setFeedback] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [finalResult, setFinalResult] = useState<CancellationConfirmResponse | null>(null)

  // Fetch impact data on modal open
  useEffect(() => {
    if (!isOpen) return

    const fetchImpactData = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await fetch('/api/cancellation/impact-data', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        })

        if (!response.ok) {
          throw new Error('Failed to fetch impact data')
        }

        const data: ImpactData = await response.json()
        setImpactData(data)
        setStep('impact')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchImpactData()
  }, [isOpen])

  // Handle reason selection
  const handleReasonSelect = async (reason: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`/api/cancellation/initiate?churn_reason=${reason}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Failed to initiate cancellation')
      }

      const data: CancellationInitiateResponse = await response.json()
      setOffers(data.alternative_offers)
      setSelectedReason(reason)

      // If there are offers (especially Plan Pausa for price reason), show them
      if (data.alternative_offers.length > 0) {
        setStep('offer')
      } else {
        setStep('confirmation')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  // Handle Plan Pausa selection
  const handlePlanPausaSelect = async () => {
    try {
      setConfirming(true)
      setError(null)

      const response = await fetch('/api/cancellation/plan-pausa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ duration_days: 90 }),
      })

      if (!response.ok) {
        throw new Error('Failed to activate Plan Pausa')
      }

      // Success! Close modal and show confirmation
      onOpenChange(false)
      onCancellationComplete?.()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setConfirming(false)
    }
  }

  // Handle final cancellation confirmation
  const handleConfirmCancellation = async () => {
    if (!selectedReason) {
      setError('Please select a cancellation reason')
      return
    }

    try {
      setConfirming(true)
      setError(null)

      const response = await fetch('/api/cancellation/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          churn_reason: selectedReason,
          churn_detail: feedback,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to confirm cancellation')
      }

      // Success!
      const data: CancellationConfirmResponse = await response.json()
      setFinalResult(data)
      setStep('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setConfirming(false)
    }
  }

  // Render content based on current step
  const renderContent = () => {
    if (loading && step === 'impact') {
      return (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          <p className="mt-4 text-gray-600">Cargando datos...</p>
        </div>
      )
    }

    if (step === 'impact' && impactData) {
      return <ImpactStep data={impactData} onNext={() => setStep('reason')} />
    }

    if (step === 'reason') {
      return (
        <ChurnReasonStep
          onSelect={handleReasonSelect}
          loading={loading}
          selectedReason={selectedReason}
        />
      )
    }

    if (step === 'offer' && offers.length > 0) {
      return (
        <DownsellOfferStep
          offers={offers}
          selectedReason={selectedReason}
          onSelectOffer={setSelectedOffer}
          onPlanPausaSelect={handlePlanPausaSelect}
          onSkipOffer={() => setStep('confirmation')}
          confirming={confirming}
        />
      )
    }

    if (step === 'confirmation') {
      return (
        <ConfirmationStep
          selectedReason={selectedReason}
          feedback={feedback}
          onFeedbackChange={setFeedback}
          onConfirm={handleConfirmCancellation}
          onCancel={() => onOpenChange(false)}
          confirming={confirming}
        />
      )
    }

    if (step === 'success' && finalResult) {
      return (
        <SuccessStep
          data={finalResult}
          onClose={() => {
            onOpenChange(false)
            onCancellationComplete?.()
          }}
        />
      )
    }

    return null
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            Cancelar Suscripción
          </DialogTitle>
          <DialogDescription>
            {step === 'impact' && 'Antes de irte, mira el impacto que has logrado'}
            {step === 'reason' && 'Cuéntanos por qué te vas (nos ayuda a mejorar)'}
            {step === 'offer' && 'Antes de partir, una opción más asequible'}
            {step === 'confirmation' && 'Confirmar cancelación de suscripción'}
            {step === 'success' && 'Cancelación confirmada con exportación de métricas'}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        <div className="min-h-[400px]">{renderContent()}</div>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// STEP COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

/**
 * STEP 1: Impact Modal
 * Shows hours saved and encourages user to reconsider
 */
interface ImpactStepProps {
  data: ImpactData
  onNext: () => void
}

function ImpactStep({ data, onNext }: ImpactStepProps) {
  return (
    <div className="space-y-6">
      {/* Big Impact Statement */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-6">
        <div className="flex items-start gap-4">
          <TrendingUp className="w-8 h-8 text-blue-600 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-xl font-bold text-gray-900">
              🎯 Has ahorrado <span className="text-blue-600">{data.hours_saved_this_month} horas</span> este mes
            </h3>
            <p className="text-gray-600 mt-1">
              Con {data.responses_approved_this_month} respuestas automáticas procesadas
            </p>
          </div>
        </div>
      </div>

      {/* Impact Breakdown */}
      <div className="grid grid-cols-2 gap-4">
        <MetricCard
          icon={<Clock className="w-5 h-5" />}
          label="Total Procesadas"
          value={data.total_reviews_processed}
        />
        <MetricCard
          icon={<Zap className="w-5 h-5" />}
          label="Aprobadas por IA"
          value={data.total_approved_responses}
        />
        <MetricCard
          icon={<TrendingUp className="w-5 h-5" />}
          label="Tasa Aprobación"
          value={`${Math.round(data.approval_rate)}%`}
        />
        <MetricCard
          icon={<DollarSign className="w-5 h-5" />}
          label="Inversión Mensual"
          value={`$${data.plan_price_monthly}`}
        />
      </div>

      {/* Testimonial-style message */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <p className="text-sm text-amber-900">
          ¿Sabías? Con un 25% más de aprovechar la plataforma, podrías ahorrar hasta{' '}
          <strong>4+ horas por semana</strong>. Nuestro equipo está disponible para ayudarte a optimizar tu setup.
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4">
        <Button
          variant="outline"
          onClick={() => {}}
          className="flex-1"
        >
          Habla con Soporte
        </Button>
        <Button
          onClick={onNext}
          className="flex-1 bg-red-600 hover:bg-red-700"
        >
          Continuar con Cancelación
        </Button>
      </div>
    </div>
  )
}

/**
 * STEP 2: Churn Reason Selection
 * Why are they leaving?
 */
interface ChurnReasonStepProps {
  onSelect: (reason: string) => void
  loading: boolean
  selectedReason: string | null
}

function ChurnReasonStep({ onSelect, loading, selectedReason }: ChurnReasonStepProps) {
  const reasons = [
    {
      id: 'price_too_high',
      label: 'A. Es muy caro para mi volumen actual.',
      description: 'Precio del plan por encima de mi uso actual.',
    },
    {
      id: 'ease_of_use_difficulty',
      label: 'B. No entiendo cómo usar algunas funciones.',
      description: 'Me faltó claridad o acompañamiento en la experiencia.',
    },
    {
      id: 'business_temporarily_closed',
      label: 'C. Mi negocio cerró temporalmente.',
      description: 'Necesito pausar mientras vuelvo a operar.',
    },
    {
      id: 'switched_competitor',
      label: 'D. Voy a probar otra herramienta.',
      description: 'Compararé otra solución para este problema.',
    },
  ]

  return (
    <div className="space-y-3">
      {reasons.map((reason) => (
        <button
          key={reason.id}
          onClick={() => onSelect(reason.id)}
          disabled={loading}
          className={cn(
            'w-full text-left p-4 border-2 rounded-lg transition-all',
            selectedReason === reason.id
              ? 'border-blue-600 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300 bg-white'
          )}
        >
          <div className="font-semibold text-gray-900">{reason.label}</div>
          <div className="text-sm text-gray-600 mt-1">{reason.description}</div>
        </button>
      ))}
    </div>
  )
}

/**
 * STEP 3: Downsell Offers
 * Try to retain with cheaper option
 */
interface DownsellOfferStepProps {
  offers: DownsellOffer[]
  selectedReason: string | null
  onSelectOffer: (type: string) => void
  onPlanPausaSelect: () => void
  onSkipOffer: () => void
  confirming: boolean
}

function DownsellOfferStep({
  offers,
  selectedReason,
  onSelectOffer,
  onPlanPausaSelect,
  onSkipOffer,
  confirming,
}: DownsellOfferStepProps) {
  const planPausaOffer = offers.find((o) => o.type === 'plan_pausa')

  return (
    <div className="space-y-4">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h3 className="font-semibold text-green-900">
          💡 Tenemos una mejor opción para ti
        </h3>
        <p className="text-sm text-green-800 mt-2">
          Basado en tu razón de cancelación, aquí hay algo que podría funcionar mejor:
        </p>
      </div>

      {/* Plan Pausa Offer (primary if price-related) */}
      {planPausaOffer && selectedReason === 'price_too_high' && (
        <div className="border-2 border-green-500 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h4 className="text-lg font-bold text-gray-900">{planPausaOffer.name}</h4>
              <p className="text-sm text-gray-600 mt-1">{planPausaOffer.description}</p>
            </div>
            <div className="text-3xl font-bold text-green-600">${planPausaOffer.price}/mes</div>
          </div>

          <div className="bg-white bg-opacity-50 rounded p-3 mb-4 space-y-2">
            {planPausaOffer.features.map((feature, idx) => (
              <div key={idx} className="text-sm text-gray-700">
                {feature}
              </div>
            ))}
          </div>

          <p className="text-sm font-semibold text-green-700 mb-4">
            {planPausaOffer.benefit_message}
          </p>

          <Button
            onClick={onPlanPausaSelect}
            disabled={confirming}
            className="w-full bg-green-600 hover:bg-green-700"
          >
            {confirming ? 'Activando...' : 'Activar Plan Pausa'}
          </Button>
        </div>
      )}

      {/* Other offers */}
      <div className="space-y-3">
        {offers
          .filter((o) => o.type !== 'plan_pausa')
          .map((offer, idx) => (
            <div
              key={idx}
              className="border border-gray-200 rounded-lg p-4 hover:border-gray-300"
            >
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-semibold text-gray-900">{offer.name}</h4>
                  <p className="text-sm text-gray-600 mt-1">{offer.description}</p>
                </div>
                {offer.price > 0 && <div className="text-lg font-bold text-gray-900">${offer.price}</div>}
              </div>
            </div>
          ))}
      </div>

      {/* Skip button */}
      <Button
        variant="outline"
        onClick={onSkipOffer}
        className="w-full"
      >
        Ninguna de estas opciones, continuar con cancelación
      </Button>
    </div>
  )
}

/**
 * STEP 4: Final Confirmation
 * Confirm cancellation with optional feedback
 */
interface ConfirmationStepProps {
  selectedReason: string | null
  feedback: string
  onFeedbackChange: (value: string) => void
  onConfirm: () => void
  onCancel: () => void
  confirming: boolean
}

function ConfirmationStep({
  selectedReason,
  feedback,
  onFeedbackChange,
  onConfirm,
  onCancel,
  confirming,
}: ConfirmationStepProps) {
  return (
    <div className="space-y-4">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <p className="text-sm text-yellow-900">
          <strong>⚠️ Importante:</strong> Tu suscripción se cancelará al final del ciclo de facturación actual.
          Los permisos de Google API permanecerán activos para asegurar continuidad.
        </p>
      </div>

      {/* Feedback textarea */}
      <div>
        <label className="block text-sm font-semibold text-gray-900 mb-2">
          Comentarios adicionales (opcional)
        </label>
        <textarea
          value={feedback}
          onChange={(e) => onFeedbackChange(e.target.value)}
          placeholder="Cuéntanos qué podríamos haber hecho mejor..."
          className="w-full border border-gray-300 rounded-lg p-3 text-sm resize-none h-24"
        />
      </div>

      {/* Action buttons */}
      <div className="flex gap-3 pt-4">
        <Button
          variant="outline"
          onClick={onCancel}
          className="flex-1"
          disabled={confirming}
        >
          Volver Atrás
        </Button>
        <Button
          onClick={onConfirm}
          className="flex-1 bg-red-600 hover:bg-red-700"
          disabled={confirming}
        >
          {confirming ? 'Cancelando...' : 'Confirmar Cancelación'}
        </Button>
      </div>
    </div>
  )
}

interface SuccessStepProps {
  data: CancellationConfirmResponse
  onClose: () => void
}

function SuccessStep({ data, onClose }: SuccessStepProps) {
  return (
    <div className="space-y-4">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <p className="text-sm text-green-900">
          <strong>Cancelación confirmada.</strong> Tu plan seguirá activo hasta el{' '}
          <strong>{data.cutoff_date}</strong>.
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
        <p className="text-sm text-blue-900">
          Hemos generado un PDF con tu historial de métricas para que te lo lleves contigo.
        </p>
        <a
          href={data.metrics_pdf_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center text-sm font-semibold text-blue-700 hover:text-blue-800"
        >
          Ver / Guardar historial en PDF
        </a>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-sm text-gray-700">
          {data.goodbye_email_sent
            ? 'Te enviamos un email de despedida con la confirmación legal de la cancelación.'
            : 'La confirmación legal de cancelación quedará disponible por email cuando esté habilitado el envío.'}
        </p>
      </div>

      <Button onClick={onClose} className="w-full bg-gray-900 hover:bg-gray-800">
        Volver al panel
      </Button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPER COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

interface MetricCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
}

function MetricCard({ icon, label, value }: MetricCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center gap-2 text-gray-600 mb-2">
        <span className="text-blue-600">{icon}</span>
        <span className="text-xs font-semibold">{label}</span>
      </div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
    </div>
  )
}
