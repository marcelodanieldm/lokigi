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
      <div className="bg-gray-900 p-4 rounded-xl mb-6 flex flex-col items-center">
        <div className="mb-2 text-[#39FF14]">Bienvenido, {user.email}</div>
        <button
          className="bg-[#39FF14] text-black font-bold px-4 py-2 rounded-lg hover:scale-105 transition"
          onClick={handleLogout}
        >Logout</button>
      </div>
    );
  }

  return (
    <form onSubmit={handleLogin} className="bg-gray-900 p-4 rounded-xl mb-6 flex flex-col items-center">
      <input
        className="mb-2 px-3 py-2 rounded bg-gray-800 text-white border border-[#39FF14] font-mono"
        type="email"
        placeholder="Email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        required
      />
      <input
        className="mb-2 px-3 py-2 rounded bg-gray-800 text-white border border-[#39FF14] font-mono"
        type="password"
        placeholder="Password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
      />
      <button
        className="bg-[#39FF14] text-black font-bold px-4 py-2 rounded-lg hover:scale-105 transition"
        type="submit"
      >Login</button>
      {error && <div className="text-red-400 mt-2">{error}</div>}
    </form>
  );
}
