// MainNav.tsx
// Navegación principal para Lokigi (Admin, Dashboard, Partner, Impact Report, etc)
// Documentación al final del archivo

import React from 'react';
import Link from 'next/link';

const navItems = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Premium', href: '/dashboard/premium' },
  { label: 'Partner', href: '/partner' },
  { label: 'Impact Report', href: '/impact-report' },
  { label: 'Admin: Partnerships', href: '/admin/partnerships' },
];

export default function MainNav() {
  return (
    <nav className="w-full bg-gray-900 border-b border-cyan-700 py-3 px-4 flex gap-4 items-center shadow">
      <span className="font-bold text-cyan-400 text-xl mr-6">Lokigi</span>
      {navItems.map((item) => (
        <Link key={item.href} href={item.href} className="text-cyan-200 hover:text-white px-3 py-1 rounded transition">
          {item.label}
        </Link>
      ))}
    </nav>
  );
}

/*
Documentación:
- Incluye enlaces a las principales secciones: Dashboard, Premium, Partner, Impact Report, Admin Partnerships.
- Agrega este componente en el layout principal o en cada página para navegación global.
*/
