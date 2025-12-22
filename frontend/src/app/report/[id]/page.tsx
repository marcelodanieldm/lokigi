"use client";

import { useParams } from "next/navigation";
import ReportCard from "@/components/ReportCard";
import { useEffect, useState } from "react";

export default function AuditReportPage() {
  const params = useParams();
  const leadId = params.id as string;
  const [auditData, setAuditData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReport();
  }, [leadId]);

  const fetchReport = async () => {
    try {
      const response = await fetch(`/api/v1/audit/${leadId}`);
      if (response.ok) {
        const data = await response.json();
        setAuditData(data);
      }
    } catch (error) {
      console.error("Error fetching report:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900 bg-opacity-50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-neon-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">L</span>
              </div>
              <h1 className="text-2xl font-bold text-white">
                Lokigi <span className="text-neon-500">Report</span>
              </h1>
            </div>
            <button className="text-gray-400 hover:text-white transition">
              Descargar PDF
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="py-12">
        <ReportCard leadId={parseInt(leadId)} auditData={auditData} loading={loading} />
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900 bg-opacity-50 py-8 mt-12">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-gray-500 text-sm">
            © 2025 Lokigi. Todos los derechos reservados.
          </p>
          <p className="text-gray-600 text-xs mt-2">
            Powered by FastAPI + Next.js + Google Gemini AI
          </p>
        </div>
      </footer>
    </div>
  );
}
