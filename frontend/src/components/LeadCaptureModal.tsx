'use client';

import { useState } from 'react';
import { X, Lock, Sparkles, CheckCircle2 } from 'lucide-react';

interface LeadCaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: LeadData) => Promise<void>;
  businessName: string;
  score: number;
}

interface LeadData {
  nombre: string;
  email: string;
  telefono: string;
  whatsapp: string;
  nombre_negocio: string;
  score_visibilidad: number;
  fallos_criticos: any;
  audit_data: any;
}

export default function LeadCaptureModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  businessName,
  score 
}: LeadCaptureModalProps) {
  const [formData, setFormData] = useState({
    nombre: '',
    email: '',
    telefono: '',
    whatsapp: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    // Validaciones
    if (!formData.nombre || !formData.email || !formData.telefono) {
      setError('Por favor completa todos los campos obligatorios');
      return;
    }

    // Validar email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Por favor ingresa un email válido');
      return;
    }

    // Validar teléfono (solo números)
    const phoneRegex = /^[0-9]{8,15}$/;
    if (!phoneRegex.test(formData.telefono.replace(/[^0-9]/g, ''))) {
      setError('Por favor ingresa un teléfono válido (8-15 dígitos)');
      return;
    }

    setIsSubmitting(true);
    
    try {
      await onSubmit({
        ...formData,
        whatsapp: formData.whatsapp || formData.telefono,
        nombre_negocio: businessName,
        score_visibilidad: score,
        fallos_criticos: null,
        audit_data: null
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error al guardar tus datos. Intenta nuevamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isSubmitting) {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={handleBackdropClick}
    >
      <div className="relative bg-white rounded-3xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Close Button */}
        {!isSubmitting && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full transition-colors z-10"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        )}

        {/* Header - Mejorado con urgencia */}
        <div className="bg-gradient-to-r from-red-600 via-orange-600 to-red-600 p-8 text-white rounded-t-3xl relative overflow-hidden">
          {/* Animated background */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.8),transparent_50%)] animate-pulse" />
          </div>
          
          <div className="relative z-10">
            <div className="flex items-center justify-center mb-4">
              <div className="bg-white/20 backdrop-blur-sm rounded-full p-4 animate-bounce">
                <Lock className="w-10 h-10" />
              </div>
            </div>
            <h2 className="text-4xl font-black text-center mb-3">
              ¡Espera! 🚨
            </h2>
            <p className="text-white text-center text-xl font-bold leading-relaxed">
              Estás a <span className="underline decoration-2">30 segundos</span> de descubrir cómo arreglar 
              estos fallos críticos
            </p>
            <p className="text-white/80 text-center text-sm mt-2">
              No requiere tarjeta de crédito · 100% GRATIS
            </p>
          </div>
        </div>

        {/* Body */}
        <div className="p-8">
          {/* Benefits - Mejorado con más impacto visual */}
          <div className="bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 rounded-2xl p-6 mb-6 border-2 border-orange-300 shadow-lg">
            <div className="flex items-start gap-3 mb-4">
              <div className="bg-gradient-to-br from-orange-500 to-red-500 rounded-full p-2">
                <Sparkles className="w-6 h-6 text-white flex-shrink-0" />
              </div>
              <div>
                <h3 className="font-black text-gray-900 mb-3 text-lg">
                  🎁 Desbloquearás GRATIS al instante:
                </h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold text-gray-900">Plan de Acción Paso a Paso</div>
                      <div className="text-sm text-gray-600">Personalizado para {businessName}</div>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold text-gray-900">Comparativa con tu Competencia</div>
                      <div className="text-sm text-gray-600">Ve exactamente qué te falta para superarlos</div>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold text-gray-900">Estimación de Pérdidas Mensuales</div>
                      <div className="text-sm text-gray-600">Descubre cuánto $ pierdes cada mes por estos fallos</div>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="font-bold text-gray-900">Checklist de Optimización</div>
                      <div className="text-sm text-gray-600">Priorizado por impacto económico</div>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Urgencia y escasez */}
          <div className="bg-yellow-100 border-2 border-yellow-400 rounded-xl p-4 mb-6 text-center">
            <p className="text-yellow-900 font-bold">
              ⏰ Cada día sin actuar = <span className="text-red-600">$170 USD perdidos</span>
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Nombre */}
            <div>
              <label htmlFor="nombre" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                👤 Tu Nombre Completo *
              </label>
              <input
                type="text"
                id="nombre"
                value={formData.nombre}
                onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                className="w-full px-4 py-4 rounded-xl border-2 border-gray-300 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 focus:outline-none transition-all text-lg"
                placeholder="Ej: Juan Pérez"
                required
                disabled={isSubmitting}
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                ✉️ Email *
              </label>
              <input
                type="email"
                id="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-4 rounded-xl border-2 border-gray-300 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 focus:outline-none transition-all text-lg"
                placeholder="tu@email.com"
                required
                disabled={isSubmitting}
              />
            </div>

            {/* Teléfono */}
            <div>
              <label htmlFor="telefono" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                📱 Teléfono *
              </label>
              <input
                type="tel"
                id="telefono"
                value={formData.telefono}
                onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
                className="w-full px-4 py-4 rounded-xl border-2 border-gray-300 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 focus:outline-none transition-all text-lg"
                placeholder="+54 11 1234-5678"
                required
                disabled={isSubmitting}
              />
            </div>

            {/* WhatsApp */}
            <div>
              <label htmlFor="whatsapp" className="block text-sm font-bold text-gray-700 mb-2 flex items-center gap-2">
                💬 WhatsApp
                <span className="text-xs font-normal text-gray-500">(Opcional - Recomendado)</span>
              </label>
              <input
                type="tel"
                id="whatsapp"
                value={formData.whatsapp}
                onChange={(e) => setFormData({ ...formData, whatsapp: e.target.value })}
                className="w-full px-4 py-4 rounded-xl border-2 border-gray-300 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 focus:outline-none transition-all text-lg"
                placeholder="Si es diferente al teléfono"
                disabled={isSubmitting}
              />
              <p className="text-xs text-gray-600 mt-2 flex items-center gap-1">
                <span>💡</span>
                <span>Te contactaremos más rápido por WhatsApp</span>
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border-2 border-red-300 rounded-xl p-4 flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <p className="text-sm text-red-700 font-medium">{error}</p>
              </div>
            )}

            {/* Submit Button - Mejorado con más impacto */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-gradient-to-r from-orange-500 via-red-500 to-orange-500 text-white font-black text-xl py-5 rounded-2xl hover:from-orange-600 hover:via-red-600 hover:to-orange-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-2xl hover:shadow-3xl transform hover:scale-105 relative overflow-hidden group"
            >
              <span className="relative z-10 flex items-center justify-center gap-2">
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Guardando tus datos...</span>
                  </>
                ) : (
                  <>
                    <span>🔓 DESBLOQUEAR MI PLAN GRATIS AHORA</span>
                  </>
                )}
              </span>
              {/* Button shine effect */}
              <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/30 to-transparent" />
            </button>

            <p className="text-center text-sm text-gray-600 font-medium">
              ⚡ Acceso instantáneo · Sin costo · Sin tarjeta
            </p>
          </form>

          {/* Trust Badges - Mejorados */}
          <div className="mt-6 space-y-3">
            <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
              <span className="text-green-500 text-xl">✓</span>
              <span className="font-medium">500+ dueños de negocio nos confían</span>
            </div>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
              <span className="text-green-500 text-xl">✓</span>
              <span className="font-medium">Tus datos están 100% seguros (SSL)</span>
            </div>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-600">
              <span className="text-green-500 text-xl">✓</span>
              <span className="font-medium">No spam, no compartimos tu info</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
