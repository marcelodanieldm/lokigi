'use client';

import { useState, useEffect } from 'react';
import AuthGuard from '@/components/AuthGuard';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import {
  TrendingUp,
  Users,
  Globe,
  DollarSign,
  Clock,
  Target,
  Zap,
  TrendingDown,
  Loader2,
  BarChart3,
  PieChart,
  Calendar,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  PieChart as RePieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Interfaces
interface ConversionMetrics {
  total_leads: number;
  diagnoses_given: number;
  ebook_purchases: number;
  service_purchases: number;
  subscriptions: number;
  diagnosis_to_ebook_rate: number;
  diagnosis_to_service_rate: number;
  diagnosis_to_subscription_rate: number;
  overall_conversion_rate: number;
}

interface RegionPerformance {
  country: string;
  country_name: string;
  flag: string;
  total_leads: number;
  total_orders: number;
  total_revenue: number;
  conversion_rate: number;
  avg_order_value: number;
  roi_score: number;
}

interface SubscriptionLTV {
  active_subscriptions: number;
  canceled_subscriptions: number;
  avg_subscription_days: number;
  avg_lifetime_months: number;
  estimated_ltv: number;
  churn_rate: number;
}

interface OperationalEfficiency {
  total_service_orders: number;
  completed_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  avg_completion_time_hours: number;
  avg_completion_time_days: number;
  fastest_completion_hours: number;
  slowest_completion_hours: number;
  completion_rate: number;
}

interface AdvancedAnalytics {
  time_range: string;
  conversion_metrics: ConversionMetrics;
  region_performance: RegionPerformance[];
  subscription_ltv: SubscriptionLTV;
  operational_efficiency: OperationalEfficiency;
}

const COLORS = ['#00ff41', '#00cc33', '#00ff99', '#66ff99', '#99ffcc'];

export default function AdminAnalyticsPage() {
  const [analytics, setAnalytics] = useState<AdvancedAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/analytics/business-intelligence?time_range=${timeRange}`
      );
      const data = await response.json();
      setAnalytics(data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getTimeRangeLabel = () => {
    const labels: Record<string, string> = {
      '7d': 'Últimos 7 días',
      '30d': 'Últimos 30 días',
      '90d': 'Últimos 90 días',
      'all': 'Todo el tiempo',
    };
    return labels[timeRange];
  };

  if (loading) {
    return (
      <AuthGuard requiredRole="superuser">
        <div className="flex min-h-screen bg-dark-900 items-center justify-center">
          <Loader2 className="w-12 h-12 text-neon-500 animate-spin" />
        </div>
      </AuthGuard>
    );
  }

  if (!analytics) {
    return (
      <AuthGuard requiredRole="superuser">
        <div className="flex min-h-screen bg-dark-900 items-center justify-center">
          <div className="text-center">
            <p className="text-white text-xl mb-4">Error al cargar analytics</p>
            <button onClick={fetchAnalytics} className="btn-primary">
              Reintentar
            </button>
          </div>
        </div>
      </AuthGuard>
    );
  }

  // Preparar datos para gráficos
  const conversionData = [
    { name: 'E-book $9', value: analytics.conversion_metrics.ebook_purchases, rate: analytics.conversion_metrics.diagnosis_to_ebook_rate },
    { name: 'Servicio $99', value: analytics.conversion_metrics.service_purchases, rate: analytics.conversion_metrics.diagnosis_to_service_rate },
    { name: 'Suscripción $29', value: analytics.conversion_metrics.subscriptions, rate: analytics.conversion_metrics.diagnosis_to_subscription_rate },
  ];

  const statusData = [
    { name: 'Completados', value: analytics.operational_efficiency.completed_orders },
    { name: 'En Proceso', value: analytics.operational_efficiency.in_progress_orders },
    { name: 'Pendientes', value: analytics.operational_efficiency.pending_orders },
  ];

  return (
    <AuthGuard requiredRole="superuser">
      <div className="flex min-h-screen bg-dark-900">
        <DashboardSidebar />
        
        <main className="flex-1 p-8 ml-64">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-neon-500" />
              Business Intelligence
              <span className="text-neon-500 ml-2 font-mono">{'>'} Admin</span>
            </h1>
            <p className="text-gray-400">
              KPIs avanzados y métricas de decisión estratégica
            </p>
          </div>

          {/* Time Range Selector */}
          <div className="card mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-neon-500" />
                <span className="text-white font-medium">Período:</span>
                <span className="text-gray-400">{getTimeRangeLabel()}</span>
              </div>
              <div className="flex gap-2">
                {(['7d', '30d', '90d', 'all'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      timeRange === range
                        ? 'bg-neon-500 text-dark-900'
                        : 'bg-dark-800 text-gray-400 hover:bg-dark-700'
                    }`}
                  >
                    {range === 'all' ? 'Todo' : range.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* ========== 1. MÉTRICAS DE CONVERSIÓN ========== */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Target className="w-6 h-6 text-neon-500" />
              1. Métricas de Conversión
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {/* Stat Cards */}
              <div className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Total Leads</p>
                    <p className="text-3xl font-bold text-white">{analytics.conversion_metrics.total_leads.toLocaleString()}</p>
                  </div>
                  <Users className="w-8 h-8 text-cyber-blue" />
                </div>
              </div>

              <div className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Diagnósticos Entregados</p>
                    <p className="text-3xl font-bold text-white">{analytics.conversion_metrics.diagnoses_given.toLocaleString()}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {((analytics.conversion_metrics.diagnoses_given / analytics.conversion_metrics.total_leads) * 100).toFixed(1)}% de leads
                    </p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-warning-500" />
                </div>
              </div>

              <div className="card border-2 border-neon-500/30">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Conversión Global</p>
                    <p className="text-3xl font-bold text-neon-500">{analytics.conversion_metrics.overall_conversion_rate}%</p>
                    <p className="text-xs text-gray-500 mt-1">Diagnóstico → Compra</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-neon-500" />
                </div>
              </div>
            </div>

            {/* Conversion Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Compras por Producto</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={conversionData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="name" stroke="#888" />
                    <YAxis stroke="#888" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #00ff41' }}
                      labelStyle={{ color: '#fff' }}
                    />
                    <Bar dataKey="value" fill="#00ff41" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Tasas de Conversión</h3>
                <div className="space-y-4 pt-4">
                  {conversionData.map((item, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-300">{item.name}</span>
                        <span className="text-neon-500 font-bold">{item.rate}%</span>
                      </div>
                      <div className="h-3 bg-dark-900 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-neon-500 transition-all duration-500"
                          style={{ width: `${Math.min(item.rate * 2, 100)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ========== 2. DESEMPEÑO POR REGIÓN ========== */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Globe className="w-6 h-6 text-neon-500" />
              2. Desempeño por Región (ROI)
            </h2>
            
            <div className="card overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-gray-400 font-medium">País</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">Leads</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">Órdenes</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">Revenue</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">Conv. %</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">AOV</th>
                    <th className="text-right py-3 px-4 text-gray-400 font-medium">ROI Score</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.region_performance.map((region, index) => (
                    <tr
                      key={region.country}
                      className="border-b border-gray-800 hover:bg-dark-800 transition-colors"
                    >
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{region.flag}</span>
                          <span className="text-white font-medium">{region.country_name}</span>
                          {index === 0 && (
                            <span className="px-2 py-1 bg-neon-500 text-dark-900 text-xs font-bold rounded">
                              TOP
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="text-right py-4 px-4 text-gray-300">{region.total_leads}</td>
                      <td className="text-right py-4 px-4 text-gray-300">{region.total_orders}</td>
                      <td className="text-right py-4 px-4 text-neon-500 font-bold">
                        {formatCurrency(region.total_revenue)}
                      </td>
                      <td className="text-right py-4 px-4 text-cyber-blue font-medium">
                        {region.conversion_rate}%
                      </td>
                      <td className="text-right py-4 px-4 text-gray-300">
                        {formatCurrency(region.avg_order_value)}
                      </td>
                      <td className="text-right py-4 px-4">
                        <span className="text-neon-500 font-bold text-lg">
                          {region.roi_score.toFixed(0)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* ========== 3. SUBSCRIPTION LTV ========== */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <DollarSign className="w-6 h-6 text-neon-500" />
              3. Lifetime Value (Suscripciones $29/mes)
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Activas</p>
                    <p className="text-3xl font-bold text-neon-500">
                      {analytics.subscription_ltv.active_subscriptions}
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-neon-500" />
                </div>
              </div>

              <div className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Canceladas</p>
                    <p className="text-3xl font-bold text-danger-500">
                      {analytics.subscription_ltv.canceled_subscriptions}
                    </p>
                  </div>
                  <TrendingDown className="w-8 h-8 text-danger-500" />
                </div>
              </div>

              <div className="card border-2 border-neon-500/30">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Duración Promedio</p>
                    <p className="text-3xl font-bold text-neon-500">
                      {analytics.subscription_ltv.avg_lifetime_months.toFixed(1)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">meses</p>
                  </div>
                  <Clock className="w-8 h-8 text-neon-500" />
                </div>
              </div>

              <div className="card border-2 border-neon-500/30">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">LTV Estimado</p>
                    <p className="text-3xl font-bold text-neon-500">
                      {formatCurrency(analytics.subscription_ltv.estimated_ltv)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">por suscriptor</p>
                  </div>
                  <DollarSign className="w-8 h-8 text-neon-500" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Distribución de Suscripciones</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <RePieChart>
                    <Pie
                      data={[
                        { name: 'Activas', value: analytics.subscription_ltv.active_subscriptions },
                        { name: 'Canceladas', value: analytics.subscription_ltv.canceled_subscriptions },
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label
                    >
                      <Cell fill="#00ff41" />
                      <Cell fill="#ff6b6b" />
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #00ff41' }}
                    />
                    <Legend />
                  </RePieChart>
                </ResponsiveContainer>
              </div>

              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Métricas de Retención</h3>
                <div className="space-y-6 pt-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300">Tasa de Churn</span>
                      <span className={`font-bold ${
                        analytics.subscription_ltv.churn_rate > 20 ? 'text-danger-500' : 
                        analytics.subscription_ltv.churn_rate > 10 ? 'text-warning-500' : 
                        'text-neon-500'
                      }`}>
                        {analytics.subscription_ltv.churn_rate}%
                      </span>
                    </div>
                    <div className="h-3 bg-dark-900 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          analytics.subscription_ltv.churn_rate > 20 ? 'bg-danger-500' : 
                          analytics.subscription_ltv.churn_rate > 10 ? 'bg-warning-500' : 
                          'bg-neon-500'
                        }`}
                        style={{ width: `${analytics.subscription_ltv.churn_rate}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300">Días promedio de suscripción</span>
                      <span className="text-neon-500 font-bold">
                        {analytics.subscription_ltv.avg_subscription_days.toFixed(0)} días
                      </span>
                    </div>
                  </div>

                  <div className="bg-dark-900 p-4 rounded-lg border border-neon-500/30">
                    <p className="text-sm text-gray-400 mb-2">💡 Insight:</p>
                    <p className="text-white text-sm">
                      {analytics.subscription_ltv.churn_rate < 10
                        ? '✅ Excelente retención de suscriptores. Continuar con la estrategia actual.'
                        : analytics.subscription_ltv.churn_rate < 20
                        ? '⚠️ Churn moderado. Considerar programas de retención.'
                        : '🚨 Churn alto. Revisar propuesta de valor y engagement.'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ========== 4. EFICIENCIA OPERATIVA ========== */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Zap className="w-6 h-6 text-neon-500" />
              4. Eficiencia Operativa (Órdenes $99)
            </h2>
            
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
              <div className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Total Órdenes</p>
                    <p className="text-3xl font-bold text-white">
                      {analytics.operational_efficiency.total_service_orders}
                    </p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-cyber-blue" />
                </div>
              </div>

              <div className="card border-2 border-neon-500/30">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Tiempo Promedio</p>
                    <p className="text-3xl font-bold text-neon-500">
                      {analytics.operational_efficiency.avg_completion_time_hours.toFixed(1)}h
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {analytics.operational_efficiency.avg_completion_time_days.toFixed(1)} días
                    </p>
                  </div>
                  <Clock className="w-8 h-8 text-neon-500" />
                </div>
              </div>

              <div className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Más Rápida</p>
                    <p className="text-3xl font-bold text-neon-500">
                      {analytics.operational_efficiency.fastest_completion_hours.toFixed(1)}h
                    </p>
                  </div>
                  <Zap className="w-8 h-8 text-neon-500" />
                </div>
              </div>

              <div className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Tasa de Completitud</p>
                    <p className="text-3xl font-bold text-neon-500">
                      {analytics.operational_efficiency.completion_rate}%
                    </p>
                  </div>
                  <Target className="w-8 h-8 text-neon-500" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Estado de Órdenes</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <RePieChart>
                    <Pie
                      data={statusData}
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {statusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #00ff41' }}
                    />
                  </RePieChart>
                </ResponsiveContainer>
              </div>

              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Performance del Equipo</h3>
                <div className="space-y-6 pt-4">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-gray-400 text-sm mb-1">Completadas</p>
                      <p className="text-2xl font-bold text-neon-500">
                        {analytics.operational_efficiency.completed_orders}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-1">En Proceso</p>
                      <p className="text-2xl font-bold text-cyber-blue">
                        {analytics.operational_efficiency.in_progress_orders}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm mb-1">Pendientes</p>
                      <p className="text-2xl font-bold text-warning-500">
                        {analytics.operational_efficiency.pending_orders}
                      </p>
                    </div>
                  </div>

                  <div className="bg-dark-900 p-4 rounded-lg border border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-gray-300">Más lenta</span>
                      <span className="text-danger-500 font-bold">
                        {analytics.operational_efficiency.slowest_completion_hours.toFixed(1)}h
                      </span>
                    </div>
                  </div>

                  <div className="bg-dark-900 p-4 rounded-lg border border-neon-500/30">
                    <p className="text-sm text-gray-400 mb-2">💡 Insight:</p>
                    <p className="text-white text-sm">
                      {analytics.operational_efficiency.avg_completion_time_hours < 24
                        ? '🚀 Excelente velocidad. El equipo está ejecutando órdenes en menos de 1 día.'
                        : analytics.operational_efficiency.avg_completion_time_hours < 48
                        ? '⚠️ Velocidad adecuada pero puede mejorar. Optimizar workflow.'
                        : '🚨 Tiempo de completitud alto. Revisar cuellos de botella.'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Summary Insights */}
          <div className="card border-2 border-neon-500/30">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <PieChart className="w-6 h-6 text-neon-500" />
              Resumen Ejecutivo
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-dark-900 p-4 rounded-lg">
                <p className="text-sm text-gray-400 mb-1">Mejor producto</p>
                <p className="text-neon-500 font-bold">
                  {analytics.conversion_metrics.service_purchases > analytics.conversion_metrics.ebook_purchases
                    ? 'Servicio $99'
                    : 'E-book $9'}
                </p>
              </div>
              <div className="bg-dark-900 p-4 rounded-lg">
                <p className="text-sm text-gray-400 mb-1">Mejor región</p>
                <p className="text-neon-500 font-bold flex items-center gap-2">
                  {analytics.region_performance[0]?.flag} {analytics.region_performance[0]?.country_name}
                </p>
              </div>
              <div className="bg-dark-900 p-4 rounded-lg">
                <p className="text-sm text-gray-400 mb-1">Salud del negocio</p>
                <p className="text-neon-500 font-bold">
                  {analytics.conversion_metrics.overall_conversion_rate > 10 &&
                  analytics.subscription_ltv.churn_rate < 15 &&
                  analytics.operational_efficiency.completion_rate > 70
                    ? '✅ Excelente'
                    : '⚠️ Necesita atención'}
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  );
}
  return (
    <AuthGuard requiredRole="superuser">
      <div className="flex min-h-screen bg-dark-900">
        <DashboardSidebar />
        
        <main className="flex-1 p-8 ml-64">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-neon-500" />
              Analytics Dashboard
              <span className="text-neon-500 font-mono">{'>'} Admin</span>
            </h1>
            <p className="text-gray-400">
              Métricas clave para decidir dónde invertir tiempo (tu único capital)
            </p>
          </div>

          {/* Time Range Selector */}
          <div className="card mb-6">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-400">Período:</span>
              <div className="flex gap-2">
                {[
                  { value: '7d', label: 'Últimos 7 días' },
                  { value: '30d', label: 'Últimos 30 días' },
                  { value: 'all', label: 'Todo el tiempo' },
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setTimeRange(option.value as any)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      timeRange === option.value
                        ? 'bg-neon-500 text-dark-900'
                        : 'bg-dark-700 text-gray-400 hover:bg-dark-600'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-12 h-12 text-neon-500 animate-spin" />
            </div>
          ) : !analytics ? (
            <div className="card text-center py-12">
              <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">No hay datos</h3>
              <p className="text-gray-400">Aún no hay suficiente información para mostrar</p>
            </div>
          ) : (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {/* Total Leads */}
                <div className="card card-hover">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 bg-cyber-blue/10 rounded-lg flex items-center justify-center border border-cyber-blue/30">
                      <Users className="w-6 h-6 text-cyber-blue" />
                    </div>
                    <TrendingUp className="w-5 h-5 text-neon-500" />
                  </div>
                  <p className="text-sm text-gray-400 mb-1">Total Leads</p>
                  <p className="text-3xl font-bold text-white">{analytics.total_leads}</p>
                </div>

                {/* Total Orders */}
                <div className="card card-hover">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 bg-neon-500/10 rounded-lg flex items-center justify-center border border-neon-500/30">
                      <BarChart3 className="w-6 h-6 text-neon-500" />
                    </div>
                    <TrendingUp className="w-5 h-5 text-neon-500" />
                  </div>
                  <p className="text-sm text-gray-400 mb-1">Pedidos Pagados</p>
                  <p className="text-3xl font-bold text-white">{analytics.total_orders}</p>
                </div>

                {/* Total Revenue */}
                <div className="card card-hover">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 bg-warning-500/10 rounded-lg flex items-center justify-center border border-warning-500/30">
                      <DollarSign className="w-6 h-6 text-warning-500" />
                    </div>
                    <TrendingUp className="w-5 h-5 text-neon-500" />
                  </div>
                  <p className="text-sm text-gray-400 mb-1">Ingresos Totales</p>
                  <p className="text-3xl font-bold text-white">{formatCurrency(analytics.total_revenue)}</p>
                </div>

                {/* Conversion Rate */}
                <div className="card card-hover">
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-12 h-12 bg-cyber-purple/10 rounded-lg flex items-center justify-center border border-cyber-purple/30">
                      <Globe className="w-6 h-6 text-cyber-purple" />
                    </div>
                    <TrendingUp className="w-5 h-5 text-neon-500" />
                  </div>
                  <p className="text-sm text-gray-400 mb-1">Conversión</p>
                  <p className="text-3xl font-bold text-white">{analytics.conversion_rate.toFixed(1)}%</p>
                </div>
              </div>

              {/* Leads por País */}
              <div className="card">
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                  <MapPin className="w-6 h-6 text-neon-500" />
                  Leads por País
                  <span className="text-sm font-normal text-gray-400 ml-auto">
                    (Decisión crítica: ¿dónde invertir tu tiempo?)
                  </span>
                </h2>

                <div className="space-y-4">
                  {analytics.leads_by_country.map((country, index) => (
                    <div
                      key={country.country}
                      className="group hover:bg-dark-700 p-4 rounded-lg transition-all cursor-pointer"
                    >
                      {/* Country Header */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-3xl">{country.flag}</span>
                          <div>
                            <h3 className="text-lg font-bold text-white group-hover:text-neon-500 transition-colors">
                              {country.country_name}
                            </h3>
                            <p className="text-sm text-gray-400">
                              {country.count} leads • {country.percentage.toFixed(1)}% del total
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-neon-500">{formatCurrency(country.revenue)}</p>
                          <p className="text-xs text-gray-500">Ingresos</p>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="relative h-3 bg-dark-800 rounded-full overflow-hidden">
                        <div
                          className="absolute inset-y-0 left-0 bg-gradient-to-r from-neon-500 to-cyber-blue transition-all duration-500"
                          style={{ width: `${(country.revenue / getMaxRevenue()) * 100}%` }}
                        />
                      </div>

                      {/* Rank Badge */}
                      {index === 0 && (
                        <div className="mt-2">
                          <span className="inline-flex items-center gap-1 px-3 py-1 bg-warning-500/20 text-warning-500 border border-warning-500/50 rounded-full text-xs font-bold uppercase">
                            🏆 Mayor oportunidad
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Strategic Insight */}
                <div className="mt-8 p-6 bg-neon-500/5 border border-neon-500/30 rounded-lg">
                  <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                    💡 Insight Estratégico
                  </h3>
                  <p className="text-gray-300 leading-relaxed">
                    {analytics.leads_by_country[0] && (
                      <>
                        <strong className="text-neon-500">{analytics.leads_by_country[0].country_name}</strong> es tu mercado más fuerte con{' '}
                        <strong className="text-neon-500">{analytics.leads_by_country[0].count} leads</strong> y{' '}
                        <strong className="text-neon-500">{formatCurrency(analytics.leads_by_country[0].revenue)}</strong> en ingresos.
                        {analytics.leads_by_country[0].percentage > 50 ? (
                          ' Representa más del 50% de tu negocio. Considera enfocar recursos aquí.'
                        ) : (
                          ' Diversifica tu marketing para aprovechar otros mercados también.'
                        )}
                      </>
                    )}
                  </p>
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </AuthGuard>
  );
}
