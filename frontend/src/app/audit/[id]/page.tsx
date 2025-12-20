'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import AuditResults from '@/components/AuditResults';

interface AuditData {
  lead: {
    id: number;
    email: string;
    nombre_negocio: string;
  };
  datos_analizados: {
    nombre: string;
    rating: number;
    numero_resenas: number;
    tiene_sitio_web: boolean;
    fecha_ultima_foto: string;
  };
  reporte: {
    fallos_criticos: Array<{
      titulo: string;
      descripcion: string;
      impacto_economico: string;
    }>;
    score_visibilidad: number;
  };
  oferta_plan_express: boolean;
  payment_status: string;
}

export default function AuditPage({ params }: { params: { id: string } }) {
  const [auditData, setAuditData] = useState<AuditData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCheckoutLoading, setIsCheckoutLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchAuditData();
  }, [params.id]);

  const fetchAuditData = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/leads/${params.id}/audit`);
      
      if (!response.ok) {
        throw new Error('No se pudo cargar la auditoría');
      }

      const data = await response.json();
      setAuditData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCheckout = async () => {
    setIsCheckoutLoading(true);
    
    try {
      const response = await fetch(`http://localhost:8000/api/leads/${params.id}/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear checkout');
      }

      const data = await response.json();
      
      // Redirigir a Stripe Checkout
      window.location.href = data.checkout_url;
      
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al procesar el pago');
      setIsCheckoutLoading(false);
    }
  };

  if (isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Cargando tu auditoría...</p>
        </div>
      </main>
    );
  }

  if (error || !auditData) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            No pudimos cargar tu auditoría
          </h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-3 bg-orange-500 text-white rounded-xl font-semibold hover:bg-orange-600 transition-colors"
          >
            Volver al inicio
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen py-12 px-4">
      <AuditResults 
        auditData={auditData}
        onCheckout={handleCheckout}
        isCheckoutLoading={isCheckoutLoading}
      />
    </main>
  );
}
