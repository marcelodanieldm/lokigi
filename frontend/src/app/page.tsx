'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import LeadForm, { LeadFormData } from '@/components/LeadForm';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (data: LeadFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/leads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al procesar la solicitud');
      }

      const result = await response.json();
      
      // Redirigir a la página de resultados
      router.push(`/audit/${result.id}`);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen">
      <LeadForm onSubmit={handleSubmit} isLoading={isLoading} />
      
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-xl shadow-lg max-w-md">
          <p className="font-semibold">Error</p>
          <p className="text-sm">{error}</p>
        </div>
      )}
    </main>
  );
}

