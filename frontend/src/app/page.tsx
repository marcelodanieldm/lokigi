'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import HeroSection from '@/components/HeroSection';
import AnalysisLoader from '@/components/AnalysisLoader';
import LeadCaptureFormModal from '@/components/LeadCaptureFormModal';

type FlowState = 'hero' | 'analyzing' | 'leadCapture';

export default function Home() {
  const [flowState, setFlowState] = useState<FlowState>('hero');
  const [businessName, setBusinessName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // Step 1: User enters business name
  const handleStartAnalysis = (name: string) => {
    setBusinessName(name);
    setFlowState('analyzing');
  };

  // Step 2: Analysis animation complete
  const handleAnalysisComplete = () => {
    setFlowState('leadCapture');
  };

  // Step 3: User submits lead form
  const handleLeadSubmit = async (email: string, phone: string) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/leads`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          business_name: businessName,
          email: email,
          phone: phone || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al procesar la solicitud');
      }

      const result = await response.json();
      
      // Redirect to audit results
      router.push(`/audit/${result.id}`);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen relative">
      {/* Hero Section - Always rendered for smooth transitions */}
      {flowState === 'hero' && (
        <HeroSection onStartAnalysis={handleStartAnalysis} />
      )}

      {/* Analysis Loader - Full screen overlay */}
      {flowState === 'analyzing' && (
        <AnalysisLoader 
          businessName={businessName}
          onComplete={handleAnalysisComplete}
        />
      )}

      {/* Lead Capture Modal - Full screen overlay */}
      {flowState === 'leadCapture' && (
        <LeadCaptureFormModal
          businessName={businessName}
          onSubmit={handleLeadSubmit}
          isLoading={isSubmitting}
        />
      )}

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-4 right-4 z-[100] max-w-md animate-slide-in">
          <div className="card border-2 border-danger-500 bg-dark-800">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-danger-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-white text-sm">✕</span>
              </div>
              <div className="flex-1">
                <p className="font-semibold text-white mb-1">Error</p>
                <p className="text-sm text-gray-400">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-gray-500 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

