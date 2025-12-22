'use client';

import { useState, useEffect } from 'react';
import { use } from 'react';
import { useRouter } from 'next/navigation';
import AuthGuard from '@/components/AuthGuard';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import AICopywriterButton from '@/components/dashboard/AICopywriterButton';
import GeotagButton from '@/components/dashboard/GeotagButton';
import CompletionChecklist from '@/components/dashboard/CompletionChecklist';
import {
  ArrowLeft,
  User,
  Mail,
  Phone,
  Building2,
  Calendar,
  DollarSign,
  ExternalLink,
  Link as LinkIcon,
  Save,
  Send,
  Loader2,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
} from 'lucide-react';

interface OrderDetail {
  id: number;
  lead_id: number;
  client_name: string;
  client_email: string;
  client_phone: string;
  client_whatsapp: string | null;
  business_name: string;
  amount: number;
  status: string;
  created_at: string;
  completed_at: string | null;
  notes: string | null;
  score_inicial: number | null;
  audit_data: any;
}

export default function WorkOrderDetailPage({ params }: { params: Promise<{ orderId: string }> }) {
  const resolvedParams = use(params);
  const orderId = resolvedParams.orderId;
  const router = useRouter();
  
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [checklistComplete, setChecklistComplete] = useState(false);
  
  // Manual fields
  const [competitorLinks, setCompetitorLinks] = useState('');
  const [internalNotes, setInternalNotes] = useState('');
  const [reportUrl, setReportUrl] = useState('');

  useEffect(() => {
    fetchOrderDetail();
  }, [orderId]);

  const fetchOrderDetail = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/orders/${orderId}`);
      const data = await response.json();
      setOrder(data);
      setInternalNotes(data.notes || '');
      setLoading(false);
    } catch (error) {
      console.error('Error fetching order:', error);
      setLoading(false);
    }
  };

  const handleSaveNotes = async () => {
    setSaving(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/orders/${orderId}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: internalNotes }),
      });
      alert('Notas guardadas correctamente');
    } catch (error) {
      console.error('Error saving notes:', error);
      alert('Error al guardar notas');
    } finally {
      setSaving(false);
    }
  };

  const handleCompleteOrder = async () => {
    if (!checklistComplete) {
      alert('⚠️ Debes completar todos los items del checklist antes de finalizar');
      return;
    }

    if (!reportUrl.trim()) {
      alert('Por favor ingresa la URL del reporte final');
      return;
    }

    if (!confirm('¿Marcar este pedido como completado y enviarlo al cliente?')) {
      return;
    }

    setCompleting(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/orders/${orderId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notes: internalNotes,
          report_url: reportUrl,
        }),
      });
      alert('✅ Pedido completado. Cliente notificado por email.');
      router.push('/dashboard/work');
    } catch (error) {
      console.error('Error completing order:', error);
      alert('Error al completar pedido');
    } finally {
      setCompleting(false);
    }
  };
    } finally {
      setCompleting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('es', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(dateString));
  };

  if (loading) {
    return (
      <AuthGuard requiredRole="worker">
        <div className="flex min-h-screen bg-dark-900 items-center justify-center">
          <Loader2 className="w-12 h-12 text-neon-500 animate-spin" />
        </div>
      </AuthGuard>
    );
  }

  if (!order) {
    return (
      <AuthGuard requiredRole="worker">
        <div className="flex min-h-screen bg-dark-900 items-center justify-center">
          <div className="card text-center max-w-md">
            <AlertCircle className="w-16 h-16 text-danger-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Pedido no encontrado</h2>
            <button onClick={() => router.push('/dashboard/work')} className="btn-primary mt-4">
              Volver al listado
            </button>
          </div>
        </div>
      </AuthGuard>
    );
  }

  return (
    <AuthGuard requiredRole="worker">
      <div className="flex min-h-screen bg-dark-900">
        <DashboardSidebar />
        
        <main className="flex-1 p-8 ml-64">
          {/* Header */}
          <div className="mb-8">
            <button
              onClick={() => router.push('/dashboard/work')}
              className="btn-secondary mb-4 flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Volver al listado
            </button>
            
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                  <span className="text-neon-500 font-mono">#{order.id}</span>
                  {order.business_name}
                </h1>
                <p className="text-gray-400">
                  Pedido recibido el {formatDate(order.created_at)}
                </p>
              </div>
              
              {order.score_inicial && (
                <div className="card">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-neon-500" />
                    <div>
                      <p className="text-xs text-gray-400">Score Inicial</p>
                      <p className="text-2xl font-bold text-neon-500">{order.score_inicial}/100</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Client Info */}
            <div className="space-y-6">
              {/* Client Card */}
              <div className="card">
                <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <User className="w-5 h-5 text-neon-500" />
                  Datos del Cliente
                </h2>
                
                <div className="space-y-3 text-sm">
                  <div className="flex items-start gap-2 text-gray-300">
                    <User className="w-4 h-4 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-xs text-gray-500">Nombre</p>
                      <p className="font-medium">{order.client_name}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-2 text-gray-300">
                    <Mail className="w-4 h-4 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-xs text-gray-500">Email</p>
                      <p className="font-medium">{order.client_email}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-2 text-gray-300">
                    <Phone className="w-4 h-4 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-xs text-gray-500">Teléfono</p>
                      <p className="font-medium">{order.client_phone}</p>
                    </div>
                  </div>
                  
                  {order.client_whatsapp && (
                    <div className="flex items-start gap-2 text-gray-300">
                      <Phone className="w-4 h-4 text-gray-500 mt-0.5" />
                      <div>
                        <p className="text-xs text-gray-500">WhatsApp</p>
                        <p className="font-medium">{order.client_whatsapp}</p>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-start gap-2 text-gray-300">
                    <Building2 className="w-4 h-4 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-xs text-gray-500">Negocio</p>
                      <p className="font-medium">{order.business_name}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-2 text-gray-300">
                    <DollarSign className="w-4 h-4 text-gray-500 mt-0.5" />
                    <div>
                      <p className="text-xs text-gray-500">Monto pagado</p>
                      <p className="font-bold text-neon-500">${order.amount} USD</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="card">
                <h3 className="text-sm font-bold text-white mb-3">Acciones Rápidas</h3>
                <div className="space-y-2">
                  <a
                    href={`mailto:${order.client_email}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary w-full justify-center"
                  >
                    <Mail className="w-4 h-4" />
                    Enviar Email
                  </a>
                  {order.client_whatsapp && (
                    <a
                      href={`https://wa.me/${order.client_whatsapp.replace(/\D/g, '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn-secondary w-full justify-center"
                    >
                      <Phone className="w-4 h-4" />
                      WhatsApp
                    </a>
                  )}
                  <a
                    href={`https://www.google.com/maps/search/${encodeURIComponent(order.business_name)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary w-full justify-center"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Ver en Google Maps
                  </a>
                </div>
              </div>

              {/* AI Tools */}
              <div className="card">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  🤖 Herramientas AI
                </h3>
                <div className="space-y-2">
                  <AICopywriterButton
                    businessName={order.business_name}
                    businessCategory={order.audit_data?.category}
                    orderId={order.id}
                  />
                  <GeotagButton
                    businessName={order.business_name}
                    businessAddress={order.audit_data?.address}
                    orderId={order.id}
                  />
                </div>
              </div>
            </div>

            {/* Right Column - Work Area */}
            <div className="lg:col-span-2 space-y-6">
              {/* Competitor Links */}
              <div className="card">
                <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <LinkIcon className="w-5 h-5 text-neon-500" />
                  Links de Competencia (Manual)
                </h2>
                <p className="text-sm text-gray-400 mb-4">
                  📋 Copia y pega los links de Google Maps de los 3-5 competidores principales (uno por línea)
                </p>
                
                <textarea
                  value={competitorLinks}
                  onChange={(e) => setCompetitorLinks(e.target.value)}
                  placeholder={`https://maps.google.com/...
https://maps.google.com/...
https://maps.google.com/...`}
                  className="input-cyber w-full h-32 font-mono text-sm"
                />
              </div>

              {/* Internal Notes */}
              <div className="card">
                <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Save className="w-5 h-5 text-neon-500" />
                  Notas Internas
                </h2>
                <p className="text-sm text-gray-400 mb-4">
                  📝 Anotaciones para el equipo (no se envían al cliente)
                </p>
                
                <textarea
                  value={internalNotes}
                  onChange={(e) => setInternalNotes(e.target.value)}
                  placeholder="Escribe tus observaciones aquí..."
                  className="input-cyber w-full h-32"
                />
                
                <button
                  onClick={handleSaveNotes}
                  disabled={saving}
                  className="btn-secondary mt-4 w-full"
                >
                  {saving ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Guardando...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      Guardar Notas
                    </>
                  )}
                </button>
              </div>

              {/* Checklist de Finalización */}
              <CompletionChecklist
                orderId={order.id}
                onChecklistComplete={setChecklistComplete}
              />

              {/* Final Report URL */}
              <div className="card border-2 border-neon-500/30">
                <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Send className="w-5 h-5 text-neon-500" />
                  Reporte Final
                </h2>
                <p className="text-sm text-gray-400 mb-4">
                  🚀 Cuando termines el análisis, pega aquí la URL del reporte (Google Docs, PDF, etc.)
                </p>
                
                <input
                  type="url"
                  value={reportUrl}
                  onChange={(e) => setReportUrl(e.target.value)}
                  placeholder="https://docs.google.com/document/..."
                  className="input-cyber w-full mb-4"
                />
                
                <button
                  onClick={handleCompleteOrder}
                  disabled={completing || !reportUrl.trim() || !checklistComplete}
                  className={`btn-primary w-full ${
                    !checklistComplete ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {completing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Completando...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-5 h-5" />
                      Marcar como Completado y Enviar
                    </>
                  )}
                </button>
                
                <p className="text-xs text-gray-500 mt-3 text-center">
                  {checklistComplete ? (
                    <>⚠️ El cliente recibirá un email con el link al reporte</>
                  ) : (
                    <span className="text-warning-500">
                      ⚠️ Completa el checklist antes de finalizar
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
