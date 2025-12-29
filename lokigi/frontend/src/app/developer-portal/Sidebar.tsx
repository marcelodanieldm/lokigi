import React from "react";
import Link from "next/link";

export default function Sidebar() {
  return (
    <aside className="w-64 hidden md:flex flex-col bg-gray-950 border-r border-green-500/30 min-h-screen p-6">
      <div className="text-2xl font-bold neon-green mb-10">Lokigi API</div>
      <nav className="flex flex-col gap-4">
        <Link href="#api-docs" className="hover:text-green-400">Documentación API</Link>
        <Link href="#api-keys" className="hover:text-green-400">API Keys</Link>
        <Link href="#usage" className="hover:text-green-400">Consumo</Link>
      </nav>
      <div className="mt-auto text-xs text-gray-500">Modo oscuro · Verde neón</div>
    </aside>
  );
}
