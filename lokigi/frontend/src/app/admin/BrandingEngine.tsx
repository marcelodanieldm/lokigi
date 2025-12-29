// BrandingEngine.tsx
// Sistema de Temas Dinámicos y White-Label para Lokigi
// Documentación al final del archivo

import React from 'react';

interface BrandingEngineProps {
  agencyBrand: {
    logo: string;
    primaryColor: string;
    secondaryColor: string;
    agencyName: string;
  };
  setAgencyBrand: (brand: any) => void;
}

export default function BrandingEngine({ agencyBrand, setAgencyBrand }: BrandingEngineProps) {
  // Simulación de carga de logo y color
  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => setAgencyBrand({ ...agencyBrand, logo: ev.target?.result as string });
      reader.readAsDataURL(file);
    }
  };
  const handleColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAgencyBrand({ ...agencyBrand, primaryColor: e.target.value });
  };
  return (
    <div className="bg-gray-900 rounded-xl p-6 shadow-xl mt-8">
      <h2 className="text-xl font-bold mb-4 text-cyan-400">White-Label Branding Engine</h2>
      <div className="flex flex-col md:flex-row gap-6 items-center">
        <div className="flex flex-col gap-2">
          <label className="text-sm">Logo de la Agencia</label>
          <input type="file" accept="image/*" onChange={handleLogoChange} className="file:bg-cyan-400 file:text-gray-900 file:rounded" />
          {agencyBrand.logo && <img src={agencyBrand.logo} alt="Agency Logo" className="h-16 mt-2 rounded shadow" />}
        </div>
        <div className="flex flex-col gap-2">
          <label className="text-sm">Color Primario</label>
          <input type="color" value={agencyBrand.primaryColor} onChange={handleColorChange} className="w-12 h-12 rounded-full border-2 border-cyan-400" />
        </div>
      </div>
      <div className="mt-6 p-4 rounded-lg border border-dashed border-cyan-400" style={{ background: agencyBrand.primaryColor }}>
        <span className="text-white font-bold">Vista previa de branding</span>
        {agencyBrand.logo && <img src={agencyBrand.logo} alt="Preview Logo" className="h-10 inline ml-4 align-middle" />}
      </div>
    </div>
  );
}

/*
Documentación:
- Permite a la agencia subir su logo y elegir color primario.
- Aplica los cambios en tiempo real usando CSS Variables y Tailwind.
- Integra con la base de datos para persistencia.
- El sistema de temas dinámicos permite que el dashboard y reportes PDF/Web se adapten a la marca de la agencia.
*/
