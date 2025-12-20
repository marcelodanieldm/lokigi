'use client';

import { useState, useEffect } from 'react';
import AuthGuard from '@/components/AuthGuard';
import LogoutButton from '@/components/LogoutButton';
import { 
  Clock, 
  CheckCircle2, 
  Circle,
  MapPin,
  Phone,
  ExternalLink,
  AlertCircle,
  ArrowRight,
  Save,
  Send,
  Loader2
} from 'lucide-react';

// ==========================================
// Types
// ==========================================

interface Task {
  id: number;
  order_id: number;
  description: string;
  category: 'SEO' | 'CONTENIDO' | 'VERIFICACION';
  is_completed: boolean;
  priority: number;
  order_index: number;
  notes: string | null;
  created_at: string;
  completed_at: string | null;
}

interface Order {
  id: number;
  lead_id: number;
  client_name: string;
  client_email: string;
  client_phone: string;
  client_whatsapp: string | null;
  business_name: string;
  amount: number;
  status: string;
  score_inicial: number | null;
  created_at: string;
  completed_at: string | null;
  notes: string | null;
  audit_data: any;
}

interface TaskListResponse {
  tasks: Task[];
  completion_percentage: number;
  pending_tasks: number;
}

// ==========================================
// Main Component
// ==========================================

export default function WorkDashboard() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskStats, setTaskStats] = useState({ completion_percentage: 0, pending_tasks: 0 });
  const [internalNotes, setInternalNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [savingNotes, setSavingNotes] = useState(false);
  const [completingOrder, setCompletingOrder] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, []);

  useEffect(() => {
    if (selectedOrder) {
      fetchTasks(selectedOrder.id);
      setInternalNotes(selectedOrder.notes || '');
    }
  }, [selectedOrder]);

  // ==========================================
  // API Calls
  // ==========================================

  const fetchOrders = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/dashboard/orders');
      const data = await response.json();
      // Filter only paid orders (completed status means paid and ready to work)
      const paidOrders = data.filter((order: Order) => order.status === 'completed');
      setOrders(paidOrders);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching orders:', error);
      setLoading(false);
    }
  };

  const fetchTasks = async (orderId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/orders/${orderId}/tasks`);
      const data: TaskListResponse = await response.json();
      setTasks(data.tasks);
      setTaskStats({
        completion_percentage: data.completion_percentage,
        pending_tasks: data.pending_tasks
      });
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const toggleTask = async (taskId: number, currentStatus: boolean) => {
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          is_completed: !currentStatus,
          notes: !currentStatus ? 'Completado desde dashboard' : ''
        })
      });

      if (response.ok) {
        // Refresh tasks
        if (selectedOrder) {
          await fetchTasks(selectedOrder.id);
        }
      }
    } catch (error) {
      console.error('Error toggling task:', error);
    }
  };

  const completeOrder = async () => {
    if (!selectedOrder) return;

    setCompletingOrder(true);
    try {
      const response = await fetch(`http://localhost:8000/api/dashboard/orders/${selectedOrder.id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notes: internalNotes
        })
      });

      if (response.ok) {
        alert('✅ Orden completada! Email enviado al cliente.');
        // Refresh orders and close panel
        await fetchOrders();
        setSelectedOrder(null);
      } else {
        alert('❌ Error al completar la orden');
      }
    } catch (error) {
      console.error('Error completing order:', error);
      alert('❌ Error al completar la orden');
    } finally {
      setCompletingOrder(false);
    }
  };

  // ==========================================
  // Helper Functions
  // ==========================================

  const getTimeElapsed = (createdAt: string) => {
    const now = new Date();
    const created = new Date(createdAt);
    const diffMs = now.getTime() - created.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d`;
    if (diffHours > 0) return `${diffHours}h`;
    return '<1h';
  };

  const getUrgencyColor = (createdAt: string) => {
    const now = new Date();
    const created = new Date(createdAt);
    const diffHours = (now.getTime() - created.getTime()) / (1000 * 60 * 60);

    if (diffHours > 72) return 'text-red-500 bg-red-500/10 border-red-500/20';
    if (diffHours > 48) return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
    if (diffHours > 24) return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
    return 'text-green-500 bg-green-500/10 border-green-500/20';
  };

  const getCategoryBadgeColor = (category: string) => {
    switch (category) {
      case 'SEO':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'CONTENIDO':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'VERIFICACION':
        return 'bg-green-500/10 text-green-400 border-green-500/20';
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
    }
  };

  // ==========================================
  // Render: Main Layout
  // ==========================================

  return (
    <AuthGuard requiredRole="any">
      <WorkDashboardContent
        orders={orders}
        selectedOrder={selectedOrder}
        setSelectedOrder={setSelectedOrder}
        tasks={tasks}
        taskStats={taskStats}
        internalNotes={internalNotes}
        setInternalNotes={setInternalNotes}
        loading={loading}
        savingNotes={savingNotes}
        completingOrder={completingOrder}
        toggleTask={toggleTask}
        completeOrder={completeOrder}
        getTimeElapsed={getTimeElapsed}
        getUrgencyColor={getUrgencyColor}
        getCategoryBadgeColor={getCategoryBadgeColor}
      />
    </AuthGuard>
  );
}

// ==========================================
// Main Content Component
// ==========================================

function WorkDashboardContent({
  orders,
  selectedOrder,
  setSelectedOrder,
  tasks,
  taskStats,
  internalNotes,
  setInternalNotes,
  loading,
  savingNotes,
  completingOrder,
  toggleTask,
  completeOrder,
  getTimeElapsed,
  getUrgencyColor,
  getCategoryBadgeColor
}: any) {
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-gray-100">
      {/* Header */}
      <div className="border-b border-gray-800 bg-black/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-[1800px] mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">Work Queue</h1>
              <p className="text-sm text-gray-400 mt-1">
                {orders.length} órdenes activas · {orders.reduce((acc: number, o: any) => acc + (taskStats.pending_tasks || 0), 0)} tareas pendientes
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-gray-400">Sistema activo</span>
              </div>
              <LogoutButton />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-[1800px] mx-auto p-6">
        <div className="flex gap-6">
          {/* Left Panel: Work Queue Table */}
          <div className={`transition-all duration-300 ${selectedOrder ? 'w-1/2' : 'w-full'}`}>
            <div className="bg-[#111111] border border-gray-800 rounded-lg overflow-hidden">
              {/* Table Header */}
              <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-gray-800 bg-black/30 text-xs font-medium text-gray-400 uppercase tracking-wider">
                <div className="col-span-4">Cliente / Negocio</div>
                <div className="col-span-2 text-center">Urgencia</div>
                <div className="col-span-4">Progreso</div>
                <div className="col-span-2 text-right">Acción</div>
              </div>

              {/* Table Body */}
              <div className="divide-y divide-gray-800">
                {orders.length === 0 ? (
                  <div className="px-6 py-12 text-center">
                    <CheckCircle2 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-400">No hay órdenes pendientes</p>
                    <p className="text-sm text-gray-500 mt-1">Todas las tareas están completadas 🎉</p>
                  </div>
                ) : (
                  orders.map((order) => (
                    <div
                      key={order.id}
                      className={`grid grid-cols-12 gap-4 px-6 py-4 hover:bg-gray-900/50 cursor-pointer transition-all ${
                        selectedOrder?.id === order.id ? 'bg-gray-900/80 border-l-2 border-blue-500' : ''
                      }`}
                      onClick={() => setSelectedOrder(order)}
                    >
                      {/* Client Info */}
                      <div className="col-span-4">
                        <div className="font-medium text-white">{order.client_name}</div>
                        <div className="text-sm text-gray-400 truncate">{order.business_name}</div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-500">Order #{order.id}</span>
                          {order.score_inicial && (
                            <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">
                              Score: {order.score_inicial}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Urgency */}
                      <div className="col-span-2 flex items-center justify-center">
                        <div className={`px-3 py-1 rounded-full text-xs font-medium border ${getUrgencyColor(order.created_at)}`}>
                          <Clock className="w-3 h-3 inline mr-1" />
                          {getTimeElapsed(order.created_at)}
                        </div>
                      </div>

                      {/* Progress */}
                      <div className="col-span-4 flex items-center">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-400">Tareas completadas</span>
                            <span className="text-xs font-medium text-white">
                              {selectedOrder?.id === order.id ? taskStats.completion_percentage.toFixed(0) : '0'}%
                            </span>
                          </div>
                          <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                              style={{ width: `${selectedOrder?.id === order.id ? taskStats.completion_percentage : 0}%` }}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Action */}
                      <div className="col-span-2 flex items-center justify-end">
                        <button className="text-blue-400 hover:text-blue-300 transition-colors">
                          <ArrowRight className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Right Panel: Order Detail */}
          {selectedOrder && (
            <div className="w-1/2 fixed right-6 top-[120px] bottom-6 overflow-hidden">
              <div className="h-full bg-[#111111] border border-gray-800 rounded-lg flex flex-col">
                {/* Panel Header */}
                <div className="px-6 py-4 border-b border-gray-800 bg-black/30">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h2 className="text-xl font-bold text-white">{selectedOrder.business_name}</h2>
                      <p className="text-sm text-gray-400 mt-1">{selectedOrder.client_name}</p>
                    </div>
                    <button
                      onClick={() => setSelectedOrder(null)}
                      className="text-gray-400 hover:text-white transition-colors"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto">
                  {/* Business Info Section */}
                  <div className="p-6 border-b border-gray-800">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Información del Negocio</h3>
                    <div className="space-y-3">
                      <a
                        href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selectedOrder.business_name)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-3 p-3 bg-blue-500/5 border border-blue-500/20 rounded-lg hover:bg-blue-500/10 transition-colors group"
                      >
                        <MapPin className="w-5 h-5 text-blue-400" />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-white">Ver en Google Maps</div>
                          <div className="text-xs text-gray-400">Abrir perfil del negocio</div>
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-blue-400 transition-colors" />
                      </a>

                      <div className="flex items-center gap-3 p-3 bg-gray-800/30 border border-gray-700 rounded-lg">
                        <Phone className="w-5 h-5 text-gray-400" />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-white">{selectedOrder.client_phone}</div>
                          <div className="text-xs text-gray-400">Teléfono de contacto</div>
                        </div>
                      </div>

                      {selectedOrder.score_inicial !== null && (
                        <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-400">Score Inicial de Visibilidad</span>
                            <AlertCircle className="w-4 h-4 text-red-400" />
                          </div>
                          <div className="text-3xl font-bold text-red-400">{selectedOrder.score_inicial}/100</div>
                          <div className="text-xs text-gray-500 mt-1">Objetivo: Llevar a 85+</div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Tasks Checklist Section */}
                  <div className="p-6 border-b border-gray-800">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Tareas del Proyecto</h3>
                      <div className="text-xs text-gray-500">
                        {tasks.filter(t => t.is_completed).length} de {tasks.length} completadas
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-400">Progreso General</span>
                        <span className="text-lg font-bold text-white">{taskStats.completion_percentage.toFixed(0)}%</span>
                      </div>
                      <div className="w-full h-3 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transition-all duration-500"
                          style={{ width: `${taskStats.completion_percentage}%` }}
                        />
                      </div>
                    </div>

                    {/* Task List */}
                    <div className="space-y-2">
                      {tasks.map((task) => (
                        <div
                          key={task.id}
                          className={`p-4 rounded-lg border transition-all ${
                            task.is_completed
                              ? 'bg-green-500/5 border-green-500/20'
                              : 'bg-gray-800/30 border-gray-700 hover:border-gray-600'
                          }`}
                        >
                          <div className="flex items-start gap-3">
                            <button
                              onClick={() => toggleTask(task.id, task.is_completed)}
                              className="mt-0.5 flex-shrink-0"
                            >
                              {task.is_completed ? (
                                <CheckCircle2 className="w-5 h-5 text-green-400" />
                              ) : (
                                <Circle className="w-5 h-5 text-gray-500 hover:text-gray-400 transition-colors" />
                              )}
                            </button>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between gap-2">
                                <p className={`text-sm ${task.is_completed ? 'text-gray-500 line-through' : 'text-white'}`}>
                                  {task.description}
                                </p>
                                <div className="flex items-center gap-2 flex-shrink-0">
                                  <span className={`text-xs px-2 py-0.5 rounded border ${getCategoryBadgeColor(task.category)}`}>
                                    {task.category}
                                  </span>
                                  <span className={`text-xs px-2 py-0.5 rounded ${
                                    task.priority >= 9 ? 'bg-red-500/10 text-red-400' :
                                    task.priority >= 7 ? 'bg-orange-500/10 text-orange-400' :
                                    task.priority >= 5 ? 'bg-yellow-500/10 text-yellow-400' :
                                    'bg-gray-500/10 text-gray-400'
                                  }`}>
                                    P{task.priority}
                                  </span>
                                </div>
                              </div>
                              {task.completed_at && (
                                <p className="text-xs text-gray-500 mt-1">
                                  Completado: {new Date(task.completed_at).toLocaleDateString('es-ES')}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Internal Notes Section */}
                  <div className="p-6">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Notas Internas</h3>
                    <textarea
                      value={internalNotes}
                      onChange={(e) => setInternalNotes(e.target.value)}
                      placeholder="Escribe notas sobre el progreso del proyecto..."
                      className="w-full h-32 px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 resize-none"
                    />
                  </div>
                </div>

                {/* Panel Footer: Complete Button */}
                <div className="p-6 border-t border-gray-800 bg-black/30">
                  <button
                    onClick={completeOrder}
                    disabled={taskStats.completion_percentage < 100 || completingOrder}
                    className={`w-full py-4 rounded-lg font-semibold text-white transition-all flex items-center justify-center gap-2 ${
                      taskStats.completion_percentage >= 100 && !completingOrder
                        ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 shadow-lg shadow-green-500/20'
                        : 'bg-gray-800 cursor-not-allowed opacity-50'
                    }`}
                  >
                    {completingOrder ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Enviando...
                      </>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        Finalizar y Enviar Reporte de Éxito
                      </>
                    )}
                  </button>
                  {taskStats.completion_percentage < 100 && (
                    <p className="text-xs text-center text-gray-500 mt-3">
                      Completa todas las tareas para habilitar este botón ({taskStats.pending_tasks} pendientes)
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
