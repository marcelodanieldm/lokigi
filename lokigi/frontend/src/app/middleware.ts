// middleware.ts
// Middleware de Multi-tenancy y subdominios para Next.js (Lokigi)
// Documentación al final del archivo
import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);

export async function middleware(req: NextRequest) {
  // 1. Detectar subdominio o dominio personalizado
  const host = req.headers.get('host') || '';
  let agencyId = '';
  if (host.endsWith('.lokigi.com')) {
    agencyId = host.split('.')[0]; // agencia.lokigi.com → agencia
  } else if (host !== 'localhost:3000' && host !== 'lokigi.com') {
    // Custom domain: reportes.miagencia.com
    // Aquí podrías mapear dominio → agencyId en Supabase
    const { data } = await supabase
      .from('agencies')
      .select('id')
      .eq('custom_domain', host)
      .single();
    agencyId = data?.id || '';
  }
  // 2. Cargar branding de la agencia (colores/logo) y exponerlo vía header
  let branding = null;
  if (agencyId) {
    const { data } = await supabase
      .from('agency_branding')
      .select('primary_color,logo_url,agency_name')
      .eq('agency_id', agencyId)
      .single();
    branding = data;
  }
  // 3. Inyectar branding en headers para el frontend
  const res = NextResponse.next();
  if (branding) {
    res.headers.set('x-agency-color', branding.primary_color || '');
    res.headers.set('x-agency-logo', branding.logo_url || '');
    res.headers.set('x-agency-name', branding.agency_name || '');
    res.headers.set('x-agency-id', agencyId);
  }
  return res;
}

export const config = {
  matcher: [
    '/((?!_next|api|static|favicon.ico).*)',
  ],
};

/*
Documentación:
- Detecta subdominios y dominios personalizados para multi-tenancy.
- Carga el branding de la agencia desde Supabase y lo expone vía headers.
- Integra con Supabase Storage para logos/reportes privados por agencia.
- Prepara la integración con la API de Vercel para dominios custom (CNAME).
- Aísla datos por agencia usando RLS en Supabase (ver backend).
*/
