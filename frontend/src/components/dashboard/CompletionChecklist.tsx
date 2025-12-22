'use client';

import { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

interface ChecklistItem {
  id: string;
  label: string;
  description: string;
}

interface CompletionChecklistProps {
  orderId: number;
  onChecklistComplete: (allComplete: boolean) => void;
}

const CHECKLIST_ITEMS: ChecklistItem[] = [
  {
    id: 'claimed_gmb',
    label: '🏢 Reclamado Google My Business',
    description: 'El negocio ha sido reclamado y verificado en GMB'
  },
  {
    id: 'photos_uploaded',
    label: '📸 Fotos subidas y geoetiquetadas',
    description: 'Al menos 10 fotos con coordenadas GPS'
  },
  {
    id: 'description_optimized',
    label: '📝 Descripción optimizada',
    description: 'Descripción de 150 palabras con keywords'
  },
  {
    id: 'categories_updated',
    label: '🏷️ Categorías actualizadas',
    description: 'Categoría principal + 3 secundarias'
  },
  {
    id: 'hours_configured',
    label: '🕐 Horarios configurados',
    description: 'Horario de atención completo'
  },
  {
    id: 'nap_verified',
    label: '📍 NAP verificado',
    description: 'Nombre, Dirección, Teléfono consistentes'
  },
  {
    id: 'attributes_set',
    label: '⚡ Atributos configurados',
    description: 'Servicios, métodos de pago, características'
  },
  {
    id: 'website_linked',
    label: '🔗 Website vinculado',
    description: 'Link al sitio web del cliente'
  }
];

export default function CompletionChecklist({ orderId, onChecklistComplete }: CompletionChecklistProps) {
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchChecklist();
  }, [orderId]);

  useEffect(() => {
    // Verificar si todos los items están completos
    const allComplete = CHECKLIST_ITEMS.every(item => checkedItems[item.id]);
    onChecklistComplete(allComplete);
  }, [checkedItems, onChecklistComplete]);

  const fetchChecklist = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/orders/${orderId}/checklist`
      );
      if (response.ok) {
        const data = await response.json();
        setCheckedItems(data.items || {});
      }
    } catch (error) {
      console.error('Error fetching checklist:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleItem = async (itemId: string) => {
    const newCheckedItems = {
      ...checkedItems,
      [itemId]: !checkedItems[itemId]
    };
    
    setCheckedItems(newCheckedItems);
    
    // Guardar automáticamente
    setSaving(true);
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/orders/${orderId}/checklist`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ items: newCheckedItems })
        }
      );
    } catch (error) {
      console.error('Error saving checklist:', error);
      // Revertir cambio si falla
      setCheckedItems(checkedItems);
    } finally {
      setSaving(false);
    }
  };

  const completionPercentage = Math.round(
    (Object.values(checkedItems).filter(Boolean).length / CHECKLIST_ITEMS.length) * 100
  );

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-neon-500 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-neon-500" />
            Checklist de Finalización
          </h2>
          {saving && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              Guardando...
            </span>
          )}
        </div>
        
        {/* Progress Bar */}
        <div className="relative">
          <div className="h-3 bg-dark-900 rounded-full overflow-hidden border border-gray-700">
            <div
              className={`h-full transition-all duration-500 ${
                completionPercentage === 100 
                  ? 'bg-neon-500' 
                  : 'bg-cyber-blue'
              }`}
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-mono font-bold text-white drop-shadow-lg">
              {completionPercentage}%
            </span>
          </div>
        </div>
        
        <p className="text-xs text-gray-400 mt-2">
          {completionPercentage === 100 ? (
            <span className="text-neon-500 font-bold">
              ✅ ¡Todos los items completados! Ya puedes finalizar la orden.
            </span>
          ) : (
            <>
              {Object.values(checkedItems).filter(Boolean).length} de {CHECKLIST_ITEMS.length} items completados
            </>
          )}
        </p>
      </div>

      {/* Checklist Items */}
      <div className="space-y-2">
        {CHECKLIST_ITEMS.map((item) => {
          const isChecked = checkedItems[item.id];
          return (
            <button
              key={item.id}
              onClick={() => toggleItem(item.id)}
              className={`w-full p-4 rounded-lg border transition-all text-left ${
                isChecked
                  ? 'bg-neon-500/10 border-neon-500/30 hover:bg-neon-500/20'
                  : 'bg-dark-900 border-gray-700 hover:border-gray-600'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {isChecked ? (
                    <CheckCircle2 className="w-5 h-5 text-neon-500" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-600" />
                  )}
                </div>
                <div className="flex-1">
                  <p className={`font-medium ${
                    isChecked ? 'text-white' : 'text-gray-300'
                  }`}>
                    {item.label}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {item.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer Message */}
      <div className={`mt-6 p-4 rounded-lg border ${
        completionPercentage === 100
          ? 'bg-neon-500/10 border-neon-500/30'
          : 'bg-warning-500/10 border-warning-500/30'
      }`}>
        <p className="text-sm text-center">
          {completionPercentage === 100 ? (
            <span className="text-neon-500 font-bold">
              🎉 El botón "Marcar como Completado" ya está habilitado
            </span>
          ) : (
            <span className="text-warning-500">
              ⚠️ Completa todos los items para habilitar el botón de finalización
            </span>
          )}
        </p>
      </div>
    </div>
  );
}
