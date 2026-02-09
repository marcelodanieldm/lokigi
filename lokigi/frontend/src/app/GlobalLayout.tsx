// GlobalLayout.tsx
// Integra ExitIntentModal, SocialProofWidget y soporte para CountdownTimer en el layout global de Lokigi

import React, { useEffect, useState } from 'react';
import { ExitIntentModal, SocialProofWidget } from './components/ExitIntentUX';

export default function GlobalLayout({ children }: { children: React.ReactNode }) {
  const [showExitModal, setShowExitModal] = useState(false);
  const [exitModalShown, setExitModalShown] = useState(false);

  useEffect(() => {
    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY <= 0 && !exitModalShown) {
        setShowExitModal(true);
        setExitModalShown(true);
      }
    };
    window.addEventListener('mouseleave', handleMouseLeave);
    return () => window.removeEventListener('mouseleave', handleMouseLeave);
  }, [exitModalShown]);

  const handleAccept = () => {
    setShowExitModal(false);
    // Aquí puedes redirigir al checkout o activar el cupón
  };
  const handleClose = () => setShowExitModal(false);

  return (
    <>
      <ExitIntentModal show={showExitModal} onAccept={handleAccept} onClose={handleClose} />
      <SocialProofWidget />
      <main>{children}</main>
    </>
  );
}

// Documentación:
// - Usa este layout en _app.tsx o layout.tsx de Next.js para aplicar a toda la app.
// - El ExitIntentModal solo aparece una vez por sesión.
// - SocialProofWidget siempre visible en la esquina inferior derecha.
// - Para el CountdownTimer, intégralo en el componente de checkout según la lógica de oferta.
