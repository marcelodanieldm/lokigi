'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AuthGuard from '@/components/AuthGuard';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import {
  Search,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Calendar,
  User,
  Building2,
  Loader2,
  TrendingUp,
} from 'lucide-react';

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
  pais: string | null;
  idioma: string | null;
}

export default function WorkerDashboardPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const router = useRouter();

  useEffect(() => {
    fetchOrders();
  }, [statusFilter]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter !== 'all') {
        params.append('status_filter', statusFilter);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/orders?${params}`);
      const data = await response.json();
      setOrders(data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchOrders();
  };

  const getStatusBadge = (status: string) => {
    const configs = {
      PENDING: {
        bg: 'bg-warning-500/20',
        text: 'text-warning-500',
        border: 'border-warning-500/50',
        icon: Clock,
        label: 'Pendiente',
      },
      IN_PROGRESS: {
        bg: 'bg-cyber-blue/20',
        text: 'text-cyber-blue',
        border: 'border-cyber-blue/50',
        icon: AlertCircle,
        label: 'En Proceso',
      },
      COMPLETED: {
        bg: 'bg-neon-500/20',
        text: 'text-neon-500',
        border: 'border-neon-500/50',
        icon: CheckCircle2,
        label: 'Completado',
      },
    };

    const config = configs[status as keyof typeof configs] || configs.PENDING;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-lg border ${config.bg} ${config.text} ${config.border} text-xs font-mono font-bold uppercase`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </span>
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getCountryFlag = (countryCode: string | null) => {
    const flags: Record<string, string> = {
      BR: '🇧🇷',
      US: '🇺🇸',
      ES: '🇪🇸',
      MX: '🇲🇽',
      AR: '🇦🇷',
      CL: '🇨🇱',
      CO: '🇨🇴',
      PE: '🇵🇪',
      VE: '🇻🇪',
      UY: '🇺🇾',
      PY: '🇵🇾',
      EC: '🇪🇨',
      BO: '🇧🇴',
      CR: '🇨🇷',
      PA: '🇵🇦',
      GT: '🇬🇹',
      HN: '🇭🇳',
      SV: '🇸🇻',
      NI: '🇳🇮',
      DO: '🇩🇴',
      CU: '🇨🇺',
      PR: '🇵🇷',
    };
    return countryCode ? flags[countryCode] || '🌎' : '🌎';
  };

  const getTimeElapsed = (dateString: string) => {
    const now = new Date();
    const created = new Date(dateString);
    const diffMs = now.getTime() - created.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffHours < 1) return { text: '<1h', color: 'text-neon-500', urgent: false };
    if (diffHours < 12) return { text: `${diffHours}h`, color: 'text-cyber-blue', urgent: false };
    if (diffHours < 24) return { text: `${diffHours}h`, color: 'text-warning-500', urgent: true };
    const diffDays = Math.floor(diffHours / 24);
    return { text: `${diffDays}d`, color: 'text-danger-500', urgent: true };
  };

  return (
    <AuthGuard requiredRole="worker">
      <div className="flex min-h-screen bg-dark-900">
        <DashboardSidebar />
        
        <main className="flex-1 p-8 ml-64">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              Panel de Trabajo
              <span className="text-neon-500 ml-2 font-mono">{'>'} Worker</span>
            </h1>
            <p className="text-gray-400">
              Gestiona pedidos manualmente para mantener costos en cero
            </p>
          </div>

          {/* Filters */}
          <div className="card mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative group">
                <div className="absolute -inset-1 bg-neon-500/20 rounded-lg blur opacity-0 group-focus-within:opacity-100 transition duration-300" />
                <div className="relative flex">
                  <input
                    type="text"
                    placeholder="Buscar por negocio o cliente..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="input-cyber flex-1 rounded-r-none"
                  />
                  <button
                    onClick={handleSearch}
                    className="btn-primary rounded-l-none"
                  >
                    <Search className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input-cyber min-w-[200px]"
              >
                <option value="pending">🕐 Pendientes</option>
                <option value="in_progress">🔄 En Proceso</option>
                <option value="completed">✅ Completados</option>
                <option value="all">📊 Todos</option>
              </select>
            </div>
          </div>

          {/* Orders Table */}
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-neon-500 animate-spin" />
            </div>
          ) : orders.length === 0 ? (
            <div className="card text-center py-12">
              <AlertCircle className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">No hay pedidos</h3>
              <p className="text-gray-400">
                {statusFilter !== 'all' ? 'Intenta cambiar el filtro' : 'No hay pedidos en el sistema'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {orders.map((order) => {
                const timeElapsed = getTimeElapsed(order.created_at);
                return (
                <div
                  key={order.id}
                  className={`card card-hover cursor-pointer group ${timeElapsed.urgent ? 'border-2 border-danger-500/50' : ''}`}
                  onClick={() => router.push(`/dashboard/work/${order.id}`)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 space-y-3">
                      {/* Header Row */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-neon-500/10 rounded-lg flex items-center justify-center border border-neon-500/30">
                            <span className="text-neon-500 font-mono font-bold">#{order.id}</span>
                          </div>
                          <div>
                            <h3 className="text-lg font-bold text-white group-hover:text-neon-500 transition-colors flex items-center gap-2">
                              {order.business_name}
                              <span className="text-2xl">{getCountryFlag(order.pais)}</span>
                            </h3>
                            <p className="text-sm text-gray-400 flex items-center gap-2">
                              <User className="w-3 h-3" />
                              {order.client_name}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {/* Time Elapsed Badge */}
                          <span className={`px-3 py-1 rounded-lg border ${timeElapsed.urgent ? 'bg-danger-500/20 border-danger-500/50' : 'bg-gray-800 border-gray-700'} ${timeElapsed.color} text-xs font-mono font-bold`}>
                            ⏱️ {timeElapsed.text}
                          </span>
                          {getStatusBadge(order.status)}
                        </div>
                      </div>

                      {/* Info Row */}
                      <div className="flex items-center gap-6 text-sm text-gray-400">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          {formatDate(order.created_at)}
                        </span>
                        <span className="flex items-center gap-1">
                          🌐 {order.idioma?.toUpperCase() || 'N/A'}
                        </span>
                        <span className="flex items-center gap-1">
                          <Building2 className="w-4 h-4" />
                          {order.client_email}
                        </span>
                        {order.score_inicial && (
                          <span className="flex items-center gap-1 text-neon-500">
                            <TrendingUp className="w-4 h-4" />
                            Score: {order.score_inicial}/100
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Action Button */}
                    <div className="ml-4">
                      <div className="w-10 h-10 bg-neon-500/10 rounded-lg flex items-center justify-center border border-neon-500/30 group-hover:bg-neon-500 group-hover:border-neon-500 transition-all">
                        <ArrowRight className="w-5 h-5 text-neon-500 group-hover:text-dark-900" />
                      </div>
                    </div>
                  </div>
                </div>
              )})}
            </div>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}
