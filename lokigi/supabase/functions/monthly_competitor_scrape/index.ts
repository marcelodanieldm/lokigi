// supabase/functions/monthly_competitor_scrape/index.ts
// Edge Function para Supabase: ejecuta scraping y actualización mensual por suscriptor
// Usa supabase-js v2 y node-fetch
import { serve } from 'std/server';
import { createClient } from '@supabase/supabase-js';

serve(async (req) => {
  // Configuración
  const supabaseUrl = Deno.env.get('SUPABASE_URL');
  const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  const supabase = createClient(supabaseUrl, supabaseKey);

  // Obtener todos los usuarios activos
  const { data: users, error } = await supabase.from('users').select('*').eq('subscription_status', 'active');
  if (error) return new Response('Error al obtener usuarios', { status: 500 });

  // Para cada usuario, dispara scraping y actualización
  for (const user of users) {
    // Aquí deberías llamar a tu backend o función de scraping
    // await fetch(`https://your-backend/scrape?user_id=${user.id}`);
    // Simulación: actualiza un campo de "última actualización"
    await supabase.from('users').update({ last_scrape: new Date().toISOString() }).eq('id', user.id);
  }

  return new Response('Scraping mensual ejecutado', { status: 200 });
});
