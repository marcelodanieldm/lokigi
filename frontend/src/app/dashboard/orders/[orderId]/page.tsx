'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import {
  ArrowLeft,
  User,
  Mail,
  Phone,
  Building2,
  Calendar,
  DollarSign,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingDown,
  Send,
  Check,
  X,
  ExternalLink,
  MessageCircle
} from 'lucide-react';

interface ChecklistItem {
  id: string;
  text: string;
  completed: boolean;
}

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
  fallos_criticos: any;
  audit_data: any;
  checklist: ChecklistItem[];
}

interface DashboardStats {
  total_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  completed_orders: number;
  total_revenue: number;
}

export default function OrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.orderId as string;

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [completionNotes, setCompletionNotes] = useState('');
  const [isCompleting, setIsCompleting] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchOrderDetail();
  }, [orderId]);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/dashboard/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchOrderDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/orders/${orderId}`);
      if (!response.ok) throw new Error('Order not found');
      const data = await response.json();
      setOrder(data);
      setChecklist(data.checklist || []);
      setCompletionNotes(data.notes || '');
    } catch (error) {
      console.error('Error fetching order:', error);
      alert('Error al cargar la orden');
    } finally {
      setLoading(false);
    }
  };

  const handleChecklistToggle = (itemId: string) => {
    setChecklist(prev =>
      prev.map(item =>
        item.id === itemId ? { ...item, completed: !item.completed } : item
      )
    );
  };

  const handleUpdateStatus = async (newStatus: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });

      if (!response.ok) throw new Error('Failed to update status');

      await fetchOrderDetail();
      alert('Estado actualizado correctamente');
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Error al actualizar el estado');
    }
  };

  const handleCompleteOrder = async () => {
    if (!confirm('¿Estás seguro de marcar esta orden como completada? Se enviará un email al cliente.')) {
      return;
    }

    setIsCompleting(true);
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/orders/${orderId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: completionNotes })
      });

      if (!response.ok) throw new Error('Failed to complete order');

      const data = await response.json();
      alert('✅ Orden completada y email enviado al cliente');
      await fetchOrderDetail();
    } catch (error) {
      console.error('Error completing order:', error);
      alert('Error al completar la orden');
    } finally {
      setIsCompleting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const configs = {
      PENDING: {
        bg: 'bg-yellow-100',
        text: 'text-yellow-700',
        icon: Clock,
        label: 'Pendiente'
      },
      IN_PROGRESS: {
        bg: 'bg-blue-100',
        text: 'text-blue-700',
        icon: Clock,
        label: 'En Proceso'
      },
      COMPLETED: {
        bg: 'bg-green-100',
        text: 'text-green-700',
        icon: CheckCircle2,
        label: 'Completado'
      }
    };

    const config = configs[status as keyof typeof configs] || configs.PENDING;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold ${config.bg} ${config.text}`}>
        <Icon className="w-5 h-5" />
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    return new Intl.DateTimeFormat('es-ES', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(dateString));
  };

  const checklistProgress = checklist.length > 0
    ? (checklist.filter(item => item.completed).length / checklist.length) * 100
    : 0;

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar stats={stats || undefined} />
        <main className="flex-1 p-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-600">Cargando orden...</p>
          </div>
        </main>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar stats={stats || undefined} />
        <main className="flex-1 p-8">
          <div className="text-center py-12">
            <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Orden no encontrada</h2>
            <button
              onClick={() => router.back()}
              className="mt-4 px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700"
            >
              Volver
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <DashboardSidebar stats={stats || undefined} />

      <main className="flex-1 p-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.back()}
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5" />
            Volver a la lista
          </button>

          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-4xl font-black text-gray-900 mb-2">
                Orden #{order.id}
              </h1>
              <p className="text-gray-600">{order.business_name}</p>
            </div>
            {getStatusBadge(order.status)}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left Column - Cliente Info */}
          <div className="lg:col-span-1 space-y-6">
            {/* Client Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Información del Cliente</h2>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <User className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Nombre</div>
                    <div className="font-semibold text-gray-900">{order.client_name}</div>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Mail className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Email</div>
                    <a
                      href={`mailto:${order.client_email}`}
                      className="font-semibold text-blue-600 hover:underline"
                    >
                      {order.client_email}
                    </a>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Phone className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Teléfono</div>
                    <a
                      href={`tel:${order.client_phone}`}
                      className="font-semibold text-blue-600 hover:underline"
                    >
                      {order.client_phone}
                    </a>
                  </div>
                </div>

                {order.client_whatsapp && (
                  <div className="flex items-start gap-3">
                    <MessageCircle className="w-5 h-5 text-green-500 mt-0.5" />
                    <div>
                      <div className="text-xs text-gray-500 mb-1">WhatsApp</div>
                      <a
                        href={`https://wa.me/${order.client_whatsapp.replace(/[^0-9]/g, '')}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-semibold text-green-600 hover:underline inline-flex items-center gap-1"
                      >
                        {order.client_whatsapp}
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </div>
                )}

                <div className="flex items-start gap-3">
                  <Building2 className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Negocio</div>
                    <div className="font-semibold text-gray-900">{order.business_name}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Order Info Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Datos de la Orden</h2>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <DollarSign className="w-5 h-5 text-green-500 mt-0.5" />
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Monto</div>
                    <div className="text-2xl font-black text-green-600">${order.amount}</div>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Fecha de Pago</div>
                    <div className="font-semibold text-gray-900">{formatDate(order.created_at)}</div>
                  </div>
                </div>

                {order.completed_at && (
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5" />
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Fecha de Completado</div>
                      <div className="font-semibold text-gray-900">{formatDate(order.completed_at)}</div>
                    </div>
                  </div>
                )}

                {order.score_inicial && (
                  <div className="flex items-start gap-3">
                    <TrendingDown className="w-5 h-5 text-red-500 mt-0.5" />
                    <div>
                      <div className="text-xs text-gray-500 mb-1">Score Inicial</div>
                      <div className="text-2xl font-black text-red-600">{order.score_inicial}/100</div>
                      <div className="text-xs text-red-600 font-semibold mt-1">CRÍTICO</div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Status Actions */}
            {order.status !== 'COMPLETED' && (
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl border-2 border-blue-200 p-6">
                <h3 className="font-bold text-gray-900 mb-4">Actualizar Estado</h3>
                <div className="space-y-2">
                  {order.status === 'PENDING' && (
                    <button
                      onClick={() => handleUpdateStatus('IN_PROGRESS')}
                      className="w-full px-4 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors"
                    >
                      Marcar En Proceso
                    </button>
                  )}
                  {order.status === 'IN_PROGRESS' && (
                    <button
                      onClick={() => handleUpdateStatus('PENDING')}
                      className="w-full px-4 py-3 bg-yellow-600 text-white font-semibold rounded-xl hover:bg-yellow-700 transition-colors"
                    >
                      Volver a Pendiente
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Checklist & Actions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Progress Bar */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-bold text-gray-900">Progreso General</h2>
                <span className="text-2xl font-black text-blue-600">
                  {Math.round(checklistProgress)}%
                </span>
              </div>
              <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                  style={{ width: `${checklistProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-2">
                {checklist.filter(i => i.completed).length} de {checklist.length} tareas completadas
              </p>
            </div>

            {/* Checklist */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Checklist de Optimización</h2>

              <div className="space-y-3">
                {checklist.map((item) => (
                  <div
                    key={item.id}
                    className={`
                      flex items-start gap-4 p-4 rounded-xl border-2 transition-all cursor-pointer
                      ${item.completed
                        ? 'bg-green-50 border-green-200 opacity-75'
                        : 'bg-white border-gray-200 hover:border-blue-300'
                      }
                    `}
                    onClick={() => handleChecklistToggle(item.id)}
                  >
                    <div className={`
                      flex-shrink-0 w-6 h-6 rounded-lg border-2 flex items-center justify-center
                      ${item.completed
                        ? 'bg-green-500 border-green-500'
                        : 'border-gray-300'
                      }
                    `}>
                      {item.completed && <Check className="w-4 h-4 text-white" />}
                    </div>
                    <div className="flex-1">
                      <p className={`
                        font-medium
                        ${item.completed ? 'text-gray-500 line-through' : 'text-gray-900'}
                      `}>
                        {item.text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Completion Section */}
            {order.status !== 'COMPLETED' && (
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl border-2 border-green-300 p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <CheckCircle2 className="w-6 h-6 text-green-600" />
                  Completar Orden
                </h2>

                <p className="text-gray-700 mb-4">
                  Al marcar como completada, se enviará automáticamente un email al cliente
                  notificando que su negocio está optimizado.
                </p>

                <div className="mb-4">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Notas de Completado (opcional)
                  </label>
                  <textarea
                    value={completionNotes}
                    onChange={(e) => setCompletionNotes(e.target.value)}
                    placeholder="Agrega notas internas sobre el trabajo realizado..."
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-green-500 focus:outline-none resize-none"
                    rows={4}
                  />
                </div>

                <button
                  onClick={handleCompleteOrder}
                  disabled={isCompleting || checklistProgress < 100}
                  className={`
                    w-full px-6 py-4 rounded-xl font-bold text-white text-lg
                    flex items-center justify-center gap-2 transition-all
                    ${checklistProgress === 100
                      ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 shadow-lg hover:shadow-xl'
                      : 'bg-gray-400 cursor-not-allowed'
                    }
                  `}
                >
                  {isCompleting ? (
                    <>
                      <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
                      Completando...
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      Marcar como Completado y Enviar Email
                    </>
                  )}
                </button>

                {checklistProgress < 100 && (
                  <p className="text-sm text-amber-700 font-semibold mt-3 text-center">
                    ⚠️ Completa todas las tareas del checklist antes de finalizar
                  </p>
                )}
              </div>
            )}

            {/* Already Completed */}
            {order.status === 'COMPLETED' && (
              <div className="bg-gradient-to-br from-green-100 to-emerald-100 rounded-2xl border-2 border-green-400 p-8 text-center">
                <CheckCircle2 className="w-16 h-16 text-green-600 mx-auto mb-4" />
                <h3 className="text-2xl font-black text-green-900 mb-2">
                  Orden Completada ✅
                </h3>
                <p className="text-green-700">
                  Esta orden fue completada el {order.completed_at && formatDate(order.completed_at)}
                </p>
                {order.notes && (
                  <div className="mt-4 p-4 bg-white/50 rounded-xl">
                    <div className="text-sm font-semibold text-gray-700 mb-1">Notas:</div>
                    <p className="text-gray-600">{order.notes}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
