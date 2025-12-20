'use client';

import { useState } from 'react';
import { Mail, Phone, Building2, ArrowRight } from 'lucide-react';

interface LeadFormProps {
  onSubmit: (data: LeadFormData) => void;
  isLoading: boolean;
}

export interface LeadFormData {
  email: string;
  telefono: string;
  nombre_negocio: string;
}

export default function LeadForm({ onSubmit, isLoading }: LeadFormProps) {
  const [formData, setFormData] = useState<LeadFormData>({
    email: '',
    telefono: '',
    nombre_negocio: '',
  });

  const [errors, setErrors] = useState<Partial<LeadFormData>>({});

  const validateForm = () => {
    const newErrors: Partial<LeadFormData> = {};

    if (!formData.email) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!formData.telefono) {
      newErrors.telefono = 'El teléfono es requerido';
    } else if (!/^\+?[\d\s-()]+$/.test(formData.telefono)) {
      newErrors.telefono = 'Teléfono inválido';
    }

    if (!formData.nombre_negocio || formData.nombre_negocio.length < 3) {
      newErrors.nombre_negocio = 'El nombre del negocio debe tener al menos 3 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleChange = (field: keyof LeadFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Limpiar error del campo al escribir
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12">
      <div className="max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-block p-4 bg-gradient-to-r from-red-500 to-orange-500 rounded-2xl mb-4">
            <Building2 className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Descubre cómo está tu negocio en Google
          </h1>
          <p className="text-xl text-gray-600">
            Análisis gratuito de tu presencia local en menos de 60 segundos
          </p>
        </div>

        {/* Benefits */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-3xl mb-2">🎯</div>
            <div className="text-sm font-semibold text-gray-900">Score de salud</div>
            <div className="text-xs text-gray-600">Tu posición real vs competencia</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-3xl mb-2">🚨</div>
            <div className="text-sm font-semibold text-gray-900">Fallos críticos</div>
            <div className="text-xs text-gray-600">Qué está costándote dinero</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-3xl mb-2">💰</div>
            <div className="text-sm font-semibold text-gray-900">Impacto económico</div>
            <div className="text-xs text-gray-600">Cuánto pierdes cada mes</div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="card space-y-6">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Nombre de tu negocio *
            </label>
            <div className="relative">
              <Building2 className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={formData.nombre_negocio}
                onChange={(e) => handleChange('nombre_negocio', e.target.value)}
                placeholder="Ej: Restaurante El Sabor"
                className={`w-full pl-12 pr-4 py-4 rounded-xl border-2 ${
                  errors.nombre_negocio ? 'border-red-500' : 'border-gray-200'
                } focus:border-orange-500 focus:outline-none transition-colors text-gray-900 font-medium`}
                disabled={isLoading}
              />
            </div>
            {errors.nombre_negocio && (
              <p className="mt-2 text-sm text-red-600">{errors.nombre_negocio}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Email *
            </label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="tu@email.com"
                className={`w-full pl-12 pr-4 py-4 rounded-xl border-2 ${
                  errors.email ? 'border-red-500' : 'border-gray-200'
                } focus:border-orange-500 focus:outline-none transition-colors text-gray-900 font-medium`}
                disabled={isLoading}
              />
            </div>
            {errors.email && (
              <p className="mt-2 text-sm text-red-600">{errors.email}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Teléfono *
            </label>
            <div className="relative">
              <Phone className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="tel"
                value={formData.telefono}
                onChange={(e) => handleChange('telefono', e.target.value)}
                placeholder="+34 612 345 678"
                className={`w-full pl-12 pr-4 py-4 rounded-xl border-2 ${
                  errors.telefono ? 'border-red-500' : 'border-gray-200'
                } focus:border-orange-500 focus:outline-none transition-colors text-gray-900 font-medium`}
                disabled={isLoading}
              />
            </div>
            {errors.telefono && (
              <p className="mt-2 text-sm text-red-600">{errors.telefono}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-primary flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Analizando tu negocio...
              </>
            ) : (
              <>
                Ver mi auditoría GRATIS
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>

          <p className="text-xs text-center text-gray-500">
            🔒 Tus datos están seguros. No compartimos información con terceros.
          </p>
        </form>

        {/* Trust signals */}
        <div className="mt-8 flex items-center justify-center gap-8 flex-wrap text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span className="text-green-500 text-xl">✓</span>
            <span>Sin tarjeta de crédito</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-green-500 text-xl">✓</span>
            <span>Resultados en 60 segundos</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-green-500 text-xl">✓</span>
            <span>100% gratis</span>
          </div>
        </div>
      </div>
    </div>
  );
}
