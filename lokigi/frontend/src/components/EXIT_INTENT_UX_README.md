# Exit Intent Flow y Cupones Dinámicos - Documentación UX/UI

## Objetivo
Retener usuarios antes de abandonar la web y aumentar conversiones con ofertas urgentes y social proof.

## Componentes

### 1. ExitIntentModal
- Modal minimalista que aparece cuando el mouse se dirige a cerrar la pestaña.
- Mensaje: "¡Espera! Tu competencia no descansa. Llévate el plan de optimización con un 15% de descuento solo por los próximos 10 minutos."
- Botón de acción destacado y opción de cerrar.
- Colores: Fondo oscuro, bordes y acentos en verde neón (Tailwind: `bg-gray-900`, `border-green-400`, `text-green-400`).

### 2. CountdownTimer
- Componente de cuenta regresiva para el checkout.
- Visualmente "estresante" pero profesional, usando verde neón y animaciones.
- Mensaje de urgencia: "Oferta expira pronto".

### 3. SocialProofWidget
- Widget flotante en la esquina inferior derecha.
- Mensaje: "Alguien en [Ciudad] acaba de optimizar su negocio con Lokigi".
- Cambia de ciudad cada 9 segundos (lista de ciudades relevantes).
- Icono verde y animación bounce para captar atención.

## Integración
- Montar `<ExitIntentModal />` en el layout raíz. Detectar intentos de salida con `window.addEventListener('mouseleave', ...)`.
- Usar `<CountdownTimer minutes={10} />` en el checkout cuando se active la oferta.
- Montar `<SocialProofWidget />` en el layout global para mostrar social proof en todo momento.
- Todos los componentes usan Tailwind CSS y colores de marca.

## Ejemplo de Uso
```tsx
import { ExitIntentModal, CountdownTimer, SocialProofWidget } from './components/ExitIntentUX';

// En el layout global:
<ExitIntentModal show={showExitModal} onAccept={handleAccept} onClose={handleClose} />
<SocialProofWidget />

// En el checkout:
<CountdownTimer minutes={10} onExpire={handleExpire} />
```

## Buenas Prácticas
- No mostrar el modal más de una vez por sesión.
- El timer debe ser real y no reiniciarse al refrescar.
- El social proof debe ser discreto pero visible.

---
Última actualización: 2025-12-29
