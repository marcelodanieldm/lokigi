// AffiliateOnboardingTour.tsx
// Onboarding interactivo para el Partner Portal de Lokigi
import React, { useState, useEffect } from 'react';
import { affiliateOnboardingSteps } from './affiliateOnboardingSteps';

function AffiliateOnboardingTour() {
  const [step, setStep] = useState<number>(0);
  const [active, setActive] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return !localStorage.getItem('affiliateOnboardingCompleted');
    }
    return true;
  });
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  useEffect(() => {
    if (!active && typeof window !== 'undefined') {
      localStorage.setItem('affiliateOnboardingCompleted', 'true');
    }
  }, [active]);
  if (!active) return null;
  const current = affiliateOnboardingSteps[step];
  // Encuentra el target y calcula posición (simple overlay)
  const targetEl = typeof window !== 'undefined' ? document.querySelector(current.target) as HTMLElement | null : null;
  const style = targetEl ? {
    position: 'absolute' as const,
    top: targetEl.getBoundingClientRect().top + window.scrollY - 10,
    left: targetEl.getBoundingClientRect().left + window.scrollX - 10,
    zIndex: 1000,
    width: (targetEl as HTMLElement).offsetWidth + 20,
    height: (targetEl as HTMLElement).offsetHeight + 20,
    pointerEvents: 'none' as const,
    border: '2px solid #22d3ee',
    borderRadius: '12px',
    boxShadow: '0 0 24px #22d3ee88',
  } : {};
  const handleNext = () => {
    setCompletedSteps((prev: number[]) => prev.indexOf(step) !== -1 ? prev : [...prev, step]);
    setStep((s: number) => Math.min(s + 1, affiliateOnboardingSteps.length - 1));
  };
  const handlePrev = () => setStep((s: number) => Math.max(s - 1, 0));
  const handleFinish = () => {
    setCompletedSteps((prev: number[]) => prev.indexOf(step) !== -1 ? prev : [...prev, step]);
    setActive(false);
  };
  return (
    <>
      {targetEl && <div style={style} />}
      <div className="fixed bottom-8 right-8 z-[2000] bg-gray-900 border border-green-400 rounded-xl shadow-xl p-6 max-w-xs animate-fade-in">
        <h2 className="text-lg font-bold text-green-400 mb-2">{current.title}</h2>
        <p className="text-white mb-4">{current.content}</p>
        <div className="flex gap-2 mb-2">
          {step > 0 && (
            <button className="px-3 py-1 bg-gray-800 text-green-300 rounded" onClick={handlePrev}>Anterior</button>
          )}
          {step < affiliateOnboardingSteps.length-1 ? (
            <button className="px-3 py-1 bg-green-400 text-gray-900 font-bold rounded" onClick={handleNext}>Siguiente</button>
          ) : (
            <button className="px-3 py-1 bg-green-400 text-gray-900 font-bold rounded" onClick={handleFinish}>Finalizar</button>
          )}
        </div>
        <div className="flex items-center gap-1 mt-2">
          {affiliateOnboardingSteps.map((_, i) => (
            <span key={i} className={`w-2 h-2 rounded-full ${completedSteps.indexOf(i) !== -1 ? 'bg-green-400' : i === step ? 'bg-green-300' : 'bg-gray-700'}`}></span>
          ))}
        </div>
      </div>
    </>
  );
}

export default AffiliateOnboardingTour;

// Documentación:
// - Usa <AffiliateOnboardingTour /> en el Partner Portal.
// - Asegúrate de que los elementos tengan los IDs: #metrics, #link-generator, #media-kit, #onboarding-guide.
// - El overlay resalta la sección relevante y el modal guía al usuario paso a paso.
// - El tour solo debe mostrarse en el primer acceso (puede usarse localStorage).
