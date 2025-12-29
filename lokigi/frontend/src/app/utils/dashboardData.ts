import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export async function getVisibilityPoints(userId: string) {
  // Consulta puntos de visibilidad del usuario
  const { data, error } = await supabase
    .from('visibility_points')
    .select('*')
    .eq('user_id', userId);
  if (error) return [];
  return data;
}

export async function getAlerts(userId: string) {
  // Consulta alertas recientes del usuario
  const { data, error } = await supabase
    .from('alerts')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(10);
  if (error) return [];
  return data;
}

export async function getROI(userId: string) {
  // Consulta ROI tracker del usuario
  const { data, error } = await supabase
    .from('roi_tracker')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(1);
  if (error || !data?.length) return { amount: 0, currency: 'USD' };
  return { amount: data[0].amount, currency: data[0].currency };
}
