'use client';

import { AlertTriangle, XCircle, AlertCircle, ShieldAlert } from 'lucide-react';

interface CriticalAlert {
  id: string;
  severity: 'critical' | 'high' | 'medium';
  title: string;
  description: string;
  impact: string;
}

interface CriticalAlertsGridProps {
  alerts: CriticalAlert[];
}

export default function CriticalAlertsGrid({ alerts }: CriticalAlertsGridProps) {
  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-gradient-to-br from-red-500/10 to-red-600/5',
          border: 'border-red-500/20',
          icon: 'text-red-500',
          badge: 'bg-red-500',
          IconComponent: XCircle
        };
      case 'high':
        return {
          bg: 'bg-gradient-to-br from-orange-500/10 to-orange-600/5',
          border: 'border-orange-500/20',
          icon: 'text-orange-500',
          badge: 'bg-orange-500',
          IconComponent: AlertTriangle
        };
      default:
        return {
          bg: 'bg-gradient-to-br from-yellow-500/10 to-yellow-600/5',
          border: 'border-yellow-500/20',
          icon: 'text-yellow-500',
          badge: 'bg-yellow-500',
          IconComponent: AlertCircle
        };
    }
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-red-500/10 rounded-xl">
            <ShieldAlert className="w-8 h-8 text-red-500" />
          </div>
          <div>
            <h2 className="text-3xl font-black text-gray-900">Fallos Críticos Detectados</h2>
            <p className="text-gray-600 mt-1">Problemas que están costándote dinero <span className="font-bold">AHORA MISMO</span></p>
          </div>
        </div>
      </div>

      {/* Alerts Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {alerts.map((alert, index) => {
          const styles = getSeverityStyles(alert.severity);
          const Icon = styles.IconComponent;

          return (
            <div
              key={alert.id}
              className={`relative group ${styles.bg} ${styles.border} border-2 rounded-2xl p-6 hover:scale-105 transition-all duration-300 cursor-pointer hover:shadow-2xl`}
            >
              {/* Badge Number */}
              <div className="absolute -top-3 -left-3 w-12 h-12 bg-gradient-to-br from-gray-900 to-gray-800 rounded-full flex items-center justify-center border-4 border-white shadow-lg">
                <span className="text-white font-black text-lg">{index + 1}</span>
              </div>

              {/* Severity Badge */}
              <div className="absolute -top-3 -right-3">
                <div className={`${styles.badge} text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg`}>
                  {alert.severity.toUpperCase()}
                </div>
              </div>

              {/* Icon */}
              <div className="mt-4 mb-6">
                <div className={`inline-flex p-4 rounded-2xl ${styles.bg} ${styles.border} border`}>
                  <Icon className={`w-10 h-10 ${styles.icon}`} />
                </div>
              </div>

              {/* Content */}
              <h3 className="text-xl font-bold text-gray-900 mb-3 group-hover:text-red-600 transition-colors">
                {alert.title}
              </h3>
              
              <p className="text-gray-700 mb-4 leading-relaxed">
                {alert.description}
              </p>

              {/* Impact Badge */}
              <div className="pt-4 border-t border-gray-200">
                <div className="flex items-start gap-2">
                  <span className="text-2xl">💸</span>
                  <div>
                    <div className="text-xs font-semibold text-gray-500 uppercase mb-1">Impacto Estimado</div>
                    <div className="text-sm font-bold text-red-600">{alert.impact}</div>
                  </div>
                </div>
              </div>

              {/* Hover Effect */}
              <div className="absolute inset-0 rounded-2xl ring-2 ring-red-500/0 group-hover:ring-red-500/50 transition-all duration-300" />
            </div>
          );
        })}
      </div>

      {/* Total Impact Summary */}
      <div className="mt-8 bg-gradient-to-r from-red-600 to-orange-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between flex-wrap gap-6">
          <div>
            <div className="text-red-100 text-sm font-semibold mb-2">💰 PÉRDIDA TOTAL ESTIMADA</div>
            <div className="text-4xl md:text-5xl font-black mb-2">
              ${alerts.reduce((sum, alert) => {
                const match = alert.impact.match(/\$([0-9,]+)/);
                return sum + (match ? parseInt(match[1].replace(',', '')) : 0);
              }, 0).toLocaleString()}<span className="text-2xl">/mes</span>
            </div>
            <div className="text-red-100">
              Eso son <span className="font-bold">
                ${(alerts.reduce((sum, alert) => {
                  const match = alert.impact.match(/\$([0-9,]+)/);
                  return sum + (match ? parseInt(match[1].replace(',', '')) : 0);
                }, 0) * 12).toLocaleString()}
              </span> al año que van directo a tu competencia
            </div>
          </div>
          <div className="text-6xl">📉</div>
        </div>
      </div>
    </div>
  );
}
