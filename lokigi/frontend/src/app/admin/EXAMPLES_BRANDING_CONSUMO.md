# Ejemplos de Consumo de Branding Multi-Tenant en el Frontend (Next.js)

## 1. Acceso a headers de branding en el cliente (Next.js)

```ts
// utils/getBrandingFromHeaders.ts
export function getBrandingFromHeaders(): {
  color: string;
  logo: string;
  name: string;
  agencyId: string;
} {
  if (typeof window === 'undefined') return { color: '', logo: '', name: '', agencyId: '' };
  return {
    color: window?.document?.head?.querySelector('meta[name="x-agency-color"]')?.getAttribute('content') || '',
    logo: window?.document?.head?.querySelector('meta[name="x-agency-logo"]')?.getAttribute('content') || '',
    name: window?.document?.head?.querySelector('meta[name="x-agency-name"]')?.getAttribute('content') || '',
    agencyId: window?.document?.head?.querySelector('meta[name="x-agency-id"]')?.getAttribute('content') || '',
  };
}
```

## 2. Uso en un componente React (aplicando color y logo)

```tsx
import React, { useEffect, useState } from 'react';
import { getBrandingFromHeaders } from '../utils/getBrandingFromHeaders';

export default function AgencyBrandingBar() {
  const [branding, setBranding] = useState({ color: '', logo: '', name: '', agencyId: '' });
  useEffect(() => {
    setBranding(getBrandingFromHeaders());
  }, []);
  return (
    <div style={{ background: branding.color || '#22d3ee' }} className="w-full flex items-center gap-4 p-2">
      {branding.logo && <img src={branding.logo} alt="Logo" className="h-8 rounded" />}
      <span className="font-bold text-white text-lg">{branding.name || 'Lokigi'}</span>
    </div>
  );
}
```

## 3. Aplicar CSS Variables globales (para Tailwind)

```tsx
// En _app.tsx o layout.tsx
import React, { useEffect } from 'react';
import { getBrandingFromHeaders } from '../utils/getBrandingFromHeaders';

export default function AppLayout({ children }) {
  useEffect(() => {
    const branding = getBrandingFromHeaders();
    if (branding.color) {
      document.documentElement.style.setProperty('--agency-primary', branding.color);
    }
  }, []);
  return <>{children}</>;
}
```

En tu tailwind.config.js:
```js
module.exports = {
  theme: {
    extend: {
      colors: {
        agency: {
          primary: 'var(--agency-primary)',
        },
      },
    },
  },
};
```

## 4. Ejemplo en PDF/WhiteLabelReport

```tsx
import WhiteLabelReport from '../admin/WhiteLabelReport';
import { getBrandingFromHeaders } from '../utils/getBrandingFromHeaders';

export default function ReportPage() {
  const branding = getBrandingFromHeaders();
  return (
    <WhiteLabelReport
      agencyLogo={branding.logo}
      agencyColor={branding.color}
      agencyName={branding.name}
    >
      {/* contenido del reporte */}
    </WhiteLabelReport>
  );
}
```

---

> Estos ejemplos permiten que el frontend adapte colores, logos y nombres dinámicamente según el tenant detectado por el middleware, soportando multi-tenancy y white-label.
