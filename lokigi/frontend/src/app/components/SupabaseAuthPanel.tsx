"use client";
import { useState } from "react";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
const supabase = createClient(supabaseUrl, supabaseAnonKey);

export default function SupabaseAuthPanel() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [user, setUser] = useState<any>(null);
  const [error, setError] = useState("");

  async function handleLogin(e: any) {
    e.preventDefault();
    setError("");
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) setError(error.message);
    else setUser(data.user);
  }

  async function handleLogout() {
    await supabase.auth.signOut();
    setUser(null);
  }

  // Check session on mount
  React.useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user));
  }, []);

  if (user) {
    return (
      <div className="card bg-white text-corporate-dark border border-corporate-gray p-6 mb-6">
        <h2 className="text-2xl font-bold text-corporate-blue mb-4">Acceso Seguro</h2>
        <div className="mb-2 text-gray-700">Bienvenido, {user.email}</div>
        <div className="flex gap-4 mt-4">
          <button
            className="bg-[#39FF14] text-black font-bold px-4 py-2 rounded-lg hover:scale-105 transition"
            onClick={handleLogout}
          >Cerrar sesión</button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleLogin} className="card bg-white text-corporate-dark border border-corporate-gray p-6 mb-6">
      <h2 className="text-2xl font-bold text-corporate-blue mb-4">Acceso Seguro</h2>
      <input
        className="mb-2 px-3 py-2 rounded bg-gray-100 text-gray-900 border border-[#39FF14] font-mono"
        type="email"
        placeholder="Email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        required
      />
      <input
        className="mb-2 px-3 py-2 rounded bg-gray-100 text-gray-900 border border-[#39FF14] font-mono"
        type="password"
        placeholder="Password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
      />
      <button
        className="bg-[#39FF14] text-black font-bold px-4 py-2 rounded-lg hover:scale-105 transition"
        type="submit"
      >Iniciar sesión</button>
      {error && <div className="text-red-400 mt-2">{error}</div>}
    </form>
  );
}
