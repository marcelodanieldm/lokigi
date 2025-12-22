'use client';

import { TrendingDown, DollarSign, Users, AlertTriangle } from 'lucide-react';

interface RevenueL ossDisplayProps {
  lucro_cesante: {
    mensual_usd: number;
    anual_usd: number;
    clientes_perdidos_mes: number;
    moneda: string;
    descripcion: string;
  };
  language: string;
}

export default function RevenueLossDisplay({ lucro_cesante, language }: RevenueLossDisplayProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className="bg-gradient-to-br from-danger-600/20 to-danger-500/10 border-2 border-danger-500 rounded-xl p-8">
      {/* Header con icono de alerta */}
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-3 bg-danger-500/20 rounded-lg">
          <AlertTriangle className="w-8 h-8 text-danger-500" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white">
            {language === 'PT' ? 'Lucro Cessante' : language === 'ES' ? 'Lucro Cesante' : 'Revenue Loss'}
          </h2>
          <p className="text-gray-400 text-sm">
            {language === 'PT' 
              ? 'Dinheiro que você está perdendo' 
              : language === 'ES' 
              ? 'Dinero que estás perdiendo' 
              : 'Money you\'re losing'}
          </p>
        </div>
      </div>

      {/* Monto Principal (MUY DESTACADO) */}
      <div className="mb-8">
        <div className="flex items-baseline space-x-2 mb-2">
          <TrendingDown className="w-6 h-6 text-danger-500 animate-pulse" />
          <span className="text-gray-400 text-sm uppercase tracking-wide">
            {language === 'PT' ? 'Por Mês' : language === 'ES' ? 'Por Mes' : 'Per Month'}
          </span>
        </div>
        <div className="text-7xl font-black text-danger-500 tracking-tight">
          {formatCurrency(lucro_cesante.mensual_usd)}
        </div>
        <div className="text-gray-400 text-sm mt-2">
          {formatCurrency(lucro_cesante.anual_usd)} {language === 'PT' ? 'por ano' : language === 'ES' ? 'por año' : 'per year'}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Clientes Perdidos */}
        <div className="bg-dark-900/50 rounded-lg p-4 border border-dark-700">
          <div className="flex items-center space-x-2 mb-2">
            <Users className="w-5 h-5 text-danger-500" />
            <span className="text-xs text-gray-400 uppercase">
              {language === 'PT' ? 'Clientes Perdidos' : language === 'ES' ? 'Clientes Perdidos' : 'Lost Customers'}
            </span>
          </div>
          <div className="text-3xl font-bold text-white">
            {lucro_cesante.clientes_perdidos_mes.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {language === 'PT' ? 'por mês' : language === 'ES' ? 'por mes' : 'per month'}
          </div>
        </div>

        {/* Posición Estimada */}
        <div className="bg-dark-900/50 rounded-lg p-4 border border-dark-700">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="w-5 h-5 text-warning-500" />
            <span className="text-xs text-gray-400 uppercase">
              {language === 'PT' ? 'Valor Ticket' : language === 'ES' ? 'Ticket Promedio' : 'Avg. Ticket'}
            </span>
          </div>
          <div className="text-3xl font-bold text-white">
            {formatCurrency(lucro_cesante.mensual_usd / lucro_cesante.clientes_perdidos_mes)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {language === 'PT' ? 'por cliente' : language === 'ES' ? 'por cliente' : 'per customer'}
          </div>
        </div>
      </div>

      {/* Explicación */}
      <div className="mt-6 p-4 bg-dark-900/80 rounded-lg border border-danger-500/30">
        <p className="text-sm text-gray-300 leading-relaxed">
          <strong className="text-danger-500">
            {language === 'PT' ? 'Por que você está perdendo dinheiro?' : language === 'ES' ? '¿Por qué estás perdiendo dinero?' : 'Why are you losing money?'}
          </strong>
          {' '}
          {lucro_cesante.descripcion}
        </p>
      </div>

      {/* Call-to-Action Hint */}
      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500">
          {language === 'PT' 
            ? '💡 Scroll para baixo para ver como corrigir esses problemas' 
            : language === 'ES' 
            ? '💡 Desplázate hacia abajo para ver cómo solucionar estos problemas' 
            : '💡 Scroll down to see how to fix these issues'}
        </p>
      </div>
    </div>
  );
}
