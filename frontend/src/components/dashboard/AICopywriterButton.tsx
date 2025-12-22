'use client';

import { useState } from 'react';
import { Wand2, Copy, Loader2, X, CheckCircle } from 'lucide-react';

interface AICopywriterButtonProps {
  businessName: string;
  businessCategory?: string;
  orderId: number;
}

interface CopywriterResult {
  description: string;
  review_responses: string[];
}

export default function AICopywriterButton({ businessName, businessCategory, orderId }: AICopywriterButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CopywriterResult | null>(null);
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  const generateCopy = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dashboard/orders/${orderId}/generate-copy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_name: businessName,
          business_category: businessCategory || ''
        })
      });
      
      if (!response.ok) throw new Error('Error al generar contenido');
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Error al generar contenido con AI');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string, itemKey: string) => {
    navigator.clipboard.writeText(text);
    setCopiedItem(itemKey);
    setTimeout(() => setCopiedItem(null), 2000);
  };

  const openModal = () => {
    setIsOpen(true);
    if (!result) {
      generateCopy();
    }
  };

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={openModal}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        <Wand2 className="w-5 h-5" />
        🤖 AI Copywriter
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-dark-800 border border-neon-500/30 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-dark-800 border-b border-neon-500/30 p-6 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <Wand2 className="w-6 h-6 text-neon-500" />
                  AI Copywriter
                </h2>
                <p className="text-gray-400 text-sm mt-1">
                  Contenido generado con Gemini AI para {businessName}
                </p>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="w-10 h-10 bg-gray-800 hover:bg-gray-700 rounded-lg flex items-center justify-center transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6">
              {loading ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <Loader2 className="w-12 h-12 text-neon-500 animate-spin mb-4" />
                  <p className="text-gray-400">Generando contenido con AI...</p>
                  <p className="text-gray-500 text-sm mt-2">Esto puede tomar 10-15 segundos</p>
                </div>
              ) : result ? (
                <>
                  {/* Business Description */}
                  <div className="card">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="text-lg font-bold text-white">
                        📝 Descripción del Negocio (150 palabras)
                      </h3>
                      <button
                        onClick={() => handleCopy(result.description, 'description')}
                        className="btn-secondary flex items-center gap-2"
                      >
                        {copiedItem === 'description' ? (
                          <>
                            <CheckCircle className="w-4 h-4 text-neon-500" />
                            Copiado
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            Copiar
                          </>
                        )}
                      </button>
                    </div>
                    <p className="text-gray-300 leading-relaxed whitespace-pre-wrap bg-dark-900 p-4 rounded-lg border border-gray-700">
                      {result.description}
                    </p>
                  </div>

                  {/* Review Responses */}
                  <div className="card">
                    <h3 className="text-lg font-bold text-white mb-4">
                      💬 Respuestas a Reseñas Negativas (3 variantes)
                    </h3>
                    <div className="space-y-4">
                      {result.review_responses.map((response, index) => (
                        <div key={index} className="bg-dark-900 p-4 rounded-lg border border-gray-700">
                          <div className="flex items-start justify-between mb-2">
                            <span className="text-sm font-mono text-neon-500 font-bold">
                              Respuesta #{index + 1}
                            </span>
                            <button
                              onClick={() => handleCopy(response, `response-${index}`)}
                              className="btn-secondary flex items-center gap-2 text-xs"
                            >
                              {copiedItem === `response-${index}` ? (
                                <>
                                  <CheckCircle className="w-3 h-3 text-neon-500" />
                                  Copiado
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3 h-3" />
                                  Copiar
                                </>
                              )}
                            </button>
                          </div>
                          <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                            {response}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Regenerate Button */}
                  <button
                    onClick={generateCopy}
                    className="btn-secondary w-full flex items-center justify-center gap-2"
                  >
                    <Wand2 className="w-4 h-4" />
                    Regenerar contenido
                  </button>
                </>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-400">Error al cargar el contenido</p>
                  <button onClick={generateCopy} className="btn-primary mt-4">
                    Reintentar
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
