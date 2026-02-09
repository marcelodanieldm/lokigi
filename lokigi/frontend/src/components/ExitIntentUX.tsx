// UX/UI: Exit Intent Modal, Countdown y Social Proof para Lokigi
// Autor: UX/UI Designer (2025)

// 1. ExitIntentModal.tsx
import React, { useEffect, useState } from 'react';

export const ExitIntentModal = ({ onAccept, show, onClose }: {
  onAccept: () => void;
  show: boolean;
  onClose: () => void;
}) => {
  if (!show) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
      <div className="bg-gray-900 rounded-xl shadow-xl p-8 max-w-md w-full border-2 border-green-400 animate-pulse">
        <h2 className="text-2xl font-bold text-green-400 mb-2">¡Espera!</h2>
        <p className="text-white mb-4">Tu competencia no descansa.<br/>Llévate el <span className="font-semibold text-green-300">plan de optimización</span> con un <span className="font-bold text-green-400">15% de descuento</span> solo por los próximos <span className="font-mono text-green-300">10 minutos</span>.</p>
        <button
          className="w-full py-2 mt-2 bg-green-400 text-gray-900 font-bold rounded hover:bg-green-300 transition"
          onClick={onAccept}
        >
          ¡Aprovechar oferta!
        </button>
        <button
          className="w-full py-1 mt-2 text-sm text-gray-400 hover:text-white"
          onClick={onClose}
        >
          No, gracias
        </button>
      </div>
    </div>
  );
};

// 2. CountdownTimer.tsx
import React, { useEffect, useState } from 'react';

export const CountdownTimer = ({ minutes, onExpire }: { minutes: number; onExpire: () => void }) => {
  const [secondsLeft, setSecondsLeft] = useState(minutes * 60);
  useEffect(() => {
    if (secondsLeft <= 0) {
      onExpire();
      return;
    }
    const interval = setInterval(() => setSecondsLeft(s => s - 1), 1000);
    return () => clearInterval(interval);
  }, [secondsLeft, onExpire]);
  const min = Math.floor(secondsLeft / 60);
  const sec = secondsLeft % 60;
  return (
    <div className="flex items-center justify-center gap-2 mt-2">
      <span className="text-lg font-mono text-green-400 animate-pulse">{min.toString().padStart(2, '0')}:{sec.toString().padStart(2, '0')}</span>
      <span className="text-xs text-green-300">Oferta expira pronto</span>
    </div>
  );
};

// 3. SocialProofWidget.tsx
import React, { useEffect, useState } from 'react';

const cities = [
  'Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao', 'Monterrey', 'CDMX', 'Buenos Aires', 'Lima', 'Bogotá', 'Miami', 'Santiago', 'Quito', 'Guadalajara', 'Medellín'
];

function getRandomCity() {
  return cities[Math.floor(Math.random() * cities.length)];
}

export const SocialProofWidget = () => {
  const [city, setCity] = useState(getRandomCity());
  useEffect(() => {
    const interval = setInterval(() => setCity(getRandomCity()), 9000);
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="fixed bottom-4 right-4 z-40 bg-gray-900 bg-opacity-90 border border-green-400 rounded-lg px-4 py-2 shadow-lg flex items-center gap-2 animate-bounce">
      <span className="text-green-400 text-lg">●</span>
      <span className="text-white text-sm">Alguien en <span className="font-bold text-green-300">{city}</span> acaba de optimizar su negocio con Lokigi</span>
    </div>
  );
};

// ---
// Documentación de integración:
// 1. Importa y monta <ExitIntentModal /> en el layout raíz. Detecta intentos de salida con eventos de mouse (onMouseLeave window).
// 2. Usa <CountdownTimer minutes={10} /> en el checkout para ofertas urgentes.
// 3. Monta <SocialProofWidget /> en el layout global para social proof dinámico.
// Todos los componentes usan Tailwind CSS y colores de marca (verde neón).
