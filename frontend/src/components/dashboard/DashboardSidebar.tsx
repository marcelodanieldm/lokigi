'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { 
  LayoutDashboard, 
  ClipboardList, 
  CheckCircle2, 
  Clock, 
  DollarSign,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { useState } from 'react';

interface DashboardStats {
  total_orders: number;
  pending_orders: number;
  in_progress_orders: number;
  completed_orders: number;
  total_revenue: number;
}

interface DashboardSidebarProps {
  stats?: DashboardStats;
}

export default function DashboardSidebar({ stats }: DashboardSidebarProps) {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const menuItems = [
    {
      label: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
      exact: true
    },
    {
      label: '🚀 Work Queue',
      href: '/dashboard/work',
      icon: ClipboardList,
      highlight: true
    },
    {
      label: 'Todas las Órdenes',
      href: '/dashboard/orders',
      icon: ClipboardList,
      count: stats?.total_orders
    },
    {
      label: 'Pendientes',
      href: '/dashboard/orders?status=pending',
      icon: Clock,
      count: stats?.pending_orders,
      color: 'text-yellow-600'
    },
    {
      label: 'En Proceso',
      href: '/dashboard/orders?status=in_progress',
      icon: Clock,
      count: stats?.in_progress_orders,
      color: 'text-blue-600'
    },
    {
      label: 'Completadas',
      href: '/dashboard/orders?status=completed',
      icon: CheckCircle2,
      count: stats?.completed_orders,
      color: 'text-green-600'
    }
  ];

  const isActive = (href: string, exact: boolean = false) => {
    if (exact) {
      return pathname === href;
    }
    return pathname?.startsWith(href);
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-lg"
      >
        {isMobileMenuOpen ? (
          <X className="w-6 h-6 text-gray-600" />
        ) : (
          <Menu className="w-6 h-6 text-gray-600" />
        )}
      </button>

      {/* Backdrop for mobile */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:sticky top-0 left-0 h-screen w-72 bg-gradient-to-b from-gray-900 to-gray-800 
          text-white flex flex-col shadow-2xl z-40 transition-transform duration-300
          ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
              <span className="text-2xl font-black">L</span>
            </div>
            <div>
              <h1 className="text-xl font-black">Lokigi</h1>
              <p className="text-xs text-gray-400">Panel Operativo</p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="p-6 space-y-3 border-b border-gray-700">
            {/* Revenue Card */}
            <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/10 rounded-xl p-4 border border-green-500/30">
              <div className="flex items-center gap-3 mb-2">
                <DollarSign className="w-5 h-5 text-green-400" />
                <span className="text-xs font-semibold text-green-300">INGRESOS TOTALES</span>
              </div>
              <div className="text-3xl font-black text-white">
                ${stats.total_revenue.toLocaleString()}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                De {stats.completed_orders} órdenes completadas
              </div>
            </div>

            {/* Active Orders */}
            <div className="bg-gradient-to-br from-blue-500/20 to-purple-500/10 rounded-xl p-4 border border-blue-500/30">
              <div className="text-xs font-semibold text-blue-300 mb-2">ÓRDENES ACTIVAS</div>
              <div className="text-3xl font-black text-white">
                {(stats.pending_orders || 0) + (stats.in_progress_orders || 0)}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {stats.pending_orders} pendientes · {stats.in_progress_orders} en proceso
              </div>
            </div>
          </div>
        )}

        {/* Navigation Menu */}
        <nav className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href, item.exact);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`
                    flex items-center justify-between gap-3 px-4 py-3 rounded-xl
                    transition-all duration-200 group
                    ${active 
                      ? 'bg-white/10 text-white shadow-lg' 
                      : 'text-gray-300 hover:bg-white/5 hover:text-white'
                    }
                  `}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${item.color || ''}`} />
                    <span className="font-medium">{item.label}</span>
                  </div>

                  {typeof item.count === 'number' && item.count > 0 && (
                    <span className={`
                      px-2 py-1 rounded-full text-xs font-bold
                      ${active 
                        ? 'bg-white text-gray-900' 
                        : 'bg-gray-700 text-gray-300 group-hover:bg-gray-600'
                      }
                    `}>
                      {item.count}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-red-500/10 hover:text-red-400 transition-colors">
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Cerrar Sesión</span>
          </button>
        </div>
      </aside>
    </>
  );
}
