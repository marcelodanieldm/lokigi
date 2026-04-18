/**
 * SubscriptionSettings Component
 * 
 * Shows subscription status and cancellation button in the Starter panel.
 * Integrates with the CancellationModal for full flow.
 */

'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertTriangle, Calendar, DollarSign, CheckCircle, AlertCircle } from 'lucide-react'
import { CancellationModal } from './CancellationModal'
import { useCancellation } from '@/hooks/useCancellation'

/**
 * SubscriptionSettings
 * 
 * Embedded in the Starter dashboard at:
 * /dashboard/settings/subscription
 * 
 * Shows:
 * - Current plan (Starter $29/month)
 * - Next billing date
 * - Active features
 * - Cancellation button
 */
export function SubscriptionSettings() {
  const [planPausaActive, setPlanPausaActive] = useState(false)
  const cancellation = useCancellation()

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Cancellation Modal */}
      <CancellationModal
        isOpen={cancellation.isOpen}
        onOpenChange={(open) => {
          if (open) {
            cancellation.openCancellationModal()
          } else {
            cancellation.closeCancellationModal()
          }
        }}
        onCancellationComplete={() => {
          cancellation.handleCancellationComplete()
          // Refresh subscription status
          window.location.reload()
        }}
      />

      {/* Success Message */}
      {cancellation.isCancelled && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Tu suscripción ha sido cancelada exitosamente. Tendrás acceso hasta el final de tu ciclo de facturación.
          </AlertDescription>
        </Alert>
      )}

      {/* Current Plan Card */}
      <Card>
        <CardHeader>
          <CardTitle>Tu Suscripción Actual</CardTitle>
          <CardDescription>
            {planPausaActive
              ? 'Plan Pausa activo - Acceso de lectura únicamente'
              : 'Plan Starter - Automatización completa de reseñas'}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Plan Details */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Plan Actual</p>
              <p className="text-2xl font-bold text-gray-900">
                {planPausaActive ? '$5' : '$29'}
                <span className="text-sm text-gray-600 font-normal">/mes</span>
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Próxima Renovación
              </p>
              <p className="text-lg font-bold text-gray-900">30 de Junio, 2024</p>
            </div>
          </div>

          {/* Plan Features */}
          <div className="space-y-3">
            <h3 className="font-semibold text-gray-900">Características Incluidas</h3>
            <div className="space-y-2">
              <FeatureItem
                included={!planPausaActive}
                label="Respuestas IA automáticas"
              />
              <FeatureItem
                included={!planPausaActive}
                label="Análisis de sentimiento en reseñas"
              />
              <FeatureItem
                included={!planPausaActive}
                label="Alertas de competidores"
              />
              <FeatureItem
                included={!planPausaActive}
                label="Reports de impacto"
              />
              <FeatureItem
                included={true}
                label="Acceso de lectura a datos"
              />
            </div>
          </div>

          {/* Plan Pausa Active Warning */}
          {planPausaActive && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Tu Plan Pausa vence el 30 de Septiembre. Puedes actualizarte de vuelta al Plan Starter en cualquier momento.
              </AlertDescription>
            </Alert>
          )}

          {/* Billing History Link */}
          <div className="pt-4 border-t">
            <a
              href="/dashboard/settings/billing-history"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Ver historial de facturación →
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-600 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Zona de Cancelación
          </CardTitle>
          <CardDescription>
            Acciones que no se pueden deshacer fácilmente
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Cancelar Suscripción</h3>
            <p className="text-sm text-gray-600 mb-4">
              Antes de irte, queremos entender qué podríamos haber hecho mejor. Se mostrará un impacto modal con las horas que has ahorrado.
            </p>
            <div className="flex gap-3">
              <Button
                variant="destructive"
                onClick={cancellation.openCancellationModal}
                className="bg-red-600 hover:bg-red-700"
              >
                Cancelar Suscripción
              </Button>
              <Button
                variant="outline"
                onClick={() => window.open('https://calendar.google.com/calendar/u/0/r/eventedit', '_blank')}
              >
                Agendar Llamada con Soporte
              </Button>
            </div>
          </div>

          {/* Downsell to Plan Pausa Option */}
          {!planPausaActive && (
            <div className="border-t pt-4">
              <h3 className="font-semibold text-gray-900 mb-2">Plan Pausa ($5/mes)</h3>
              <p className="text-sm text-gray-600 mb-4">
                En lugar de cancelar completamente, considera pausar tu suscripción. Mantén tu cuenta, datos y permisos de Google API activos por solo $5/mes.
              </p>
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    const response = await fetch('/api/cancellation/plan-pausa', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      credentials: 'include',
                      body: JSON.stringify({ duration_days: 90 }),
                    })
                    if (response.ok) {
                      setPlanPausaActive(true)
                      // Refresh
                      window.location.reload()
                    }
                  } catch (err) {
                    console.error('Error activating Plan Pausa:', err)
                  }
                }}
                className="border-amber-300 text-amber-700 hover:bg-amber-50"
              >
                Activar Plan Pausa
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* FAQ */}
      <Card>
        <CardHeader>
          <CardTitle>Preguntas Frecuentes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <FAQItem
            question="¿Qué sucede con mis datos cuando cancelo?"
            answer="Mantenemos tus datos durante 90 días. Los permisos de Google API permanecen activos hasta el final de tu ciclo de facturación. Puedes reactivar tu cuenta en cualquier momento."
          />
          <FAQItem
            question="¿Cuándo se aplica la cancelación?"
            answer="La cancelación se aplica al final de tu ciclo de facturación actual. No hay cancelación inmediata ni cargos por adelantado."
          />
          <FAQItem
            question="¿Puedo reactivar mi cuenta después?"
            answer="Sí, puedes volver a activar tu cuenta en cualquier momento dentro de los 90 días. Tu historial de datos se preservará."
          />
          <FAQItem
            question="¿Cuál es la diferencia entre cancelar y Plan Pausa?"
            answer="Plan Pausa ($5/mes) te permite acceder a tus datos en modo lectura. La cancelación completa desactiva todas las características de automatización pero mantiene permisos de Google API."
          />
        </CardContent>
      </Card>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPER COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

interface FeatureItemProps {
  included: boolean
  label: string
}

function FeatureItem({ included, label }: FeatureItemProps) {
  return (
    <div className={`flex items-center gap-2 text-sm ${included ? 'text-gray-900' : 'text-gray-500 line-through'}`}>
      <div
        className={`w-4 h-4 rounded border flex items-center justify-center ${
          included
            ? 'bg-green-600 border-green-600'
            : 'bg-gray-200 border-gray-300'
        }`}
      >
        {included && <div className="text-white text-xs">✓</div>}
      </div>
      {label}
    </div>
  )
}

interface FAQItemProps {
  question: string
  answer: string
}

function FAQItem({ question, answer }: FAQItemProps) {
  const [isOpen, setIsOpen] = React.useState(false)

  return (
    <div className="border-b border-gray-200 pb-4 last:border-b-0 last:pb-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full text-left font-semibold text-gray-900 hover:text-blue-600 transition-colors"
      >
        {question}
      </button>
      {isOpen && <p className="text-sm text-gray-600 mt-2">{answer}</p>}
    </div>
  )
}
