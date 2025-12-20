'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import {
  TrendingUp,
  Clock,
  CheckCircle2,
  DollarSign,
  AlertCircle,
  ArrowRight,
  Activity
} from 'lucide-react';

interface DashboardStats {
  total_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  completed_orders: number;
  total_revenue: number;
}

interface RecentOrder {
  id: number;
  business_name: string;
  client_name: string;
  status: string;
  created_at: string;
}

export default function DashboardHomePage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentOrders, setRecentOrders] = useState<RecentOrder[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch stats
      const statsResponse = await fetch('http://localhost:8000/api/dashboard/stats');
      const statsData = await statsResponse.json();
      setStats(statsData);

      // Fetch recent orders (limit 5)
      const ordersResponse = await fetch('http://localhost:8000/api/dashboard/orders');
      const ordersData = await ordersResponse.json();
      setRecentOrders(ordersData.slice(0, 5));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Ingresos Totales',
      value: `$${stats?.total_revenue.toLocaleString() || 0}`,
      icon: DollarSign,
      color: 'from-green-500 to-emerald-500',
      bgColor: 'from-green-50 to-emerald-50',
      textColor: 'text-green-700'
    },
    {
      title: 'Órdenes Totales',
      value: stats?.total_orders || 0,
      icon: Activity,
      color: 'from-blue-500 to-purple-500',
      bgColor: 'from-blue-50 to-purple-50',
      textColor: 'text-blue-700'
    },
    {
      title: 'Pendientes',
      value: stats?.pending_orders || 0,
      icon: Clock,
      color: 'from-yellow-500 to-orange-500',
      bgColor: 'from-yellow-50 to-orange-50',
      textColor: 'text-yellow-700'
    },
    {
      title: 'En Proceso',
      value: stats?.in_progress_orders || 0,
      icon: AlertCircle,
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'from-blue-50 to-cyan-50',
      textColor: 'text-blue-700'
    },
    {
      title: 'Completadas',
      value: stats?.completed_orders || 0,
      icon: CheckCircle2,
      color: 'from-green-500 to-teal-500',
      bgColor: 'from-green-50 to-teal-50',
      textColor: 'text-green-700'
    }
  ];

  const getStatusBadge = (status: string) => {
    const configs = {
      PENDING: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Pendiente' },
      IN_PROGRESS: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'En Proceso' },
      COMPLETED: { bg: 'bg-green-100', text: 'text-green-700', label: 'Completado' }
    };
    const config = configs[status as keyof typeof configs] || configs.PENDING;
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-bold ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50">
        <DashboardSidebar />
        <main className="flex-1 p-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-gray-600">Cargando dashboard...</p>
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
        <div className="mb-8">
          <h1 className="text-4xl font-black text-gray-900 mb-2">
            Dashboard Operativo
          </h1>
          <p className="text-gray-600">
            Gestión de órdenes de optimización SEO Local
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          {statCards.map((card, index) => {
            const Icon = card.icon;
            return (
              <div
                key={index}
                className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${card.bgColor} border-2 border-gray-200 p-6 shadow-sm hover:shadow-lg transition-shadow`}
              >
                <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${card.color} opacity-10 rounded-full -mr-12 -mt-12`} />
                <div className="relative">
                  <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${card.color} mb-3`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-sm font-semibold text-gray-600 mb-1">
                    {card.title}
                  </div>
                  <div className={`text-3xl font-black ${card.textColor}`}>
                    {card.value}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Link
            href="/dashboard/orders?status=pending"
            className="group bg-gradient-to-br from-yellow-500 to-orange-500 rounded-2xl p-6 text-white hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <Clock className="w-10 h-10 mb-3" />
            <h3 className="text-xl font-bold mb-2">Ver Pendientes</h3>
            <p className="text-yellow-100 mb-4">
              {stats?.pending_orders || 0} órdenes esperando atención
            </p>
            <div className="flex items-center gap-2 font-semibold">
              Ir a pendientes
              <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform" />
            </div>
          </Link>

          <Link
            href="/dashboard/orders?status=in_progress"
            className="group bg-gradient-to-br from-blue-500 to-purple-500 rounded-2xl p-6 text-white hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <AlertCircle className="w-10 h-10 mb-3" />
            <h3 className="text-xl font-bold mb-2">En Proceso</h3>
            <p className="text-blue-100 mb-4">
              {stats?.in_progress_orders || 0} órdenes en curso
            </p>
            <div className="flex items-center gap-2 font-semibold">
              Ver en proceso
              <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform" />
            </div>
          </Link>

          <Link
            href="/dashboard/orders"
            className="group bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-6 text-white hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <Activity className="w-10 h-10 mb-3" />
            <h3 className="text-xl font-bold mb-2">Todas las Órdenes</h3>
            <p className="text-gray-300 mb-4">
              Ver lista completa de {stats?.total_orders || 0} órdenes
            </p>
            <div className="flex items-center gap-2 font-semibold">
              Ver todas
              <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform" />
            </div>
          </Link>
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Órdenes Recientes</h2>
              <Link
                href="/dashboard/orders"
                className="text-blue-600 hover:text-blue-700 font-semibold text-sm flex items-center gap-1"
              >
                Ver todas
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {recentOrders.length === 0 ? (
            <div className="p-12 text-center">
              <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-600">No hay órdenes recientes</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {recentOrders.map((order) => (
                <Link
                  key={order.id}
                  href={`/dashboard/orders/${order.id}`}
                  className="flex items-center justify-between p-6 hover:bg-gray-50 transition-colors group"
                >
                  <div className="flex-1">
                    <div className="font-bold text-gray-900 mb-1 group-hover:text-blue-600">
                      {order.business_name}
                    </div>
                    <div className="text-sm text-gray-600">
                      Cliente: {order.client_name}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {getStatusBadge(order.status)}
                    <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Performance Summary */}
        <div className="mt-8 grid md:grid-cols-2 gap-6">
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl border-2 border-green-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">Tasa de Completado</h3>
                <p className="text-sm text-gray-600">Órdenes finalizadas vs. totales</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
            <div className="text-4xl font-black text-green-600 mb-2">
              {stats?.total_orders 
                ? Math.round((stats.completed_orders / stats.total_orders) * 100)
                : 0}%
            </div>
            <div className="text-sm text-gray-600">
              {stats?.completed_orders || 0} de {stats?.total_orders || 0} órdenes completadas
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl border-2 border-blue-200 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-1">Órdenes Activas</h3>
                <p className="text-sm text-gray-600">Pendientes + En proceso</p>
              </div>
              <Activity className="w-8 h-8 text-blue-600" />
            </div>
            <div className="text-4xl font-black text-blue-600 mb-2">
              {(stats?.pending_orders || 0) + (stats?.in_progress_orders || 0)}
            </div>
            <div className="text-sm text-gray-600">
              {stats?.pending_orders || 0} pendientes · {stats?.in_progress_orders || 0} en proceso
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
