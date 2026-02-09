# Public Audit Landing Page (Lokigi)

## Objetivo
Página viral y mobile-first para auditoría pública, optimizada para WhatsApp/Instagram.

## Implementación

### 1. Efecto de Carga
- Al abrir el link, muestra un progreso animado: 'Verificando seguridad de tu perfil...'.
- Refuerza autoridad y genera expectativa.

### 2. Hero de Impacto
- Mensaje central: 'Tu negocio está perdiendo aproximadamente [Monto] por mes'.
- Visual ultra-impactante, acento rojo para el monto.

### 3. Gráfica de Competencia
- Barras animadas (Tailwind, sin frameworks pesados) que aparecen al hacer scroll.
- Componente `BarAnim` con animación por delay.

### 4. Mobile-First
- Layout vertical, paddings y fuentes grandes.
- 100% optimizada para móviles y carga instantánea.

## Ejemplo de Uso

```tsx
import PublicAuditLanding from "./PublicAuditLanding";

<PublicAuditLanding
  loss={1200}
  currency="USD"
  competitors={[
    { name: "Competidor A", score: 90 },
    { name: "Tu Negocio", score: 65 },
    { name: "Competidor B", score: 80 }
  ]}
/>
```

## Estética
- Dark mode (`bg-gray-950`), tipografía técnica (`font-mono`), acentos verde neón y rojo.
- Ultra-liviana, sin frameworks pesados.

---

**UX/UI Designer: Landing validada y lista para viralizar.**
