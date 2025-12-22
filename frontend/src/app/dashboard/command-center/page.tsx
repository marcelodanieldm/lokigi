'use client';

import { useState, useEffect } from 'react';
import AuthGuard from '@/components/AuthGuard';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import {
  DollarSign,
  TrendingUp,
  Globe,
  Users,
  Zap,
  Target,
  AlertTriangle,
  Calendar,
  Loader2,
  MapPin,
  Clock,
  Award,
  ShoppingCart,
  CreditCard,
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
  FunnelChart,
  Funnel,
  LabelList,
} from 'recharts';

// ===== INTERFACES =====

interface FinancialMetrics {
  total_revenue: number;
  ebook_revenue: number;
  service_revenue: number;
  subscription_revenue: number;
  ebook_count: number;
  service_count: number;
  subscription_count: number;
  avg_order_value: number;
  revenue_by_country: Array<{
    country: string;
    country_name: string;
    flag: string;
    revenue: number;
    orders: number;
  }>;
}

interface ConversionFunnelMetrics {
  total_visitors: number;
  completed_diagnosis: number;
  initiated_checkout: number;
  completed_purchase: number;
  visitor_to_diagnosis_rate: number;
  diagnosis_to_checkout_rate: number;
  checkout_to_purchase_rate: number;
  checkout_abandonment_rate: number;
  overall_conversion_rate: number;
}

interface WorkerStats {
  worker_id: number;
  worker_name: string;
  worker_email: string;
  orders_completed: number;
  orders_in_progress: number;
  avg_completion_time_hours: number;
  avg_score_improvement: number;
  efficiency_score: number;
}

interface WorkerPerformanceResponse {
  workers: WorkerStats[];
  total_orders: number;
  avg_completion_time: number;
}

interface GeographicalData {
  country: string;
  country_name: string;
  flag: string;
  diagnosis_count: number;
  lead_count: number;
  conversion_rate: number;
  lat: number;
  lng: number;
}

interface GeographicalHeatmapResponse {
  locations: GeographicalData[];
  total_diagnoses: number;
  top_country: string;
}

const COLORS = ['#00ff41', '#00cc33', '#00ff99', '#66ff99', '#99ffcc', '#ccffdd'];

export default function CommandCenterPage() {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');
  const [countryFilter, setCountryFilter] = useState<string>('');
  
  const [financial, setFinancial] = useState<FinancialMetrics | null>(null);
  const [funnel, setFunnel] = useState<ConversionFunnelMetrics | null>(null);
  const [workers, setWorkers] = useState<WorkerPerformanceResponse | null>(null);
  const [heatmap, setHeatmap] = useState<GeographicalHeatmapResponse | null>(null);
  
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
  }, [timeRange, countryFilter]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const token = localStorage.getItem('token');
      
      const headers = {
        'Authorization': `Bearer ${token}`
      };

      // Fetch all endpoints in parallel
      const [financialRes, funnelRes, workersRes, heatmapRes] = await Promise.all([
        fetch(`${baseUrl}/api/dashboard/command-center/financial?time_range=${timeRange}${countryFilter ? `&country=${countryFilter}` : ''}`, { headers }),
        fetch(`${baseUrl}/api/dashboard/command-center/funnel?time_range=${timeRange}`, { headers }),
        fetch(`${baseUrl}/api/dashboard/command-center/workers?time_range=${timeRange}`, { headers }),
        fetch(`${baseUrl}/api/dashboard/command-center/heatmap?time_range=${timeRange}`, { headers }),
      ]);

      const [financialData, funnelData, workersData, heatmapData] = await Promise.all([
        financialRes.json(),
        funnelRes.json(),
        workersRes.json(),
        heatmapRes.json(),
      ]);

      setFinancial(financialData);
      setFunnel(funnelData);
      setWorkers(workersData);
      setHeatmap(heatmapData);
    } catch (error) {
      console.error('Error fetching command center data:', error);
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

  // Preparar datos para gráficos
  const revenueByProductData = financial ? [
    { name: 'E-book $9', value: financial.ebook_revenue, count: financial.ebook_count },
    { name: 'Servicio $99', value: financial.service_revenue, count: financial.service_count },
    { name: 'Suscripción $29/mes', value: financial.subscription_revenue, count: financial.subscription_count },
  ] : [];

  const funnelChartData = funnel ? [
    { name: 'Visitantes', value: funnel.total_visitors, fill: '#00ff41' },
    { name: 'Diagnósticos', value: funnel.completed_diagnosis, fill: '#00cc33' },
    { name: 'Checkout Iniciado', value: funnel.initiated_checkout, fill: '#00ff99' },
    { name: 'Compra Completada', value: funnel.completed_purchase, fill: '#66ff99' },
  ] : [];

  return (
    <AuthGuard requiredRole="superuser">
      <div className="flex min-h-screen bg-dark-900">
        <DashboardSidebar />
        
        <main className="flex-1 p-8 ml-64">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
              <Zap className="w-8 h-8 text-neon-500" />
              Command Center
              <span className="text-neon-500 ml-2 font-mono">{'>'} Business Intelligence</span>
            </h1>
            <p className="text-gray-400">
              Panel de control ejecutivo con métricas en tiempo real
            </p>
          </div>

          {/* Time Range & Filters */}
          <div className="card mb-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-neon-500" />
                <span className="text-white font-medium">Período:</span>
                <span className="text-gray-400">{getTimeRangeLabel()}</span>
              </div>
              
              <div className="flex gap-2 flex-wrap">
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

              {/* Country Filter */}
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-neon-500" />
                <select
                  value={countryFilter}
                  onChange={(e) => setCountryFilter(e.target.value)}
                  className="bg-dark-800 text-white px-4 py-2 rounded-lg border border-dark-700 focus:border-neon-500 outline-none"
                >
                  <option value="">Todos los países</option>
                  <option value="BR">🇧🇷 Brasil</option>
                  <option value="AR">🇦🇷 Argentina</option>
                  <option value="US">🇺🇸 Estados Unidos</option>
                  <option value="MX">🇲🇽 México</option>
                  <option value="CO">🇨🇴 Colombia</option>
                  <option value="CL">🇨🇱 Chile</option>
                  <option value="ES">🇪🇸 España</option>
                </select>
              </div>
            </div>
          </div>

          {/* ========== 1. FINANCIAL OVERVIEW ========== */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <DollarSign className="w-6 h-6 text-neon-500" />
              Financial Overview
            </h2>

            {/* Revenue Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="card border-neon-500">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">Revenue Total</span>
                  <TrendingUp className="w-5 h-5 text-neon-500" />
                </div>
                <p className="text-3xl font-bold text-neon-500">
                  {formatCurrency(financial?.total_revenue || 0)}
                </p>
              </div>

              <div className="card">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">E-books</span>
                  <ShoppingCart className="w-5 h-5 text-blue-400" />
                </div>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(financial?.ebook_revenue || 0)}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {financial?.ebook_count || 0} ventas
                </p>
              </div>

              <div className="card">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">Servicios</span>
                  <Target className="w-5 h-5 text-purple-400" />
                </div>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(financial?.service_revenue || 0)}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {financial?.service_count || 0} servicios
                </p>
              </div>

              <div className="card">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-400">Suscripciones MRR</span>
                  <Users className="w-5 h-5 text-green-400" />
                </div>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(financial?.subscription_revenue || 0)}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                  {financial?.subscription_count || 0} activas
                </p>
              </div>
            </div>

            {/* Revenue Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue by Product */}
              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Revenue por Producto</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={revenueByProductData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                    <XAxis dataKey="name" stroke="#666" />
                    <YAxis stroke="#666" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #00ff41' }}
                      labelStyle={{ color: '#fff' }}
                    />
                    <Bar dataKey="value" fill="#00ff41" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Revenue by Country */}
              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Revenue por País</h3>
                <div className="space-y-3">
                  {financial?.revenue_by_country.slice(0, 5).map((country, index) => (
                    <div key={country.country} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{country.flag}</span>
                        <div>
                          <p className="text-white font-medium">{country.country_name}</p>
                          <p className="text-sm text-gray-400">{country.orders} órdenes</p>
                        </div>
                      </div>
                      <p className="text-neon-500 font-bold text-lg">
                        {formatCurrency(country.revenue)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* ========== 2. CONVERSION FUNNEL ========== */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Target className="w-6 h-6 text-neon-500" />
              Conversion Funnel
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Funnel Visualization */}
              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Embudo de Conversión</h3>
                <ResponsiveContainer width="100%" height={350}>
                  <BarChart data={funnelChartData} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
                    <XAxis type="number" stroke="#666" />
                    <YAxis dataKey="name" type="category" stroke="#666" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #00ff41' }}
                    />
                    <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                      {funnelChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Funnel Metrics */}
              <div className="card">
                <h3 className="text-lg font-bold text-white mb-4">Métricas del Funnel</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Visitante → Diagnóstico</span>
                      <span className="text-neon-500 font-bold">{funnel?.visitor_to_diagnosis_rate}%</span>
                    </div>
                    <div className="w-full bg-dark-800 rounded-full h-2">
                      <div
                        className="bg-neon-500 h-2 rounded-full"
                        style={{ width: `${funnel?.visitor_to_diagnosis_rate || 0}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Diagnóstico → Checkout</span>
                      <span className="text-blue-400 font-bold">{funnel?.diagnosis_to_checkout_rate}%</span>
                    </div>
                    <div className="w-full bg-dark-800 rounded-full h-2">
                      <div
                        className="bg-blue-400 h-2 rounded-full"
                        style={{ width: `${funnel?.diagnosis_to_checkout_rate || 0}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-400">Checkout → Compra</span>
                      <span className="text-green-400 font-bold">{funnel?.checkout_to_purchase_rate}%</span>
                    </div>
                    <div className="w-full bg-dark-800 rounded-full h-2">
                      <div
                        className="bg-green-400 h-2 rounded-full"
                        style={{ width: `${funnel?.checkout_to_purchase_rate || 0}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-4 border-t border-dark-700">
                    <div className="flex justify-between items-center">
                      <span className="text-white font-medium">Conversión Global</span>
                      <span className="text-neon-500 font-bold text-2xl">
                        {funnel?.overall_conversion_rate}%
                      </span>
                    </div>
                  </div>

                  {funnel && funnel.checkout_abandonment_rate > 50 && (
                    <div className="mt-4 p-3 bg-red-500/10 border border-red-500 rounded-lg flex items-start gap-2">
                      <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-red-500 font-medium">Alto abandono en checkout</p>
                        <p className="text-sm text-gray-400 mt-1">
                          {funnel.checkout_abandonment_rate.toFixed(1)}% de usuarios abandonan el pago
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* ========== 3. WORKER PERFORMANCE ========== */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Users className="w-6 h-6 text-neon-500" />
              Worker Performance
            </h2>

            <div className="card">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-gray-400">Total de órdenes procesadas</p>
                  <p className="text-2xl font-bold text-white">{workers?.total_orders || 0}</p>
                </div>
                <div className="text-right">
                  <p className="text-gray-400">Tiempo promedio de completitud</p>
                  <p className="text-2xl font-bold text-neon-500">
                    {workers?.avg_completion_time.toFixed(1)}h
                  </p>
                </div>
              </div>

              {/* Workers Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-dark-700">
                      <th className="text-left py-3 px-4 text-gray-400 font-medium">Worker</th>
                      <th className="text-center py-3 px-4 text-gray-400 font-medium">Completadas</th>
                      <th className="text-center py-3 px-4 text-gray-400 font-medium">En Proceso</th>
                      <th className="text-center py-3 px-4 text-gray-400 font-medium">Tiempo Avg</th>
                      <th className="text-center py-3 px-4 text-gray-400 font-medium">Score Mejora</th>
                      <th className="text-center py-3 px-4 text-gray-400 font-medium">Eficiencia</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workers?.workers.map((worker, index) => (
                      <tr key={worker.worker_id} className="border-b border-dark-800 hover:bg-dark-800/50">
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            {index === 0 && (
                              <Award className="w-5 h-5 text-yellow-400" />
                            )}
                            <div>
                              <p className="text-white font-medium">{worker.worker_name}</p>
                              <p className="text-sm text-gray-400">{worker.worker_email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-center text-white font-medium">
                          {worker.orders_completed}
                        </td>
                        <td className="py-4 px-4 text-center text-blue-400">
                          {worker.orders_in_progress}
                        </td>
                        <td className="py-4 px-4 text-center text-white">
                          <div className="flex items-center justify-center gap-1">
                            <Clock className="w-4 h-4 text-gray-400" />
                            {worker.avg_completion_time_hours.toFixed(1)}h
                          </div>
                        </td>
                        <td className="py-4 px-4 text-center text-neon-500 font-medium">
                          +{worker.avg_score_improvement.toFixed(0)} pts
                        </td>
                        <td className="py-4 px-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <div className="w-20 bg-dark-700 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  worker.efficiency_score >= 80
                                    ? 'bg-green-400'
                                    : worker.efficiency_score >= 60
                                    ? 'bg-yellow-400'
                                    : 'bg-red-400'
                                }`}
                                style={{ width: `${worker.efficiency_score}%` }}
                              />
                            </div>
                            <span className="text-white font-bold w-12 text-right">
                              {worker.efficiency_score.toFixed(0)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* ========== 4. GEOGRAPHICAL HEATMAP ========== */}
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <Globe className="w-6 h-6 text-neon-500" />
              Geographical Heatmap
            </h2>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Summary Cards */}
              <div className="card lg:col-span-1">
                <div className="text-center mb-4">
                  <p className="text-gray-400 mb-2">Total Diagnósticos</p>
                  <p className="text-4xl font-bold text-neon-500">
                    {heatmap?.total_diagnoses || 0}
                  </p>
                </div>
                <div className="text-center pt-4 border-t border-dark-700">
                  <p className="text-gray-400 mb-2">País con Más Actividad</p>
                  <p className="text-2xl font-bold text-white">
                    {heatmap?.top_country || 'N/A'}
                  </p>
                </div>
              </div>

              {/* Locations Table */}
              <div className="card lg:col-span-2">
                <h3 className="text-lg font-bold text-white mb-4">Actividad por País</h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {heatmap?.locations.map((location) => (
                    <div
                      key={location.country}
                      className="flex items-center justify-between p-3 bg-dark-800/50 rounded-lg hover:bg-dark-800 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-3xl">{location.flag}</span>
                        <div>
                          <p className="text-white font-medium">{location.country_name}</p>
                          <div className="flex items-center gap-2 text-sm text-gray-400">
                            <MapPin className="w-3 h-3" />
                            <span>Lat: {location.lat.toFixed(2)}, Lng: {location.lng.toFixed(2)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-neon-500 font-bold text-lg">
                          {location.diagnosis_count} diagnósticos
                        </p>
                        <p className="text-sm text-gray-400">
                          {location.lead_count} leads · Conv: {location.conversion_rate}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Marketing Insights */}
            {heatmap && heatmap.locations.length > 0 && (
              <div className="card mt-6 border-neon-500">
                <div className="flex items-start gap-3">
                  <Zap className="w-6 h-6 text-neon-500 flex-shrink-0" />
                  <div>
                    <h3 className="text-lg font-bold text-white mb-2">Marketing Intelligence</h3>
                    <p className="text-gray-400 mb-3">
                      Basado en la distribución geográfica de diagnósticos, recomendamos:
                    </p>
                    <ul className="space-y-2">
                      {heatmap.locations[0] && (
                        <li className="text-neon-500">
                          ✓ Invertir 50% del presupuesto de marketing en {heatmap.locations[0].country_name} 
                          ({heatmap.locations[0].diagnosis_count} diagnósticos)
                        </li>
                      )}
                      {heatmap.locations[1] && (
                        <li className="text-blue-400">
                          ✓ Expandir presencia en {heatmap.locations[1].country_name} 
                          ({heatmap.locations[1].diagnosis_count} diagnósticos)
                        </li>
                      )}
                      {heatmap.locations.some(l => l.conversion_rate < 50) && (
                        <li className="text-yellow-400">
                          ⚠ Optimizar conversión en países con tasa baja (&lt;50%)
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </section>
        </main>
      </div>
    </AuthGuard>
  );
}
