import React from "react";
import Link from "next/link";
import { HomeIcon, KeyIcon, ChartBarIcon } from "@heroicons/react/24/outline";

export default function Sidebar() {
  return (
    <aside className="w-64 hidden md:flex flex-col bg-white border-r border-gray-200 min-h-screen p-6">
      <div className="text-2xl font-bold text-corporate-blue mb-10">Lokigi API</div>
      <nav className="flex flex-col gap-4">
        <Link href="#api-docs" className="flex items-center gap-2 text-corporate-dark hover:text-corporate-blue">
          <HomeIcon className="w-5 h-5" />
          Documentación API
        </Link>
        <Link href="#api-keys" className="flex items-center gap-2 text-corporate-dark hover:text-corporate-blue">
          <KeyIcon className="w-5 h-5" />
          API Keys
        </Link>
        <Link href="#usage" className="flex items-center gap-2 text-corporate-dark hover:text-corporate-blue">
          <ChartBarIcon className="w-5 h-5" />
          Consumo
        </Link>
      </nav>
      <div className="mt-auto text-xs text-gray-400">Lokigi · Portal Empresarial</div>
    </aside>
  );
}
