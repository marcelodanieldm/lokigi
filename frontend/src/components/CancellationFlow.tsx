"use client";

import { useState } from "react";
import { X, AlertTriangle, TrendingDown, Gift, MessageSquare } from "lucide-react";

interface CancellationFlowProps {
  isOpen: boolean;
  onClose: () => void;
  subscriptionId: number;
  leadId: number;
  language: "es" | "pt" | "en";
}

interface CompetitorThreat {
  competitor_name: string;
  threat_type: string;
  threat_level: string;
  details: string;
  metric_change: Record<string, number>;
}

interface MicroAuditData {
  has_threats: boolean;
  threats_detected: CompetitorThreat[];
  business_current_rank: number;
  total_competitors: number;
  days_since_last_scan: number;
  urgency_message: string;
  risk_level: string;
}

interface RetentionOffer {
  offer_type: string;
  original_price: number;
  discount_price: number;
  savings_amount: number;
  coupon_code: string;
  valid_until: string;
}

export default function CancellationFlow({
  isOpen,
  onClose,
  subscriptionId,
  leadId,
  language,
}: CancellationFlowProps) {
  const [step, setStep] = useState(1); // 1 = Micro-Audit, 2 = Retention Offer, 3 = Feedback
  const [loading, setLoading] = useState(false);
  const [microAuditData, setMicroAuditData] = useState<MicroAuditData | null>(null);
  const [retentionOffer, setRetentionOffer] = useState<RetentionOffer | null>(null);
  
  // Feedback form state
  const [reasonCategory, setReasonCategory] = useState("");
  const [reasonDetail, setReasonDetail] = useState("");
  const [satisfactionScore, setSatisfactionScore] = useState(0);

  // Translations
  const t = {
    es: {
      step1Title: "⚠️ Espera un momento...",
      step1Subtitle: "Antes de irte, déjanos mostrarte algo importante",
      analyzing: "Analizando actividad de competidores...",
      continueCancel: "Continuar con cancelación",
      staySubscribed: "Mantener suscripción",
      step2Title: "🎁 Última oportunidad",
      step2Subtitle: "Tenemos una oferta especial solo para ti",
      acceptOffer: "Aceptar oferta",
      noThanks: "No, gracias",
      step3Title: "📋 Ayúdanos a mejorar",
      step3Subtitle: "¿Por qué decidiste cancelar? Tu feedback es valioso",
      reasonLabel: "Motivo de cancelación",
      detailsLabel: "Cuéntanos más (opcional)",
      satisfactionLabel: "¿Qué tan satisfecho estuviste?",
      submitFeedback: "Enviar y cancelar",
      reasons: {
        price: "Es muy caro",
        not_using: "No lo estoy usando",
        missing_features: "Le faltan funciones",
        competitor: "Encontré otra solución",
        other: "Otro motivo",
      },
    },
    pt: {
      step1Title: "⚠️ Aguarde um momento...",
      step1Subtitle: "Antes de ir, deixe-nos mostrar algo importante",
      analyzing: "Analisando atividade dos concorrentes...",
      continueCancel: "Continuar com cancelamento",
      staySubscribed: "Manter assinatura",
      step2Title: "🎁 Última chance",
      step2Subtitle: "Temos uma oferta especial só para você",
      acceptOffer: "Aceitar oferta",
      noThanks: "Não, obrigado",
      step3Title: "📋 Ajude-nos a melhorar",
      step3Subtitle: "Por que você decidiu cancelar? Seu feedback é valioso",
      reasonLabel: "Motivo do cancelamento",
      detailsLabel: "Conte-nos mais (opcional)",
      satisfactionLabel: "Quão satisfeito você ficou?",
      submitFeedback: "Enviar e cancelar",
      reasons: {
        price: "É muito caro",
        not_using: "Não estou usando",
        missing_features: "Faltam recursos",
        competitor: "Encontrei outra solução",
        other: "Outro motivo",
      },
    },
    en: {
      step1Title: "⚠️ Wait a moment...",
      step1Subtitle: "Before you go, let us show you something important",
      analyzing: "Analyzing competitor activity...",
      continueCancel: "Continue with cancellation",
      staySubscribed: "Keep subscription",
      step2Title: "🎁 Last chance",
      step2Subtitle: "We have a special offer just for you",
      acceptOffer: "Accept offer",
      noThanks: "No, thanks",
      step3Title: "📋 Help us improve",
      step3Subtitle: "Why did you decide to cancel? Your feedback is valuable",
      reasonLabel: "Cancellation reason",
      detailsLabel: "Tell us more (optional)",
      satisfactionLabel: "How satisfied were you?",
      submitFeedback: "Submit and cancel",
      reasons: {
        price: "It's too expensive",
        not_using: "I'm not using it",
        missing_features: "Missing features",
        competitor: "Found another solution",
        other: "Other reason",
      },
    },
  };

  const texts = t[language];

  // PASO 1: Micro-Audit
  const handleMicroAudit = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/retention/micro-audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lead_id: leadId,
          subscription_id: subscriptionId,
          language,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMicroAuditData(data);
      }
    } catch (error) {
      console.error("Micro-audit error:", error);
    } finally {
      setLoading(false);
    }
  };

  // PASO 2: Retention Offer
  const handleRetentionOffer = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/retention/retention-offer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lead_id: leadId,
          subscription_id: subscriptionId,
          language,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setRetentionOffer(data.offer);
      }
    } catch (error) {
      console.error("Retention offer error:", error);
    } finally {
      setLoading(false);
    }
  };

  // Aceptar oferta de retención
  const handleAcceptOffer = async () => {
    if (!retentionOffer?.coupon_code) return;

    setLoading(true);
    try {
      const response = await fetch(
        `/api/retention/apply-coupon/${retentionOffer.coupon_code}?subscription_id=${subscriptionId}`,
        { method: "POST" }
      );

      if (response.ok) {
        alert(texts.es === t.es ? "¡Oferta aplicada!" : texts.pt === t.pt ? "Oferta aplicada!" : "Offer applied!");
        onClose();
      }
    } catch (error) {
      console.error("Apply coupon error:", error);
    } finally {
      setLoading(false);
    }
  };

  // PASO 3: Submit Feedback
  const handleSubmitFeedback = async () => {
    if (!reasonCategory) {
      alert("Please select a reason");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch("/api/retention/churn-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lead_id: leadId,
          subscription_id: subscriptionId,
          cancellation_reason: {
            reason_category: reasonCategory,
            reason_detail: reasonDetail,
            satisfaction_score: satisfactionScore,
          },
          accepted_retention_offer: false,
          retention_offer_type: null,
          language,
        }),
      });

      if (response.ok) {
        alert(texts.es === t.es ? "Cancelación completada" : texts.pt === t.pt ? "Cancelamento concluído" : "Cancellation complete");
        onClose();
      }
    } catch (error) {
      console.error("Feedback error:", error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-load Micro-Audit when modal opens
  useState(() => {
    if (isOpen && step === 1 && !microAuditData && !loading) {
      handleMicroAudit();
    }
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70">
      <div className="relative w-full max-w-2xl bg-gray-900 rounded-lg shadow-2xl border border-red-500">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X className="w-6 h-6" />
        </button>

        {/* STEP 1: Micro-Audit Warning */}
        {step === 1 && (
          <div className="p-8">
            <div className="text-center mb-6">
              <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-white mb-2">{texts.step1Title}</h2>
              <p className="text-gray-400">{texts.step1Subtitle}</p>
            </div>

            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-500 mx-auto mb-4"></div>
                <p className="text-gray-400">{texts.analyzing}</p>
              </div>
            ) : microAuditData ? (
              <div className="space-y-4">
                {/* Urgency message */}
                <div className="bg-red-900 bg-opacity-30 border border-red-500 rounded-lg p-4">
                  <p className="text-white text-lg" dangerouslySetInnerHTML={{ __html: microAuditData.urgency_message }} />
                </div>

                {/* Threats detected */}
                {microAuditData.threats_detected.map((threat, idx) => (
                  <div key={idx} className="bg-gray-800 rounded-lg p-4 border border-yellow-600">
                    <div className="flex items-start gap-3">
                      <TrendingDown className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-1" />
                      <div>
                        <h3 className="font-semibold text-white">{threat.competitor_name}</h3>
                        <p className="text-gray-400 text-sm">{threat.details}</p>
                        <div className="flex gap-4 mt-2 text-xs text-gray-500">
                          {Object.entries(threat.metric_change).map(([key, value]) => (
                            <span key={key}>
                              {key}: <span className="text-red-400">{value > 0 ? `+${value}` : value}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Current rank */}
                <div className="bg-gray-800 rounded-lg p-4 text-center">
                  <p className="text-gray-400 text-sm">Tu posición actual</p>
                  <p className="text-4xl font-bold text-white">
                    #{microAuditData.business_current_rank} <span className="text-gray-500 text-lg">/ {microAuditData.total_competitors}</span>
                  </p>
                </div>

                {/* Action buttons */}
                <div className="flex gap-4 mt-6">
                  <button
                    onClick={() => {
                      handleRetentionOffer();
                      setStep(2);
                    }}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition"
                  >
                    {texts.continueCancel}
                  </button>
                  <button
                    onClick={onClose}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition"
                  >
                    {texts.staySubscribed}
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* STEP 2: Retention Offer */}
        {step === 2 && (
          <div className="p-8">
            <div className="text-center mb-6">
              <Gift className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-white mb-2">{texts.step2Title}</h2>
              <p className="text-gray-400">{texts.step2Subtitle}</p>
            </div>

            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto"></div>
              </div>
            ) : retentionOffer ? (
              <div className="space-y-6">
                {/* Offer card */}
                <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-lg p-6 border-2 border-green-500">
                  <div className="text-center">
                    <p className="text-gray-300 text-sm line-through">${retentionOffer.original_price}/mes</p>
                    <p className="text-5xl font-bold text-white mb-2">${retentionOffer.discount_price}/mes</p>
                    <p className="text-green-300 text-lg font-semibold">50% OFF por 2 meses</p>
                    <p className="text-gray-300 text-sm mt-2">Ahorras ${retentionOffer.savings_amount} en total</p>
                  </div>

                  <div className="mt-6 bg-black bg-opacity-30 rounded-lg p-4">
                    <p className="text-white text-sm">
                      🎁 <strong>Bonus:</strong> Reporte premium de palabras clave ocultas de tus competidores
                    </p>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex gap-4">
                  <button
                    onClick={handleAcceptOffer}
                    disabled={loading}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition disabled:opacity-50"
                  >
                    {texts.acceptOffer}
                  </button>
                  <button
                    onClick={() => setStep(3)}
                    className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 px-6 rounded-lg transition"
                  >
                    {texts.noThanks}
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* STEP 3: Feedback Survey */}
        {step === 3 && (
          <div className="p-8">
            <div className="text-center mb-6">
              <MessageSquare className="w-16 h-16 text-blue-500 mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-white mb-2">{texts.step3Title}</h2>
              <p className="text-gray-400">{texts.step3Subtitle}</p>
            </div>

            <div className="space-y-6">
              {/* Reason dropdown */}
              <div>
                <label className="block text-white font-semibold mb-2">{texts.reasonLabel}</label>
                <select
                  value={reasonCategory}
                  onChange={(e) => setReasonCategory(e.target.value)}
                  className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg p-3"
                >
                  <option value="">-- Select --</option>
                  <option value="price">{texts.reasons.price}</option>
                  <option value="not_using">{texts.reasons.not_using}</option>
                  <option value="missing_features">{texts.reasons.missing_features}</option>
                  <option value="competitor">{texts.reasons.competitor}</option>
                  <option value="other">{texts.reasons.other}</option>
                </select>
              </div>

              {/* Details textarea */}
              <div>
                <label className="block text-white font-semibold mb-2">{texts.detailsLabel}</label>
                <textarea
                  value={reasonDetail}
                  onChange={(e) => setReasonDetail(e.target.value)}
                  rows={4}
                  className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg p-3"
                  placeholder="..."
                />
              </div>

              {/* Satisfaction score */}
              <div>
                <label className="block text-white font-semibold mb-2">{texts.satisfactionLabel}</label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((score) => (
                    <button
                      key={score}
                      onClick={() => setSatisfactionScore(score)}
                      className={`flex-1 py-3 rounded-lg font-semibold transition ${
                        satisfactionScore === score
                          ? "bg-blue-600 text-white"
                          : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                      }`}
                    >
                      {score}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit button */}
              <button
                onClick={handleSubmitFeedback}
                disabled={!reasonCategory || loading}
                className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition disabled:opacity-50"
              >
                {texts.submitFeedback}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
