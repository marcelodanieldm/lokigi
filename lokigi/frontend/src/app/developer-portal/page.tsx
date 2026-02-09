import React from "react";
import Sidebar from "./Sidebar";
import ApiDocs from "./ApiDocs";
import ApiKeyManager from "./ApiKeyManager";
import UsageCharts from "./UsageCharts";
import "../globals.css";

export default function DeveloperPortal() {
  return (
    <div className="flex min-h-screen bg-corporate-gray text-corporate-dark">
      <Sidebar />
      <main className="flex-1 p-6 md:p-12 overflow-y-auto">
        <h1 className="text-3xl font-bold mb-6">Lokigi Developer Portal</h1>
        <div className="grid gap-8 md:grid-cols-2">
          <section className="card">
            <ApiDocs />
          </section>
          <section className="card">
            <ApiKeyManager />
          </section>
        </div>
        <section className="mt-8 card">
          <UsageCharts />
        </section>
      </main>
    </div>
  );
}
