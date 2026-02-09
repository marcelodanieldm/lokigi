import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabase = createClient(supabaseUrl, supabaseAnonKey);

export function useSuperuser() {
  const [isSuperuser, setIsSuperuser] = useState(false);
  useEffect(() => {
    async function checkRole() {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return setIsSuperuser(false);
      // Asume que el rol está en user.user_metadata.role o en un claim personalizada
      const role = user.user_metadata?.role || user.role;
      setIsSuperuser(role === "SUPERUSER" || role === "ADMIN");
    }
    checkRole();
  }, []);
  return isSuperuser;
}

// Todos los mensajes y retornos deben ser claros, profesionales y alineados al nuevo tono empresarial.
