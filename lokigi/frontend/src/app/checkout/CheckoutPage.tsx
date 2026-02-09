// checkout/CheckoutPage.tsx
import React, { useState } from 'react';
import { CountdownTimer } from '../components/ExitIntentUX';

export default function CheckoutPage() {
  const [offerActive, setOfferActive] = useState(true); // Simula si la oferta está activa
  const handleExpire = () => {
    setOfferActive(false);
    // Aquí puedes desactivar el cupón o mostrar mensaje de expirado
  };
  return (
    <div className="max-w-lg mx-auto mt-12 p-6 bg-gray-900 rounded-xl shadow-lg border border-green-400">
      <h1 className="text-2xl font-bold text-green-400 mb-4">Finaliza tu optimización</h1>
      {offerActive && (
        <div className="mb-4">
          <div className="text-green-300 font-semibold mb-1">¡15% de descuento solo por tiempo limitado!</div>
          <CountdownTimer minutes={10} onExpire={handleExpire} />
        </div>
      )}
      {/* ...formulario de pago, resumen, etc... */}
      {!offerActive && (
        <div className="text-red-400 font-bold mt-4">La oferta ha expirado.</div>
      )}
      <button className="w-full py-2 mt-6 bg-green-400 text-gray-900 font-bold rounded hover:bg-green-300 transition">
        Pagar y optimizar mi negocio
      </button>
    </div>
  );
}

// Documentación:
// - Usa este componente como página de checkout.
// - El CountdownTimer muestra la urgencia y desactiva la oferta al expirar.
// - Personaliza la lógica de cupón y expiración según tu backend.
