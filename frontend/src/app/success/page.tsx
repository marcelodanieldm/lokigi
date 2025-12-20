'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle2, Download, ArrowRight } from 'lucide-react';

export default function SuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const leadId = searchParams.get('lead_id');
  const [countdown, setCountdown] = useState(10);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          if (leadId) {
            router.push(`/audit/${leadId}`);
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [leadId, router]);

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-2xl w-full text-center">
        {/* Success Icon */}
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-green-100 rounded-full mb-4 animate-bounce">
            <CheckCircle2 className="w-16 h-16 text-green-600" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            ¡Pago Exitoso! 🎉
          </h1>
          <p className="text-xl text-gray-600">
            Tu Plan de Acción Express está siendo preparado
          </p>
        </div>

        {/* What's next */}
        <div className="card text-left space-y-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900">¿Qué sigue?</h2>
          
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 bg-green-50 rounded-xl">
              <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">Confirmación por email</h3>
                <p className="text-sm text-gray-600">
                  Recibirás un email de confirmación con los detalles de tu compra en los próximos minutos.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 bg-blue-50 rounded-xl">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">PDF personalizado en 24h</h3>
                <p className="text-sm text-gray-600">
                  Nuestro equipo preparará tu Plan de Acción Express con los pasos exactos para mejorar tu SEO Local.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 bg-purple-50 rounded-xl">
              <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold">
                3
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">Acceso al dashboard</h3>
                <p className="text-sm text-gray-600">
                  Podrás hacer seguimiento de las mejoras y ver el impacto en tu negocio.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="space-y-4">
          <button
            onClick={() => leadId && router.push(`/audit/${leadId}`)}
            className="w-full md:w-auto btn-primary flex items-center justify-center gap-3 mx-auto"
          >
            <Download className="w-5 h-5" />
            Ver mi auditoría completa
            <ArrowRight className="w-5 h-5" />
          </button>

          <p className="text-sm text-gray-500">
            Redirigiendo automáticamente en {countdown} segundos...
          </p>
        </div>

        {/* Support */}
        <div className="mt-8 p-6 bg-gray-50 rounded-xl">
          <p className="text-sm text-gray-600">
            ¿Necesitas ayuda? Contáctanos en{' '}
            <a href="mailto:support@lokigi.com" className="text-orange-600 font-semibold hover:underline">
              support@lokigi.com
            </a>
          </p>
        </div>
      </div>
    </main>
  );
}
