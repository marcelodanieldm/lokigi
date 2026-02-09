// frontend/src/utils/getSubscriptionStatus.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

export async function getSubscriptionStatus(userId: string): Promise<'active'|'past_due'|'canceled'|'none'> {
  if (!userId) return 'none';
  const { data, error } = await supabase.from('users').select('subscription_status').eq('id', userId).single();
  if (error || !data) return 'none';
  return (data.subscription_status as 'active'|'past_due'|'canceled') || 'none';
}
