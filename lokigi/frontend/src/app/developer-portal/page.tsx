import React from "react";
import Sidebar from "./Sidebar";
import ApiDocs from "./ApiDocs";
import ApiKeyManager from "./ApiKeyManager";
import UsageCharts from "./UsageCharts";

export default function DeveloperPortal() {
  return (
    <div className="flex min-h-screen bg-gradient-to-br from-black via-gray-900 to-green-900 text-white">
      <Sidebar />
      <main className="flex-1 p-6 md:p-12 overflow-y-auto">
        <h1 className="text-3xl font-bold mb-6 neon-green">Lokigi Developer Portal</h1>
        <div className="grid gap-8 md:grid-cols-2">
          <section className="bg-gray-900/80 rounded-xl p-6 shadow-lg">
            <ApiDocs />
          </section>
          <section className="bg-gray-900/80 rounded-xl p-6 shadow-lg">
            <ApiKeyManager />
          </section>
        </div>
        <section className="mt-8 bg-gray-900/80 rounded-xl p-6 shadow-lg">
          <UsageCharts />
        </section>
      </main>
    </div>
  );
}
