'use client';

import { useState, useEffect } from 'react';
import AuthGuard from '@/components/AuthGuard';
import DashboardSidebar from '@/components/dashboard/DashboardSidebar';
import {
  TrendingUp,
  Users,
  Globe,
  DollarSign,
  MapPin,
  BarChart3,
  Loader2,
} from 'lucide-react';

interface LeadsByCountry {
  country: string;
  country_name: string;
  count: number;
  revenue: number;
  percentage: number;
  flag: string;
}

interface AnalyticsData {
  total_leads: number;
  total_orders: number;
  total_revenue: number;
  conversion_rate: number;
  leads_by_country: LeadsByCountry[];
}

const COUNTRY_FLAGS: Record<string, string> = {
  BR: '🇧🇷',
  AR: '🇦🇷',
  MX: '🇲🇽',
  CO: '🇨🇴',
  CL: '🇨🇱',
  US: '🇺🇸',
  ES: '🇪🇸',
  OTHER: '🌍',
};

const COUNTRY_NAMES: Record<string, string> = {
  BR: 'Brasil',
  AR: 'Argentina',
  MX: 'México',
  CO: 'Colombia',
  CL: 'Chile',
  US: 'Estados Unidos',
  ES: 'España',
  OTHER: 'Otros',
};

export default function AdminAnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | 'all'>('30d');

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/analytics?time_range=${timeRange}`
      );
      const data = await response.json();
      
      // Enrich data with flags and names
      data.leads_by_country = data.leads_by_country.map((item: any) => ({
        ...item,
        flag: COUNTRY_FLAGS[item.country] || COUNTRY_FLAGS.OTHER,
        country_name: COUNTRY_NAMES[item.country] || item.country,
      }));
      
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

  const getMaxRevenue = () => {
    if (!analytics) return 0;
    return Math.max(...analytics.leads_by_country.map(c => c.revenue), 1);
  };

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
