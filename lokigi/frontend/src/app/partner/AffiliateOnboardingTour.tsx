// AffiliateOnboardingTour.tsx
// Onboarding interactivo para el Partner Portal de Lokigi
import React, { useState } from 'react';

const steps = [
  {
    title: '¡Bienvenido al Partner Portal!',
    content: 'Aquí puedes monitorear tus clics, leads y comisiones en tiempo real.',
    target: '#metrics',
  },
  {
    title: 'Tu link de afiliado',
    content: 'Copia tu link único y genera un QR para compartirlo en redes o impresos.',
    target: '#link-generator',
  },
  {
    title: 'Media Kit',
    content: 'Descarga banners y capturas para potenciar tu promoción.',
    target: '#media-kit',
  },
  {
    title: '¿Dudas?',
    content: 'Consulta la guía visual de onboarding o contacta soporte desde aquí.',
    target: '#onboarding-guide',
  },
];

export default function AffiliateOnboardingTour() {
  const [step, setStep] = useState(0);
  const [active, setActive] = useState(true);
  if (!active) return null;
  const current = steps[step];
  // Encuentra el target y calcula posición (simple overlay)
  const targetEl = typeof window !== 'undefined' ? document.querySelector(current.target) : null;
  const style = targetEl ? {
    position: 'absolute',
    top: targetEl.getBoundingClientRect().top + window.scrollY - 10,
    left: targetEl.getBoundingClientRect().left + window.scrollX - 10,
    zIndex: 1000,
    width: targetEl.offsetWidth + 20,
    height: targetEl.offsetHeight + 20,
    pointerEvents: 'none',
    border: '2px solid #22d3ee',
    borderRadius: '12px',
    boxShadow: '0 0 24px #22d3ee88',
  } : {};
  return (
    <>
      {targetEl && <div style={style} />}
      <div className="fixed bottom-8 right-8 z-[2000] bg-gray-900 border border-green-400 rounded-xl shadow-xl p-6 max-w-xs animate-fade-in">
        <h2 className="text-lg font-bold text-green-400 mb-2">{current.title}</h2>
        <p className="text-white mb-4">{current.content}</p>
        <div className="flex gap-2">
          {step > 0 && (
            <button className="px-3 py-1 bg-gray-800 text-green-300 rounded" onClick={() => setStep(step-1)}>Anterior</button>
          )}
          {step < steps.length-1 ? (
            <button className="px-3 py-1 bg-green-400 text-gray-900 font-bold rounded" onClick={() => setStep(step+1)}>Siguiente</button>
          ) : (
            <button className="px-3 py-1 bg-green-400 text-gray-900 font-bold rounded" onClick={() => setActive(false)}>Finalizar</button>
          )}
        </div>
      </div>
    </>
  );
}

// Documentación:
// - Usa <AffiliateOnboardingTour /> en el Partner Portal.
// - Asegúrate de que los elementos tengan los IDs: #metrics, #link-generator, #media-kit, #onboarding-guide.
// - El overlay resalta la sección relevante y el modal guía al usuario paso a paso.
// - El tour solo debe mostrarse en el primer acceso (puede usarse localStorage).
